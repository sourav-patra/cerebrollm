"""Tests for model_guard.py. No network, no real disk reads, no real models.

Run from research/model-study:  python -B -m unittest -v test_model_guard   (pytest also collects them)

Byte thresholds are written out as literal numbers on purpose, so a wrong constant in model_guard.py cannot
cancel itself out in a test:  8 GiB = 8589934592,  1 GiB = 1073741824.
"""
import hashlib
import io
import json
import tempfile
import types
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import model_guard as mg

REAL_HTTP = mg._http  # setUp replaces mg._http with a fake; one test needs the real one
GOOD_SHOW = {'details': {}, 'modelfile': '# Modelfile'}  # what a genuine local /api/show reply looks like, abridged

FIXTURE = '''
[host]
disk_path = "/mnt/c"
disk_path_windows = "C:\\\\"
floor_gb = 8

[models."small"]
role = "chat"
licence = "MIT"
allowed = true
num_ctx = 16384
digest = ""

[models."other"]
role = "chat"
licence = "Apache-2.0"
allowed = true
num_ctx = 16384
digest = ""

[models."phi4"]
role = "chat"
licence = "MIT"
allowed = true
num_ctx = 16384
digest = ""

[models."gpl-model"]
role = "chat"
licence = "GPL-3.0"
allowed = false
reason = "GPL-3.0 is not Apache-2.0 or MIT"
num_ctx = 16384
digest = ""

[models."disabled"]
role = "chat"
licence = "MIT"
allowed = false
reason = "switched off by the owner"
num_ctx = 16384
digest = ""

[models."sneaky"]
role = "chat"
licence = "Llama-3"
allowed = true
num_ctx = 16384
digest = ""

[models."evil:cloud"]
role = "chat"
licence = "Apache-2.0"
allowed = true
num_ctx = 16384
digest = ""

[models."evil-cloud"]
role = "chat"
licence = "Apache-2.0"
allowed = true
num_ctx = 16384
digest = ""
'''

DIGEST_A = 'ab' * 32  # /api/tags digests are bare 64-digit hex
DIGEST_B = 'cd' * 32
DIGEST_C = 'ee' * 32
CLOUD_SHOW = {'remote_model': 'kimi-k3', 'remote_host': 'https://ollama.com'}


class FakeOllama:
    """Stands in for model_guard._http and records every call."""

    def __init__(self):
        self.tags = []
        self.ps = [[]]  # successive /api/ps contents; the last one repeats
        self.events = [{'status': 'pulling manifest'}, {'status': 'success'}]
        self.digest = DIGEST_A  # digest the model gets when pulled
        self.show = {}  # model name -> /api/show reply (an Exception instance is raised instead)
        self.pull_extra = {}  # extra /api/tags fields on the entry a pull creates, e.g. remote_host
        self.generate = [{'model': 'x', 'response': '', 'done': True, 'done_reason': 'unload'}]
        self.delete_error = None
        self.delete_reply = []  # JSON objects Ollama sends back for a delete (a real delete sends none)
        self.delete_noop = False  # True: the delete answers fine but the model stays installed
        self.calls = []

    def __call__(self, method, path, payload=None, timeout=600):
        self.calls.append((method, path, payload))
        if path == '/api/tags':
            yield {'models': self.tags}
        elif path == '/api/show':
            reply = self.show.get(payload['model'], GOOD_SHOW)
            if isinstance(reply, Exception):
                raise reply
            yield reply
        elif path == '/api/ps':
            cur = self.ps.pop(0) if len(self.ps) > 1 else self.ps[0]
            yield {'models': [{'name': n} for n in cur]}
        elif path == '/api/pull':
            yield from self.events
            self.tags.append({'name': mg._tag(payload['model']), 'digest': self.digest, **self.pull_extra})
        elif path == '/api/generate':
            yield from self.generate
        elif path == '/api/delete':
            if self.delete_error:
                raise self.delete_error
            if not self.delete_noop:
                self.tags[:] = [t for t in self.tags if t['name'] != mg._tag(payload['model'])]
            yield from self.delete_reply
        else:
            raise AssertionError(f'unexpected request {method} {path}')

    def paths(self):
        return [c[1] for c in self.calls]


