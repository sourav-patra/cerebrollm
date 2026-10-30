"""Guarded pull and unload for the local Ollama host (issue #9). Standard library only.

    python model_guard.py pull NAME     pull one model listed in engine/models.toml, record its digest
    python model_guard.py unload NAME   keep_alive 0, require a completed unload reply, then an empty /api/ps
    python model_guard.py check-empty   require an empty /api/ps

Exit codes: 0 done, 2 refused by a guard, 1 operational failure (Ollama down, pull error, digest mismatch).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import tomllib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS_TOML = HERE.parents[1] / 'engine' / 'models.toml'
PULLS = HERE / 'pulls.jsonl'
MACHINE = HERE / 'machine-wsl.json'
BASE = 'http://127.0.0.1:11434'  # fixed on purpose: the guard never talks to another host
REGISTRY = 'https://registry.ollama.ai/v2/library'
MANIFEST_ACCEPT = 'application/vnd.docker.distribution.manifest.v2+json'
GIB = 1024 ** 3
LICENCES = {'Apache-2.0', 'MIT'}
CAPS = {'embedding': 8192, 'chat': 16384}


SHOW_FIELDS = {'details', 'modelfile', 'model_info', 'capabilities', 'template', 'license'}  # a real /api/show reply has these


class Refused(Exception):
    """A guard rule stopped the request before or during the action."""


class RemoteModel(Refused):
    """The model answers from a remote host, so using it would send data off the machine."""


def _http(method, path, payload=None, timeout=600):
    """Yield each JSON object of the reply: one object, or the progress stream of /api/pull."""
    req = urllib.request.Request(
        BASE + path, method=method, headers={'Content-Type': 'application/json'},
        data=None if payload is None else json.dumps(payload).encode())
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=timeout) as r:
        for line in r:
            if line.strip():
                try:
                    reply = json.loads(line)
                except ValueError as e:
                    raise RuntimeError(f'{method} {path}: malformed JSON from Ollama ({e})')
                if not isinstance(reply, dict):
                    raise RuntimeError(f'{method} {path}: Ollama sent {type(reply).__name__}, not a JSON object')
                yield reply


def _one(method, path, payload=None):
    reply = next(_http(method, path, payload), None)
    if reply is None:
        raise RuntimeError(f'{method} {path}: empty reply from Ollama')
    return reply


def _free(path):
    return shutil.disk_usage(path).free


def _disk_path(host):
    return host['disk_path_windows'] if os.name == 'nt' else host['disk_path']


def load():
    cfg = tomllib.loads(MODELS_TOML.read_text(encoding='utf-8'))
    for name, m in cfg['models'].items():
        cap = CAPS.get(m['role'])
        if cap is None or m['num_ctx'] > cap:
            raise Refused(f'{name}: role {m["role"]!r} with num_ctx {m["num_ctx"]} breaks the caps {CAPS}')
    return cfg


def vet(name):
    """Return the model's entry, or raise Refused. Cloud names are refused before the list is read."""
    if name.strip().lower().endswith(('-cloud', ':cloud')):
        raise Refused(f'{name}: cloud models send data off the machine')
    m = load()['models'].get(name)
    if m is None:
        raise Refused(f'{name}: not listed in engine/models.toml')
    if m.get('allowed') is not True or m.get('licence') not in LICENCES:
        raise Refused(f'{name}: not allowed (licence {m.get("licence")!r}, allowed={m.get("allowed")}, '
                      f'reason: {m.get("reason", "none given")})')
    return m


def _tag(name):
    return name if ':' in name else name + ':latest'


def _installed(name):
    """The /api/tags entry of an installed model, or None."""
    return next((t for t in _one('GET', '/api/tags')['models'] if t['name'] == _tag(name)), None)


def _remote(reply):
    return reply.get('remote_host') or reply.get('remote_model')


def _show(name):
    """The /api/show reply; anything but a genuine reply means the model cannot be shown to be local."""
    try:
        reply = _one('POST', '/api/show', {'model': name})
    except (RuntimeError, ValueError) as e:
        raise Refused(f'{name}: no usable /api/show reply ({e}); cannot prove the model is local')
    if not isinstance(reply, dict) or 'error' in reply or not (_remote(reply) or SHOW_FIELDS & reply.keys()):
        raise Refused(f'{name}: /api/show gave an error or an unrecognised reply ({str(reply)[:200]}); '
                      f'cannot prove the model is local')
    return reply


