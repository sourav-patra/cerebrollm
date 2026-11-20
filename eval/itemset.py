"""Settings of one public item set (eval/itemset-<name>.toml). Stdlib only.

An item set is a JSON-lines file of items, the folder of saved sources its quotes point into, and the numbers the
checker and the report hold it to: how many items of each group and kind, the earliest publication date of a source,
the grader, and the printed-bound target. The v2 file carries the values that were once written into
check_items_v2.py and report_v2.py, so v2's output does not change.

The set a run uses is named by --set on run_v2.py and check_items_v2.py, which pass it on in CEREBROLLM_ITEMSET;
without either, "v2".
"""
import os
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = "CEREBROLLM_ITEMSET"
DEFAULT = "v2"


class ItemSet:
    def __init__(self, name, data):
        self.name = name
        self.items = os.path.join(HERE, data["items"])
        self.sources = os.path.join(HERE, data["sources"])
        self.cutoff = data["cutoff"]
        self.judge = data["judge"]
        self.runs_dir = data["runs_dir"]
        self.results = os.path.join(HERE, data["results"])
        self.target_pct = data.get("target_pct")   # printed-bound target in percent, or None for no statement
        self.want = {(w["group"], w["kind"]): w["count"] for w in data["want"]}
        # answers with an expected verdict that the grader must get right before its verdicts can support the target
        self.canaries = [(c["id"], c["answer"], c["verdict"]) for c in data.get("canary", [])]

    @property
    def total(self):
        return sum(self.want.values())

    @property
    def n_unanswerable(self):
        return sum(c for (g, k), c in self.want.items() if k == "unanswerable")

    @property
    def n_answerable(self):
        return self.total - self.n_unanswerable

    def kind_count(self, kind):
        return sum(c for (g, k), c in self.want.items() if k == kind)


def load(name=None):
    name = name or os.environ.get(ENV) or DEFAULT
    path = os.path.join(HERE, "itemset-%s.toml" % name)
    if not os.path.isfile(path) or not name.replace("-", "").replace("_", "").isalnum():
        raise SystemExit("unknown item set %r: no eval/itemset-%s.toml" % (name, name))
    with open(path, "rb") as f:
        return ItemSet(name, tomllib.load(f))


def load_early():
    """(settings, error) at import time, before --set is parsed: the set named by the environment, or v2 together
    with the error when that name is unknown, so that an explicit --set is not defeated by a stale environment value."""
    try:
        return load(), None
    except (SystemExit, OSError, ValueError) as e:   # unknown name, unreadable file or invalid TOML (a ValueError)
        return load(DEFAULT), SystemExit(str(e)) if not isinstance(e, SystemExit) else e
