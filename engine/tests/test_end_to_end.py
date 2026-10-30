"""End to end on a small fixture folder against the real Postgres and Ollama.
Skipped with a message when either is down. Uses its own table and state directory."""
import copy
import tempfile
import unittest
from pathlib import Path

from cerebrollm import config, store
from tests import SCRATCH

FILES = {
    "alpha/review.md": "# Review\n\n## Rounds\n\nA change gets two review rounds before it merges. "
                       "The zephyrquartz token marks this chunk in the lexical test.\n",
    "alpha/guide-rev2.md": "# Guide\n\nThe current guide explains how the pipeline records evidence.\n",
    "alpha/guide-rev1.md": "# Guide\n\nThe old guide explained how the pipeline recorded evidence.\n",
    "alpha/evidence/run.md": "# Run\n\nzephyrquartz appears in a never-index folder.\n",
    "alpha/key.md": "# Key\n\naws " + "AKIA" + "ABCDEFGHIJKLMNOP" + " leaked\n",   # built at runtime
}
FILES["a-old/review.md"] = FILES["alpha/review.md"]   # identical copy: indexed once, also_at
FILES["alpha/merge.md"] = "# Merge\n\nA pull request merges when both checks pass.\n"   # PR synonym


def unavailable():
    try:
        with store.sql(config.load()) as cur:
            cur.execute("select 1")
    except Exception as exc:                                    # noqa: BLE001
        return "Postgres unavailable: %s" % exc
    try:
        cfg = config.load()
        if store.model_digest(cfg) is None:
            return "Ollama has no bge-m3 model"
    except Exception as exc:                                    # noqa: BLE001
        return "Ollama unavailable: %s" % exc
    return None


REASON = unavailable()


@unittest.skipIf(REASON, REASON or "")
class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        cls.root = Path(cls.tmp.name) / "corpus"
        for rel, text in FILES.items():
            p = cls.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        data = copy.deepcopy(config.load().data)
        data["domain"] = "org"
        data["state_dir"] = str(Path(cls.tmp.name) / "state")
        data["postgres"]["table"] = "cerebrollm_test"
        data["root"] = [{"name": "fx", "kind": "dir", "path": str(cls.root), "ref": "file"}]
        data["rule"] = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"}]
        cls.cfg = config.Config(data, Path("test"))

    @classmethod
    def tearDownClass(cls):
        with store.sql(cls.cfg) as cur:
            cur.execute("drop table if exists %s" % cls.cfg.data_table)
        cls.tmp.cleanup()

    def test_flow(self):
        from cerebrollm import search, status, verify
        from cerebrollm.indexer import run_index
        cfg = self.cfg

        first = run_index(cfg)
        # key.md (secret) and evidence/ skipped; a-old/review.md is a copy of alpha/review.md
        self.assertEqual(first["documents"], 4)
        self.assertEqual(first["duplicates_collapsed"], 1)
        self.assertEqual(len(first["skipped_secret"]), 1)
        self.assertGreater(first["chunks_embedded"], 0)
        self.assertEqual(first["chunks_located"], first["chunks_embedded"])

        s = status.collect(cfg)
        self.assertEqual(s["never_violations"], 0)
        self.assertEqual(s["documents"], 4)

        for mode in ("lexical", "vector", "hybrid"):
            hits = search.run_search(cfg, "how many review rounds does a change get", k=3, mode=mode)
            self.assertTrue(hits, mode)
            self.assertEqual(hits[0]["path"], "alpha/review.md", mode)
            self.assertEqual(hits[0]["heading_path"], "Review > Rounds")
            self.assertEqual(hits[0]["line_start"], 1)           # the bare "# Review" merged forward
            self.assertEqual(hits[0]["also_at"], ["fx:a-old/review.md"], mode)

        lexical = search.run_search(cfg, "zephyrquartz", mode="lexical")
        self.assertEqual({h["path"] for h in lexical}, {"alpha/review.md"})   # evidence/ never indexed
        self.assertEqual(verify.run_verify(cfg, "a-old/review.md", "two review rounds before it merges")[0],
                         "OK")                                   # a collapsed copy is still indexed

        # "PR" in the query reaches "pull request" in the text through the synonym table (lexical arm)
        merge = search.run_search(cfg, "when is a PR ready", k=3, mode="lexical", synonyms=True)
        self.assertEqual(merge[0]["path"], "alpha/merge.md")

        self.assertTrue(search.run_search(cfg, "review:  rounds (any)? | & !", mode="lexical"))  # operators are safe

        current = {h["path"] for h in search.run_search(cfg, "guide pipeline evidence", mode="hybrid")}
        self.assertNotIn("alpha/guide-rev1.md", current)         # superseded is filtered out
        everything = {h["path"] for h in search.run_search(cfg, "guide pipeline evidence", mode="hybrid",
                                                           all_status=True)}
        self.assertIn("alpha/guide-rev1.md", everything)

        code, _ = verify.run_verify(cfg, "alpha/review.md", "two review rounds before it merges")
        self.assertEqual(code, "OK")
        self.assertEqual(verify.run_verify(cfg, "alpha/review.md", "a made-up quote")[0], "MISSING")

        again = run_index(cfg, changed=True)
        self.assertEqual(again["chunks_embedded"], 0)            # nothing changed, nothing embedded

        (self.root / "alpha/review.md").write_text(FILES["alpha/review.md"] + "\nAn extra line.\n")
        self.assertEqual(verify.run_verify(cfg, "alpha/review.md", "two review rounds")[0], "CHANGED")
        third = run_index(cfg, changed=True)
        self.assertGreater(third["chunks_embedded"], 0)
        self.assertEqual(verify.run_verify(cfg, "alpha/review.md", "two review rounds")[0], "OK")

        (self.root / "alpha/guide-rev1.md").unlink()
        run_index(cfg, changed=True)
        # review.md (new bytes), a-old/review.md (old bytes, no longer a copy), guide-rev2.md and
        # merge.md; the removed guide-rev1.md left the index
        self.assertEqual(status.collect(cfg)["documents"], 4)


if __name__ == "__main__":
    unittest.main()
