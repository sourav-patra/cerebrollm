"""Machine settings for the study scripts, read from study.toml next to this file.

Every string value expands ~ and $VARS; an unset variable or a missing key stops with a message that
names the key and the file. `engine_config_text` carries the data and corpus folders into the engine
configurations the study builds.
"""
import os
from pathlib import Path
import re
import tomllib

HERE = Path(__file__).resolve().parent
DEFAULT = HERE / 'study.toml'


def _expand(node, source, where=''):
    for key, value in node.items():
        here = '%s.%s' % (where, key) if where else key
        if isinstance(value, dict):
            _expand(value, source, here)
        elif isinstance(value, str):
            expanded = os.path.expanduser(os.path.expandvars(value))
            if '$' in expanded:
                raise SystemExit('%s: %s = %r uses an unset environment variable; set it or edit the file'
                                 % (source.name, here, value))
            node[key] = expanded
    return node


def load(path=DEFAULT):
    path = Path(path)
    return _expand(tomllib.loads(path.read_text()), path)


def get(data, section, key, source=DEFAULT):
    try:
        return data[section][key]
    except KeyError:
        raise SystemExit('%s: missing [%s] %s (file: %s)' % (Path(source).name, section, key, source))


_data = load()
ENGINE_DIR = (HERE / get(_data, 'engine', 'path')).resolve()   # relative paths count from this folder
DATA_DIR = Path(get(_data, 'data', 'path'))
VENV_PYTHON = str(Path(get(_data, 'venv', 'path')) / 'bin' / 'python')
CORPUS = Path(get(_data, 'corpus', 'path'))
OLLAMA = get(_data, 'ollama', 'path')
OLLAMA_URL = get(_data, 'ollama', 'url')
DOCKER = get(_data, 'docker', 'path')
PG_BIN = get(_data, 'postgres', 'bin')


def hostpath(path):
    """Path as the Docker daemon sees it: Windows Docker cannot resolve /mnt/c/... from Ubuntu."""
    if DOCKER.endswith('.exe') and os.name == 'posix':
        import subprocess
        return subprocess.run(['wslpath', '-w', str(path)], capture_output=True, text=True, check=True).stdout.strip()
    return str(path)

# keys of cerebrollm.toml that study.toml controls: (pattern for the line, new value)
_POINTS = [(r'^(state_dir = ")([^"]*)(")', lambda data, corpus: str(data)),
           (r'^(socket_dir = ")([^"]*)(")', lambda data, corpus: str(Path(data) / 'pg16' / 'sock')),
           (r'^(path = ")([^"]*)(")', lambda data, corpus: str(corpus))]


def engine_config_text(original, data_dir=DATA_DIR, corpus=CORPUS):
    """cerebrollm.toml text with the state directory, socket directory and corpus root taken from
    study.toml. A line that already resolves to the same path is left as written."""
    for pattern, new in _POINTS:
        def swap(m, new=new):
            value = new(data_dir, corpus)
            old = os.path.expanduser(os.path.expandvars(m.group(2)))
            return m.group(0) if old == value else m.group(1) + value + m.group(3)
        original = re.sub(pattern, swap, original, count=1, flags=re.M)
    return original
