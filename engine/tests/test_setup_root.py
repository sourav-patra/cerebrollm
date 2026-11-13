"""setup/root-ubuntu.sh with stub apt-get and systemctl: a PostgreSQL service that existed before the
script is left as it was; only a service the install itself created is stopped and disabled."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "setup" / "root-ubuntu.sh"

STUB_SYSTEMCTL = """#!/bin/bash
echo "systemctl $*" >> "$STUB_LOG"
case "$1" in
  cat) [ "$STUB_UNIT" = yes ] ;;
  *) exit 0 ;;
esac
"""
STUB_APT = """#!/bin/bash
echo "apt-get $*" >> "$STUB_LOG"
"""


class TestRootSetup(unittest.TestCase):
    def run_script(self, unit, systemd=True):
        with tempfile.TemporaryDirectory() as d:
            bin_dir, log = Path(d, "bin"), Path(d, "log")
            bin_dir.mkdir()
            stubs = {"apt-get": STUB_APT}
            if systemd:
                stubs["systemctl"] = STUB_SYSTEMCTL
            for name, body in stubs.items():
                p = bin_dir / name
                p.write_text(body)
                p.chmod(0o755)
            env = dict(os.environ, PATH="%s:/usr/bin:/bin" % bin_dir, STUB_LOG=str(log), STUB_UNIT=unit)
            if not systemd:   # hide any real systemctl
                env["PATH"] = "%s:%s" % (bin_dir, Path(d, "empty"))
                env["PATH"] += ":" + ":".join(p for p in ("/usr/bin", "/bin") if not Path(p, "systemctl").exists())
            r = subprocess.run(["/bin/bash", str(SCRIPT)], env=env, capture_output=True, text=True)
            return r, (log.read_text().splitlines() if log.exists() else [])

    def test_a_service_that_existed_before_is_left_alone(self):
        r, calls = self.run_script("yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("left as it was", r.stdout)
        self.assertFalse([c for c in calls if c.startswith("systemctl disable")])
        self.assertIn("apt-get install -y python3.12-venv postgresql-16 postgresql-16-pgvector zstd", calls)

    def test_a_service_the_install_created_is_stopped_and_disabled(self):
        r, calls = self.run_script("no")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("systemctl disable --now postgresql", calls)
        self.assertLess(calls.index("apt-get update"), calls.index("systemctl disable --now postgresql"))

    def test_no_systemd_still_completes(self):
        r, calls = self.run_script("no", systemd=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse([c for c in calls if c.startswith("systemctl")])


if __name__ == "__main__":
    unittest.main()