class FakeDisk:
    """Stands in for model_guard._free: free bytes per volume, and it fails the test on a volume nobody expects."""

    def __init__(self):
        self.volumes = {'/mnt/c': 100_000_000_000, 'C:\\': 100_000_000_000, '/': 3_000_000_000}
        self.script = {}  # volume -> successive readings, consumed before `volumes`
        self.asked = []

    def __call__(self, path):
        self.asked.append(path)
        if path not in self.volumes:
            raise AssertionError(f'guard asked for an unexpected volume {path!r}')
        if self.script.get(path):
            return self.script[path].pop(0)
        if self.volumes[path] is None:
            raise FileNotFoundError(path)
        return self.volumes[path]


class GuardTest(unittest.TestCase):
    fake_manifest = True  # False: model_guard._manifest runs for real against a fake urlopen

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        self.toml, self.pulls, self.machine = d / 'models.toml', d / 'pulls.jsonl', d / 'machine.json'
        self.toml.write_text(FIXTURE, encoding='utf-8')
        self.machine.write_text(json.dumps({'ollama': '0.40.12'}), encoding='utf-8')
        self.fake = FakeOllama()
        self.disk = FakeDisk()
        self.os = types.SimpleNamespace(name='posix')
        self.manifest = (1073741824, DIGEST_A)  # (registry bytes, sha256 of the manifest body)
        patches = [mock.patch.object(mg, 'MODELS_TOML', self.toml), mock.patch.object(mg, 'PULLS', self.pulls),
                   mock.patch.object(mg, 'MACHINE', self.machine), mock.patch.object(mg, '_http', self.fake),
                   mock.patch.object(mg, '_free', self.disk), mock.patch.object(mg, 'os', self.os),
                   mock.patch.object(mg.time, 'sleep')]
        if self.fake_manifest:
            patches.append(mock.patch.object(mg, '_manifest', lambda name: self.manifest))
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def assertRefused(self, name, fn=None, text=None, requests=()):
        with self.assertRaises(mg.Refused) as cm:
            (fn or mg.pull)(name)
        for path in ('/api/pull', *requests):
            self.assertNotIn(path, self.fake.paths())
        self.assertFalse(self.pulls.exists(), 'a refusal must not write a pull record')
        if text:
            self.assertIn(text, str(cm.exception))

    def lines(self):
        return [json.loads(x) for x in self.pulls.read_text(encoding='utf-8').splitlines()]

    def pinned(self, name):
        return mg.load()['models'][name]['digest']


class PullRefusals(GuardTest):
    def test_refuses_unlisted_model(self):
        self.assertRefused('llama3:8b', text='not listed')
        self.assertEqual(self.fake.calls, [], 'an unlisted name must not reach Ollama')

    def test_refuses_dash_cloud_name(self):
        self.assertRefused('gpt-oss:120b-cloud', text='off the machine')
        self.assertEqual(self.fake.calls, [])

    def test_refuses_colon_cloud_name(self):
        self.assertRefused('kimi-k3:cloud', text='off the machine')
        self.assertEqual(self.fake.calls, [])

    def test_refuses_cloud_name_even_when_listed_and_allowed(self):
        self.assertRefused('evil:cloud', text='off the machine')
        self.assertRefused('evil-cloud', text='off the machine')
        self.assertRefused(' KIMI:CLOUD ', text='off the machine')

    def test_refuses_disallowed_licence(self):
        self.assertRefused('gpl-model', text='GPL-3.0')

    def test_refuses_model_switched_off_although_its_licence_is_fine(self):
        self.assertRefused('disabled', text='switched off by the owner')

    def test_refuses_allowed_entry_with_a_licence_outside_apache_or_mit(self):
        self.assertRefused('sneaky', text='Llama-3')

    def test_refuses_pull_that_would_cross_the_disk_floor(self):
        self.disk.volumes['/mnt/c'] = 9663676415  # 8 GiB floor + 1 GiB model, one byte short
        self.assertRefused('small', text='GiB free')

    def test_pull_exactly_at_the_floor_is_allowed(self):
        self.disk.volumes['/mnt/c'] = 9663676416  # 8589934592 + 1073741824
        self.assertEqual(mg.pull('small'), DIGEST_A)

    def test_refuses_when_the_registry_manifest_has_grown_past_the_floor(self):
        self.manifest = (20_000_000_000, DIGEST_A)  # the registry now serves a 20 GB build
        self.disk.volumes['/mnt/c'] = 28589934591  # 8589934592 + 20000000000, one byte short
        self.assertRefused('small', text='GiB free')
        self.disk.volumes['/mnt/c'] = 28589934592
        self.assertEqual(mg.pull('small'), DIGEST_A)

    def test_refuses_when_free_space_cannot_be_read(self):
        self.disk.volumes['/mnt/c'] = None
        self.assertRefused('small', text='cannot read free space')

    def test_cancels_and_refuses_when_the_floor_is_reached_during_the_pull(self):
        # readings: before the pull, after event 1, after event 2 (below 8589934592)
        self.disk.script['/mnt/c'] = [100_000_000_000, 100_000_000_000, 7_000_000_000]
        with self.assertRaises(mg.Refused):
            mg.pull('small')
        self.assertEqual(self.fake.tags, [], 'the pull stream must be closed before the model is registered')
        self.assertFalse(self.pulls.exists())
        self.assertIsNone(json.loads(self.machine.read_text()).get('pulled_digests'))
        self.assertEqual(self.pinned('small'), '')

    def test_refuses_config_with_num_ctx_above_the_role_cap(self):
        self.toml.write_text(FIXTURE.replace('num_ctx = 16384\ndigest = ""\n\n[models."other"]',
                                             'num_ctx = 32768\ndigest = ""\n\n[models."other"]'), encoding='utf-8')
        self.assertRefused('small', text='caps')

    def test_refuses_embedding_role_above_8192(self):
        self.toml.write_text(FIXTURE.replace('role = "chat"\nlicence = "MIT"', 'role = "embedding"\nlicence = "MIT"'),
                             encoding='utf-8')
        self.assertRefused('small', text='caps')


