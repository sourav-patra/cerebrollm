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
            os.chmod(folder, 0o750)
            self.assertEqual(status.socket_dir_mode(folder), "0750  (open to other users: chmod 700 it)")
            os.chmod(folder, 0o700)
            self.assertEqual(status.socket_dir_mode(os.path.join(folder, "absent")), "missing")

    def test_status_prints_the_mode(self):
        cfg = config.load()
        with mock.patch("cerebrollm.store.read_state", lambda c: {}), \
                mock.patch("cerebrollm.store.table_exists", lambda c: False), \
                mock.patch("cerebrollm.status.socket_dir_mode", lambda p: "0700"):
            text = status.format_status(cfg, status.collect(cfg))
        self.assertIn("postgres socket folder: %s  mode 0700" % cfg.pg["socket_dir"], text)


if __name__ == "__main__":
    unittest.main()
