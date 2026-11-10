"""cerebrollm status: the socket folder mode line. No database."""
import os
import tempfile
import unittest
from unittest import mock

from cerebrollm import config, status


class TestSocketMode(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "POSIX permission bits")
    def test_private_open_and_missing_folders(self):
        with tempfile.TemporaryDirectory() as folder:
            os.chmod(folder, 0o700)
            self.assertEqual(status.socket_dir_mode(folder), "0700")
            os.chmod(folder, 0o755)
            self.assertEqual(status.socket_dir_mode(folder), "0755")
            os.chmod(folder, 0o700)
            self.assertEqual(status.socket_dir_mode(os.path.join(folder, "absent")), "missing")
        with mock.patch("os.stat", side_effect=PermissionError):
            self.assertEqual(status.socket_dir_mode("/x"), "unreadable")

    def text_for(self, mode):
        cfg = config.load()
        with mock.patch("cerebrollm.store.read_state", lambda c: {}), \
                mock.patch("cerebrollm.store.table_exists", lambda c: False), \
                mock.patch("cerebrollm.status.socket_dir_mode", lambda p: mode):
            return cfg, status.format_status(cfg, status.collect(cfg))

    def test_status_prints_the_mode_and_warns_only_when_open(self):
        cfg, text = self.text_for("0700")
        self.assertIn("postgres socket folder: %s  mode 0700" % cfg.pg["socket_dir"], text)
        self.assertNotIn("WARNING", text)
        for mode in ("0755", "0710", "0701"):
            self.assertIn("WARNING: other local users can reach the database socket", self.text_for(mode)[1], mode)
        for mode in ("missing", "unreadable", "not checked on Windows"):
            self.assertNotIn("WARNING", self.text_for(mode)[1], mode)


if __name__ == "__main__":
    unittest.main()