class Volumes(GuardTest):
    def test_ubuntu_checks_the_c_volume_and_no_other(self):
        self.manifest = (15_000_000_000, DIGEST_A)
        self.disk.volumes.update({'/mnt/c': 20_000_000_000, '/': 500_000_000_000, 'C:\\': 500_000_000_000})
        self.assertRefused('small', text='/mnt/c')  # need 23589934592 > 20000000000
        self.assertEqual(self.disk.asked, ['/mnt/c'])

    def test_other_volumes_with_little_space_do_not_block_a_pull_that_fits_on_c(self):
        self.disk.volumes.update({'/mnt/c': 100_000_000_000, '/': 1_000_000, 'C:\\': 1_000_000})
        self.assertEqual(mg.pull('small'), DIGEST_A)
        self.assertEqual(set(self.disk.asked), {'/mnt/c'})

    def test_windows_python_checks_the_c_drive_and_no_other(self):
        self.os.name = 'nt'
        self.manifest = (15_000_000_000, DIGEST_A)
        self.disk.volumes.update({'C:\\': 20_000_000_000, '/mnt/c': 500_000_000_000, '/': 500_000_000_000})
        self.assertRefused('small', text='C:\\')
        self.assertEqual(self.disk.asked, ['C:\\'])
        self.disk.asked.clear()
        self.manifest = (1073741824, DIGEST_A)
        self.disk.volumes.update({'C:\\': 100_000_000_000, '/mnt/c': 1_000_000, '/': 1_000_000})
        self.assertEqual(mg.pull('small'), DIGEST_A)
        self.assertEqual(set(self.disk.asked), {'C:\\'})