def _check_remote(name, entry):
    """Refuse a model that runs remotely.

    `ollama cp kimi-k3:cloud phi4` makes a cloud model answer to an allowed name, so the name proves nothing.
    Both /api/tags and /api/show carry remote_host and remote_model for such entries.
    """
    src = entry if _remote(entry) else _show(name)
    if _remote(src):
        raise RemoteModel(f'{name}: runs remotely ({src.get("remote_model")} on {src.get("remote_host")}); '
                          f'data would leave the machine')


def _check_local(name, m, entry):
    """Refuse a model that runs remotely or is not the pinned build."""
    if m.get('digest') and entry['digest'] != m['digest']:
        raise Refused(f'{name}: installed digest {entry["digest"]} differs from the pinned {m["digest"]}')
    _check_remote(name, entry)


def _remove(name):
    """Delete a model and prove it is gone from /api/tags. Raises RuntimeError on any doubt."""
    try:
        replies = list(_http('DELETE', '/api/delete', {'model': name}))
        still_listed = _installed(name) is not None
    except (OSError, KeyError, TypeError) as e:
        raise RuntimeError(f'delete or the check after it failed: {e!r}')
    for r in replies:
        if 'error' in r:
            raise RuntimeError(f'delete answered with an error: {r["error"]}')
    if still_listed:
        raise RuntimeError('/api/tags still lists the model after the delete')


def _discard(name, digest, message, exc=RuntimeError, **extra):
    """Remove a model that came out of a pull but must not be kept, log the outcome, and raise."""
    try:
        _remove(name)
        removed, tail = True, 'the model was removed (confirmed absent from /api/tags)'
    except RuntimeError as e:
        removed, tail, exc = False, f'CLEANUP FAILED, the model may still be installed: {e}', RuntimeError
    _log(name, digest, 'pulled', ok=False, removed=removed, reason=message, **extra)
    raise exc(f'{message}; {tail}')


def _manifest(name):
    """Current registry manifest: (config + layer bytes, sha256 of the manifest body). Refused if unreadable."""
    repo, _, tag = _tag(name).partition(':')
    req = urllib.request.Request(f'{REGISTRY}/{repo}/manifests/{tag}', headers={'Accept': MANIFEST_ACCEPT})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
        d = json.loads(body)
        sizes = [d['config']['size']] + [layer['size'] for layer in d['layers']]
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise Refused(f'{name}: cannot read the registry manifest ({e!r}); size unknown, disk floor cannot be checked')
    # exact ints only: NaN slips past every comparison, True counts as 1, and a negative size cancels a positive one
    if not all(type(s) is int and s >= 0 for s in sizes) or sum(sizes) <= 0:
        raise Refused(f'{name}: registry manifest has unusable sizes {sizes}')
    return sum(sizes), hashlib.sha256(body).hexdigest()  # Ollama's /api/tags digest is this same hash


def _check_disk(name, size, host):
    path = _disk_path(host)
    floor = host['floor_gb'] * GIB
    try:
        free = _free(path)
    except OSError as e:
        raise Refused(f'{name}: cannot read free space on {path}: {e}')
    if free < floor + size:
        raise Refused(f'{name}: {free / GIB:.1f} GiB free on {path}, need {(floor + size) / GIB:.1f} GiB '
                      f'(registry size {size / GIB:.1f} GiB + floor {host["floor_gb"]} GiB)')
    return path, floor


def _set_digest(name, digest):
    text = MODELS_TOML.read_bytes().decode('utf-8')
    i = text.index(f'[models."{name}"]')
    j = text.find('\n[', i + 1)
    j = len(text) if j < 0 else j
    block, n = re.subn(r'^digest = ".*?"', f'digest = "{digest}"', text[i:j], count=1, flags=re.M)
    if n != 1:
        raise RuntimeError(f'{name}: no digest line in {MODELS_TOML}')
    MODELS_TOML.write_bytes((text[:i] + block + text[j:]).encode('utf-8'))


