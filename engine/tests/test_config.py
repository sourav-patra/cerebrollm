import os
import unittest
from unittest import mock

from cerebrollm import config


class ExpandPathsTest(unittest.TestCase):
    def test_variables_and_home_expand_in_path_keys(self):
        with mock.patch.dict(os.environ, {"NOTES_ROOT": "/data/notes", "HOME": "/srv/u"}):
            data = config.expand_paths({"state_dir": "$HOME/state", "postgres": {"socket_dir": "$NOTES_ROOT/sock"},
                                        "root": [{"name": "n", "path": "$NOTES_ROOT"}], "domain": "$NOT_A_PATH"})
        self.assertEqual(data["state_dir"], "/srv/u/state")
        self.assertEqual(data["postgres"]["socket_dir"], "/data/notes/sock")
        self.assertEqual(data["root"][0]["path"], "/data/notes")
        self.assertEqual(data["domain"], "$NOT_A_PATH")   # only path keys expand

    def test_unset_variable_is_refused_with_its_key(self):
        env = {k: v for k, v in os.environ.items() if k != "CEREBROLLM_TEST_UNSET"}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, r"root\[0\]\.path"):
                config.expand_paths({"root": [{"path": "$CEREBROLLM_TEST_UNSET/x"}]})


if __name__ == "__main__":
    unittest.main()