class PullOutcomes(GuardTest):
    def test_successful_pull_writes_the_digest(self):
        digest = mg.pull('small')
        self.assertEqual(digest, DIGEST_A)
        rec = self.lines()
        self.assertEqual([(r['model'], r['digest'], r['how'], r['ok'], r['manifest'], r['manifest_bytes']) for r in rec],
                         [('small', DIGEST_A, 'pulled', True, DIGEST_A, 1073741824)])
        models = mg.load()['models']
        self.assertEqual(models['small']['digest'], DIGEST_A)
        self.assertEqual(models['other']['digest'], '', 'only the pulled model changes')
        self.assertEqual(json.loads(self.machine.read_text())['pulled_digests'], {'small': DIGEST_A})
        self.assertIn(('POST', '/api/pull', {'model': 'small', 'stream': True}), self.fake.calls)

    def test_installed_model_is_not_pulled_again_but_its_digest_is_recorded(self):
        self.fake.tags.append({'name': 'small:latest', 'digest': DIGEST_B})
        self.assertEqual(mg.pull('small'), DIGEST_B)
        self.assertNotIn('/api/pull', self.fake.paths())
        self.assertEqual(self.lines()[0]['how'], 'already-installed')
        self.assertNotIn('pulled_digests', json.loads(self.machine.read_text()))

    def test_digest_that_differs_from_the_pinned_one_fails_and_keeps_the_pin(self):
        mg.pull('small')
        self.fake.tags.clear()  # model removed by hand; the registry now serves another build
        self.fake.digest = DIGEST_C
        self.manifest = (1073741824, DIGEST_C)  # the manifest agrees with the pull, only the pin differs
        with self.assertRaises(RuntimeError):
            mg.pull('small')
        self.assertFalse(self.lines()[-1]['ok'])
        self.assertEqual(self.pinned('small'), DIGEST_A)

    def test_digest_that_differs_from_the_checked_manifest_is_removed_and_fails(self):
        self.fake.digest = DIGEST_C  # what the registry served at pull time
        self.manifest = (1073741824, DIGEST_A)  # what the guard read before the pull
        with self.assertRaises(RuntimeError) as cm:
            mg.pull('small')
        self.assertIn('removed', str(cm.exception))
        self.assertIn(('DELETE', '/api/delete', {'model': 'small'}), self.fake.calls)
        self.assertEqual(self.fake.tags, [])
        last = self.lines()[-1]
        self.assertEqual((last['ok'], last['digest'], last['manifest']), (False, DIGEST_C, DIGEST_A))
        self.assertEqual(self.pinned('small'), '')
        self.assertIsNone(json.loads(self.machine.read_text()).get('pulled_digests'))

    def test_failed_removal_after_a_manifest_mismatch_is_reported(self):
        self.fake.digest = DIGEST_C
        self.fake.delete_error = urllib.error.URLError('connection reset')
        with self.assertRaises(RuntimeError) as cm:
            mg.pull('small')
        self.assertIn('CLEANUP FAILED', str(cm.exception))
        self.assertNotIn('was removed', str(cm.exception))
        last = self.lines()[-1]
        self.assertEqual((last['ok'], last['removed']), (False, False))
        self.assertEqual(self.pinned('small'), '')

    def test_cleanup_that_gets_an_error_reply_from_delete_is_a_failure_not_a_removal(self):
        self.fake.digest = DIGEST_C
        self.fake.delete_noop = True
        self.fake.delete_reply = [{'error': 'model "small" not found'}]
        with self.assertRaises(RuntimeError) as cm:
            mg.pull('small')
        self.assertIn('CLEANUP FAILED', str(cm.exception))
        self.assertIn('not found', str(cm.exception))
        self.assertNotIn('was removed', str(cm.exception))
        self.assertFalse(self.lines()[-1]['removed'])

    def test_cleanup_whose_delete_leaves_the_model_listed_is_a_failure(self):
        self.fake.digest = DIGEST_C
        self.fake.delete_noop = True  # Ollama answers the delete without error, yet /api/tags still lists the model
        with self.assertRaises(RuntimeError) as cm:
            mg.pull('small')
        self.assertIn('CLEANUP FAILED', str(cm.exception))
        self.assertIn('still lists', str(cm.exception))
        self.assertFalse(self.lines()[-1]['removed'])

    def test_cleanup_confirms_absence_in_tags_before_it_says_removed(self):
        self.fake.digest = DIGEST_C
        with self.assertRaises(RuntimeError) as cm:
            mg.pull('small')
        self.assertIn('was removed', str(cm.exception))
        paths = self.fake.paths()
        self.assertEqual(paths[-2:], ['/api/delete', '/api/tags'], 'the delete must be followed by a tags check')
        self.assertTrue(self.lines()[-1]['removed'])

    def test_a_failed_cleanup_exits_non_zero_from_the_cli(self):
        self.fake.digest = DIGEST_C
        self.fake.delete_noop = True
        with mock.patch('sys.stderr'), mock.patch('sys.stdout'):
            self.assertEqual(mg.main(['pull', 'small']), 1)

    def test_remote_metadata_after_a_pull_is_removed_and_refused(self):
        # the pulled build has the manifest's digest, so only the locality check can catch the alias
        self.fake.show['small'] = dict(GOOD_SHOW, **CLOUD_SHOW)
        with self.assertRaises(mg.Refused) as cm:
            mg.pull('small')
        self.assertIn('runs remotely', str(cm.exception))
        self.assertIn('was removed', str(cm.exception))
        self.assertIn(('DELETE', '/api/delete', {'model': 'small'}), self.fake.calls)
        self.assertEqual(self.fake.tags, [])
        last = self.lines()[-1]
        self.assertEqual((last['ok'], last['removed'], last['digest']), (False, True, DIGEST_A))
        self.assertEqual(self.pinned('small'), '', 'a remote model must never be pinned')
        self.assertIsNone(json.loads(self.machine.read_text()).get('pulled_digests'))

    def test_remote_fields_in_tags_after_a_pull_are_removed_and_refused(self):
        self.fake.pull_extra = dict(CLOUD_SHOW)
        with self.assertRaises(mg.Refused):
            mg.pull('small')
        self.assertIn(('DELETE', '/api/delete', {'model': 'small'}), self.fake.calls)
        self.assertNotIn('/api/show', self.fake.paths(), 'a remote tags entry settles it without /api/show')
        self.assertEqual(self.fake.tags, [])
        self.assertEqual(self.pinned('small'), '')

    def test_remote_model_whose_cleanup_fails_is_reported_as_a_failure(self):
        self.fake.show['small'] = dict(GOOD_SHOW, **CLOUD_SHOW)
        self.fake.delete_noop = True
        with self.assertRaises(RuntimeError) as cm:
            mg.pull('small')
        self.assertIn('CLEANUP FAILED', str(cm.exception))
        self.assertEqual(self.pinned('small'), '')
        self.assertFalse(self.lines()[-1]['removed'])

    def test_unprovable_locality_after_a_pull_is_refused_and_not_recorded(self):
        self.fake.show['small'] = {'error': 'server busy'}
        with self.assertRaises(mg.Refused):
            mg.pull('small')
        self.assertFalse(self.pulls.exists())
        self.assertEqual(self.pinned('small'), '')
        self.assertIsNone(json.loads(self.machine.read_text()).get('pulled_digests'))

    def test_exit_codes_for_a_remote_model_after_a_pull(self):
        self.fake.show['small'] = dict(GOOD_SHOW, **CLOUD_SHOW)
        with mock.patch('sys.stderr'), mock.patch('sys.stdout'):
            self.assertEqual(mg.main(['pull', 'small']), 2)

    def test_pull_error_event_fails_and_records_nothing(self):
        self.fake.events = [{'status': 'pulling manifest'}, {'error': 'pull model manifest: file does not exist'}]
        with self.assertRaises(RuntimeError):
            mg.pull('small')
        self.assertFalse(self.pulls.exists())

    def test_pull_without_success_status_fails(self):
        self.fake.events = [{'status': 'pulling manifest'}]
        with self.assertRaises(RuntimeError):
            mg.pull('small')
        self.assertFalse(self.pulls.exists())


