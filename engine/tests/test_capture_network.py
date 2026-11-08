"""The address classifier and argument check of tests/capture_network.py (no network)."""
import contextlib
import io
import unittest

from tests import capture_network as C


class TestCapture(unittest.TestCase):
    def test_loopback_and_unix_sockets_are_local(self):
        for addr in ("/srv/.cerebrollm/pg16/sock/.s.PGSQL.54329", b"/run/x.sock", ("127.0.0.1", 11434),
                     ("127.8.0.1", 1), ("::1", 11434), ("localhost", 11434)):
            self.assertTrue(C.is_local(addr), addr)

    def test_other_hosts_are_remote(self):
        for addr in (("10.0.0.5", 11434), ("huggingface.co", 443), ("127.0.0.1.example.com", 80)):
            self.assertFalse(C.is_local(addr), addr)

    def test_missing_arguments_print_usage(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(C.main([]), 2)
            self.assertEqual(C.main(["out.txt", "search", "q"]), 2)
        self.assertIn("Network capture check", err.getvalue())


if __name__ == "__main__":
    unittest.main()
