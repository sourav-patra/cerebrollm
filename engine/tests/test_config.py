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


class OllamaUrlTest(unittest.TestCase):
    def test_loopback_addresses_pass(self):
        for url in ("http://127.0.0.1:11434", "http://localhost:11434", "http://[::1]:11434"):
            config.check_ollama_url({"base_url": url})

    def test_remote_address_is_refused_unless_allowed(self):
        for url in ("http://192.168.1.5:11434", "https://ollama.example.com", "http://127.0.0.1.example.com"):
            with self.assertRaisesRegex(ValueError, "not a loopback address"):
                config.check_ollama_url({"base_url": url})
        with self.assertRaisesRegex(ValueError, "allow_remote"):
            config.check_ollama_url({"base_url": "http://10.0.0.2:11434", "allow_remote": "yes"})   # only true counts
        config.check_ollama_url({"base_url": "http://10.0.0.2:11434", "allow_remote": True})

    def test_shipped_config_loads(self):
        self.assertEqual(config.load().ollama["base_url"], "http://127.0.0.1:11434")

    def test_loading_a_config_with_a_remote_address_is_refused(self):
        import tomllib
        with open(config.DEFAULT_CONFIG, "rb") as f:
            data = config.expand_paths(tomllib.load(f))
        data["ollama"]["base_url"] = "http://10.0.0.5:11434"
        with self.assertRaisesRegex(ValueError, r"ollama\.base_url"):
            config.Config(data, config.DEFAULT_CONFIG)
        data["ollama"]["allow_remote"] = True
        config.Config(data, config.DEFAULT_CONFIG)


if __name__ == "__main__":
    unittest.main()
