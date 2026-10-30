import sys
import tempfile
import unittest
from pathlib import Path

import studyconfig

ENGINE = Path(studyconfig.HERE).parents[1] / 'engine'
sys.path.insert(0, str(ENGINE))
BASE = (ENGINE / 'cerebrollm.toml').read_text()


def write(tmp, text):
    p = Path(tmp) / 'study.toml'
    p.write_text(text)
    return p


class TestLoad(unittest.TestCase):
    def test_unset_variable_in_any_key_names_key_and_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, '[postgres]\nbin = "${NO_SUCH_VAR_X}/bin"\n')
            with self.assertRaises(SystemExit) as cm:
                studyconfig.load(p)
            msg = str(cm.exception)
            self.assertIn('postgres.bin', msg)
            self.assertIn('study.toml', msg)

    def test_expands_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = studyconfig.load(write(tmp, '[postgres]\nbin = "$HOME/pg"\n'))
            self.assertNotIn('$', data['postgres']['bin'])

    def test_missing_key_names_key(self):
        with self.assertRaises(SystemExit) as cm:
            studyconfig.get({'a': {}}, 'a', 'b', 'study.toml')
        self.assertIn('[a] b', str(cm.exception))

    def test_shipped_study_toml_loads(self):
        self.assertTrue(studyconfig.PG_BIN)


class TestEnginePaths(unittest.TestCase):
    def build(self, tmp, data, corpus):
        from cerebrollm import config
        text = studyconfig.engine_config_text(BASE, data, corpus)
        p = Path(tmp) / 'built.toml'
        p.write_text(text)
        return config.load(p)

    def test_defaults_leave_the_text_unchanged(self):
        self.assertEqual(studyconfig.engine_config_text(BASE), BASE)

    def test_changed_paths_reach_the_built_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self.build(tmp, Path(tmp) / 'state', Path(tmp) / 'notes')
            self.assertEqual(str(cfg.state_dir), str(Path(tmp) / 'state'))
            self.assertEqual(cfg.pg['socket_dir'], str(Path(tmp) / 'state' / 'pg16' / 'sock'))
            self.assertEqual(cfg.roots['notes']['path'], str(Path(tmp) / 'notes'))


if __name__ == '__main__':
    unittest.main()