class ManifestFetch(GuardTest):
    fake_manifest = False

    def serve(self, body=None, error=None):
        seen = []

        def urlopen(req, timeout=None):
            seen.append((req, timeout))
            if error:
                raise error
            return io.BytesIO(body)
        p = mock.patch.object(mg.urllib.request, 'urlopen', urlopen)
        p.start()
        self.addCleanup(p.stop)
        return seen

    def test_sums_config_and_layers_and_hashes_the_body(self):
        body = json.dumps({'config': {'size': 10}, 'layers': [{'size': 100}, {'size': 1000}]}).encode()
        seen = self.serve(body)
        self.assertEqual(mg._manifest('qwen3:8b'), (1110, hashlib.sha256(body).hexdigest()))
        req = seen[0][0]
        self.assertEqual(req.full_url, 'https://registry.ollama.ai/v2/library/qwen3/manifests/8b')
        self.assertEqual(req.get_header('Accept'), 'application/vnd.docker.distribution.manifest.v2+json')
        self.assertEqual(mg._manifest('phi4')[0], 1110)
        self.assertEqual(seen[1][0].full_url, 'https://registry.ollama.ai/v2/library/phi4/manifests/latest')

    def test_refuses_the_pull_when_the_registry_is_unreachable(self):
        self.serve(error=urllib.error.URLError('no route'))
        self.assertRefused('small', text='cannot read the registry manifest')

    def test_refuses_the_pull_when_the_registry_answers_with_an_http_error(self):
        self.serve(error=urllib.error.HTTPError('u', 404, 'Not Found', {}, None))
        self.assertRefused('small', text='cannot read the registry manifest')

    def test_refuses_a_manifest_that_cannot_give_a_size(self):
        for body in (b'not json', b'{}', b'{"config": {"size": 5}}', b'{"config": {"size": 0}, "layers": []}',
                     b'{"config": {"size": "x"}, "layers": [{"size": 1}]}'):
            self.serve(body)
            self.assertRefused('small')

    def test_refuses_nan_boolean_negative_and_non_integer_sizes(self):
        bodies = {
            'NaN config size': b'{"config": {"size": NaN}, "layers": [{"size": 1000}]}',
            'NaN layer size': b'{"config": {"size": 10}, "layers": [{"size": NaN}]}',
            'true as config size': b'{"config": {"size": true}, "layers": [{"size": 5}]}',
            'true as layer size': b'{"config": {"size": 0}, "layers": [{"size": true}]}',
            'false as layer size': b'{"config": {"size": 7}, "layers": [{"size": false}]}',
            '-1 as layer size': b'{"config": {"size": 10}, "layers": [{"size": -1}]}',
            '-1 as config size': b'{"config": {"size": -1}, "layers": [{"size": 1000}]}',
            'negative cancelling a positive': b'{"config": {"size": 1000}, "layers": [{"size": -999}, {"size": 5}]}',
            'float size': b'{"config": {"size": 1.5}, "layers": [{"size": 2}]}',
            'whole float size': b'{"config": {"size": 10.0}, "layers": [{"size": 2}]}',
            'string size': b'{"config": {"size": "5"}, "layers": [{"size": 2}]}',
            'null size': b'{"config": {"size": null}, "layers": [{"size": 2}]}',
        }
        for label, body in bodies.items():
            with self.subTest(label):
                self.serve(body)
                with self.assertRaises(mg.Refused) as cm:
                    mg._manifest('small')
                self.assertIn('unusable sizes', str(cm.exception))
                self.assertRefused('small', text='unusable sizes')

    def test_accepts_zero_sized_layers_when_the_total_is_positive(self):
        self.serve(b'{"config": {"size": 0}, "layers": [{"size": 0}, {"size": 7}]}')
        self.assertEqual(mg._manifest('small')[0], 7)

    def test_pulled_digest_is_compared_with_the_hash_of_the_manifest_body(self):
        body = json.dumps({'config': {'size': 1000}, 'layers': [{'size': 2000}]}).encode()
        self.serve(body)
        self.fake.digest = hashlib.sha256(body).hexdigest()
        self.assertEqual(mg.pull('small'), self.fake.digest)
        self.fake.tags.clear()
        self.fake.digest = DIGEST_C
        with self.assertRaises(RuntimeError):
            mg.pull('other')
        self.assertIn(('DELETE', '/api/delete', {'model': 'other'}), self.fake.calls)


