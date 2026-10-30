"""Shared test settings. Test scratch directories live under $HOME/.cerebrollm so that no test writes
outside the repository and the cerebrollm state directory."""
import os

SCRATCH = os.path.join(os.path.expanduser("~"), ".cerebrollm", "test-scratch")
os.makedirs(SCRATCH, exist_ok=True)