def _log(name, digest, how, ok=True, **extra):
    with PULLS.open('a', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps({'time': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'model': name,
                            'digest': digest, 'how': how, 'ok': ok, **extra}) + '\n')


def _record(name, m, digest, how, **extra):
    ok = not m.get('digest') or m['digest'] == digest
    _log(name, digest, how, ok, pinned=m.get('digest', ''), **extra)
    if not ok:
        raise RuntimeError(f'{name}: digest {digest} differs from the pinned {m["digest"]}; models.toml left unchanged')
    if not m.get('digest'):
        _set_digest(name, digest)
    if how == 'pulled' and MACHINE.exists():
        d = json.loads(MACHINE.read_text(encoding='utf-8'))
        d.setdefault('pulled_digests', {})[name] = digest
        MACHINE.write_text(json.dumps(d, indent=2) + '\n', encoding='utf-8', newline='\n')
    return digest


def pull(name):
    m = vet(name)
    entry = _installed(name)
    if entry:  # never re-pull an installed model: a changed upstream tag would replace the live digest
        _check_local(name, m, entry)
        return _record(name, m, entry['digest'], 'already-installed')
    size, expected = _manifest(name)
    path, floor = _check_disk(name, size, load()['host'])
    last = {}
    # shortcut: the Ollama API cannot bind /api/pull to the manifest checked above, so the registry may serve a
    # newer build in between; the digest comparison after the pull catches it. Upgrade if /api/pull takes a digest.
    stream = _http('POST', '/api/pull', {'model': name, 'stream': True})
    try:
        for last in stream:
            if 'error' in last:
                raise RuntimeError(f'{name}: {last["error"]}')
            if _free(path) < floor:  # second line of defence: the registry size can still be wrong
                raise Refused(f'{name}: free space on {path} fell below the floor during the pull; pull cancelled')
    finally:
        stream.close()  # closing the connection cancels a running pull
    if last.get('status') != 'success':
        raise RuntimeError(f'{name}: pull ended without success (last event {last})')
    entry = _installed(name)
    if not entry:
        raise RuntimeError(f'{name}: pulled but /api/tags does not list it')
    if entry['digest'] != expected:
        _discard(name, entry['digest'], f'{name}: installed digest {entry["digest"]} is not the manifest checked '
                                        f'before the pull ({expected})', manifest=expected)
    try:  # a cloud alias can carry the digest of a real build, so the digest above does not prove the model is local
        _check_remote(name, entry)
    except RemoteModel as e:
        _discard(name, entry['digest'], str(e), exc=RemoteModel, manifest=expected)
    return _record(name, m, entry['digest'], 'pulled', manifest=expected, manifest_bytes=size)


def check_empty(wait=10):
    """Ollama drops a model a moment after keep_alive 0, so poll for up to `wait` seconds."""
    for i in range(wait):
        loaded = [x['name'] for x in _one('GET', '/api/ps')['models']]
        if not loaded:
            return
        time.sleep(1)
    raise RuntimeError(f'/api/ps still lists {loaded} after {wait} s')


def unload(name):
    m = vet(name)
    entry = _installed(name)
    if entry is None:
        raise RuntimeError(f'{name}: not installed, nothing to unload')
    _check_local(name, m, entry)
    replies = list(_http('POST', '/api/generate', {'model': name, 'keep_alive': 0}))
    for r in replies:
        if 'error' in r:
            raise RuntimeError(f'{name}: unload failed: {r["error"]}')
    if not any(r.get('done') is True and r.get('done_reason') == 'unload' for r in replies):
        raise RuntimeError(f'{name}: no completed unload reply (got {replies})')
    check_empty()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('action', choices=['pull', 'unload', 'check-empty'])
    p.add_argument('name', nargs='?')
    a = p.parse_args(argv)
    if a.action != 'check-empty' and not a.name:
        p.error(f'{a.action} needs a model NAME')
    try:
        if a.action == 'pull':
            print(f'{a.name} digest {pull(a.name)}')
        elif a.action == 'unload':
            unload(a.name)
            print(f'{a.name} unloaded; /api/ps is empty')
        else:
            check_empty()
            print('/api/ps is empty')
    except Refused as e:
        print(f'REFUSED: {e}', file=sys.stderr)
        return 2
    except (RuntimeError, OSError) as e:
        print(f'FAILED: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
