"""promptfoo exec provider for arm A1 (see n2_lib.py)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import n2_lib  # noqa: E402

n2_lib.arm_main("A1")