class RemoteModels(GuardTest):
    """A cloud model copied under an allowed name (ollama cp kimi-k3:cloud phi4) must never be called."""

    def copy_as_phi4(self, in_tags=False, in_show=False, digest=DIGEST_B):
        entry = {'name': 'phi4:latest', 'digest': digest}
        if in_tags:
            entry.update(CLOUD_SHOW)
        self.fake.tags.append(entry)
        if in_show:
            self.fake.show['phi4'] = dict(CLOUD_SHOW)

    def test_unload_refuses_a_cloud_model_copied_under_an_allowed_name(self):
        self.copy_as_phi4(in_show=True)  # /api/show returns remote metadata under the name phi4
        self.assertRefused('phi4', fn=mg.unload, text='runs remotely', requests=('/api/generate',))
        self.assertIn(('POST', '/api/show', {'model': 'phi4'}), self.fake.calls)

    def test_unload_refuses_when_only_the_tags_entry_is_remote(self):
        self.copy_as_phi4(in_tags=True)
        self.assertRefused('phi4', fn=mg.unload, text='runs remotely', requests=('/api/generate', '/api/show'))

    def test_pull_refuses_an_installed_cloud_copy_and_does_not_record_it(self):
        self.copy_as_phi4(in_show=True)
        self.assertRefused('phi4', text='runs remotely')
        self.assertEqual(self.pinned('phi4'), '')

    def test_unload_refuses_an_installed_digest_that_differs_from_the_pin(self):
        mg._set_digest('phi4', DIGEST_A)
        self.copy_as_phi4(digest=DIGEST_B)  # remote metadata hidden, but the build is not the pinned one
        self.assertRefused('phi4', fn=mg.unload, text='pinned', requests=('/api/generate',))

    def test_unload_accepts_a_local_model_whose_digest_matches_the_pin(self):
        mg._set_digest('phi4', DIGEST_A)
        self.copy_as_phi4(digest=DIGEST_A)
        mg.unload('phi4')
        self.assertIn(('POST', '/api/generate', {'model': 'phi4', 'keep_alive': 0}), self.fake.calls)

    def test_show_error_reply_blocks_unload_before_any_generate_request(self):
        self.copy_as_phi4()
        self.fake.show['phi4'] = {'error': 'model "phi4" not found'}
        self.assertRefused('phi4', fn=mg.unload, text='cannot prove', requests=('/api/generate',))

    def test_malformed_show_replies_block_unload_before_any_generate_request(self):
        self.copy_as_phi4()
        replies = {'empty object': {}, 'unrelated fields': {'unexpected': True}, 'list': [], 'text': 'ok',
                   'error next to genuine fields': {'error': 'partial failure', 'details': {}},
                   'null': None, 'malformed JSON from Ollama': RuntimeError('malformed JSON'),
                   'undecodable': ValueError('Expecting value')}
        for label, reply in replies.items():
            with self.subTest(label):
                self.fake.show['phi4'] = reply
                self.assertRefused('phi4', fn=mg.unload, text='cannot prove', requests=('/api/generate',))

    def test_unreachable_show_blocks_unload_before_any_generate_request(self):
        self.copy_as_phi4()
        self.fake.show['phi4'] = urllib.error.URLError('connection reset')
        with self.assertRaises(OSError):
            mg.unload('phi4')
        self.assertNotIn('/api/generate', self.fake.paths())

    def test_show_error_reply_refuses_the_pull_of_an_installed_model_and_records_nothing(self):
        self.copy_as_phi4()
        self.fake.show['phi4'] = {'error': 'server busy'}
        self.assertRefused('phi4', text='cannot prove')
        self.assertEqual(self.pinned('phi4'), '')

    def test_genuine_show_reply_with_one_standard_field_is_accepted(self):
        self.copy_as_phi4()
        self.fake.show['phi4'] = {'capabilities': ['completion']}
        mg.unload('phi4')
        self.assertIn('/api/generate', self.fake.paths())


class HttpReplies(GuardTest):
    """The real _http against a stubbed connection."""

    def stub(self, body):
        opener = mock.Mock()
        opener.open.return_value = io.BytesIO(body)
        p = mock.patch.object(mg.urllib.request, 'build_opener', return_value=opener)
        p.start()
        self.addCleanup(p.stop)

    def test_yields_each_json_object(self):
        self.stub(b'{"a": 1}\n\n{"b": 2}\n')
        self.assertEqual(list(REAL_HTTP('GET', '/x')), [{'a': 1}, {'b': 2}])

    def test_malformed_json_is_a_failure_not_a_traceback(self):
        self.stub(b'{"a": 1}\nthis is not json\n')
        with self.assertRaises(RuntimeError) as cm:
            list(REAL_HTTP('POST', '/api/show', {'model': 'x'}))
        self.assertIn('malformed JSON', str(cm.exception))

    def test_a_json_value_that_is_not_an_object_is_a_failure(self):
        self.stub(b'[1, 2]\n')
        with self.assertRaises(RuntimeError):
            list(REAL_HTTP('GET', '/x'))


class Unload(GuardTest):
    def setUp(self):
        super().setUp()
        self.fake.tags.append({'name': 'small:latest', 'digest': DIGEST_A})

    def test_unload_sends_keep_alive_zero_then_confirms_ps_is_empty(self):
        mg.unload('small')
        self.assertEqual(self.fake.paths(), ['/api/tags', '/api/show', '/api/generate', '/api/ps'])
        self.assertIn(('POST', '/api/generate', {'model': 'small', 'keep_alive': 0}), self.fake.calls)

    def test_unload_waits_for_ollama_to_drop_the_model(self):
        self.fake.ps = [['small'], ['small'], []]
        mg.unload('small')
        self.assertEqual(self.fake.paths().count('/api/ps'), 3)

    def test_unload_fails_loudly_when_a_model_stays_loaded(self):
        self.fake.ps = [['small']]
        with self.assertRaises(RuntimeError) as cm:
            mg.unload('small')
        self.assertIn('small', str(cm.exception))

    def test_unload_fails_on_an_error_response(self):
        self.fake.generate = [{'error': 'model "small" not found'}]
        with self.assertRaises(RuntimeError) as cm:
            mg.unload('small')
        self.assertIn('unload failed: model "small" not found', str(cm.exception))
        self.assertNotIn('/api/ps', self.fake.paths(), 'a failed unload must not fall through to the ps check')

    def test_unload_fails_on_an_empty_response_stream(self):
        self.fake.generate = []
        with self.assertRaises(RuntimeError) as cm:
            mg.unload('small')
        self.assertIn('no completed unload reply', str(cm.exception))
        self.assertNotIn('/api/ps', self.fake.paths())

    def test_unload_fails_when_the_reply_is_not_an_unload(self):
        for reply in ({'done': True, 'done_reason': 'stop'}, {'done': False, 'done_reason': 'unload'}, {'done': True}):
            self.fake.generate = [reply]
            with self.assertRaises(RuntimeError, msg=reply):
                mg.unload('small')

    def test_unload_fails_for_a_model_that_is_not_installed(self):
        self.fake.tags.clear()
        with self.assertRaises(RuntimeError):
            mg.unload('small')
        self.assertNotIn('/api/generate', self.fake.paths())

    def test_unload_refuses_cloud_and_unlisted_names_without_any_request(self):
        self.fake.calls.clear()
        for name in ('kimi-k3:cloud', 'gpt-oss:120b-cloud', 'llama3:8b', 'gpl-model'):
            with self.assertRaises(mg.Refused, msg=name):
                mg.unload(name)
        self.assertEqual(self.fake.calls, [])

    def test_check_empty_fails_when_anything_is_loaded(self):
        self.fake.ps = [['qwen3.5:9b']]
        with self.assertRaises(RuntimeError):
            mg.check_empty()

    def test_check_empty_passes_on_an_empty_list(self):
        mg.check_empty()


class Cli(GuardTest):
    def run_cli(self, *argv):
        with mock.patch('sys.stderr'), mock.patch('sys.stdout'):
            return mg.main(list(argv))

    def test_exit_codes(self):
        self.assertEqual(self.run_cli('pull', 'kimi-k3:cloud'), 2)
        self.assertEqual(self.run_cli('pull', 'llama3:8b'), 2)
        self.assertEqual(self.run_cli('pull', 'small'), 0)
        self.assertEqual(self.run_cli('check-empty'), 0)
        self.assertEqual(self.run_cli('unload', 'small'), 0)
        self.fake.ps = [['small']]
        self.assertEqual(self.run_cli('check-empty'), 1)

    def test_ollama_down_is_an_operational_failure(self):
        def down(*a, **k):
            raise ConnectionRefusedError('down')
            yield
        with mock.patch.object(mg, '_http', down):
            self.assertEqual(self.run_cli('check-empty'), 1)

    def test_pull_and_unload_need_a_name(self):
        with self.assertRaises(SystemExit):
            self.run_cli('pull')


class RealConfig(unittest.TestCase):
    def test_engine_models_toml_is_valid_and_complete(self):
        cfg = mg.load()
        self.assertEqual(cfg['host'], {'disk_path': '/mnt/c', 'disk_path_windows': 'C:\\', 'floor_gb': 8})
        self.assertEqual(set(cfg['models']), {
            'bge-m3', 'qwen3-embedding:0.6b', 'qwen3-embedding:4b', 'phi4', 'devstral:24b',
            'gpt-oss:20b', 'qwen3:14b', 'qwen3:8b', 'qwen3-coder:30b', 'qwen3:30b', 'gemma4:12b',
            'nemotron-3.5-lightning', 'qwen3.6:35b-a3b-coding-mtp-q4_K_M', 'glm-4.7-flash:q4_K_M'})
        for name, m in cfg['models'].items():
            self.assertFalse(name.lower().endswith(('-cloud', ':cloud')), name)
            self.assertEqual(m['allowed'], m['licence'] in mg.LICENCES, name)
            if not m['allowed']:
                self.assertTrue(m.get('reason'), name)
            self.assertRegex(m['digest'], r'^(sha256:)?([0-9a-f]{64})?$', name)
            self.assertLessEqual(m['num_ctx'], mg.CAPS[m['role']], name)


if __name__ == '__main__':
    unittest.main()
