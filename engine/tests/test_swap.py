"""Full rebuild into a new table, then swap. Runs against the real Postgres and Ollama on its own table
(cerebrollm_swaptest) and state directory; skipped with a message when either is down, as in
test_end_to_end. The embedding model is wrapped so that a build can be held or failed after its first
batch (one chunk per batch)."""
import copy
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from llama_index.embeddings.ollama import OllamaEmbedding

from cerebrollm import config, store
from tests import SCRATCH
from tests.test_end_to_end import FILES, REASON

TABLE = "cerebrollm_swaptest"
HOOK = {"before": None}   # called with the text count before each Ollama embed call of a build


class HookedEmbedding(OllamaEmbedding):
    def get_general_text_embeddings(self, texts):
        if HOOK["before"] is not None:
            HOOK["before"](len(texts))
        return super().get_general_text_embeddings(texts)


def hooked_embed_model(cfg):
    return HookedEmbedding(model_name=cfg.ollama["model"], base_url=cfg.ollama["base_url"],
                           embed_batch_size=1, ollama_additional_kwargs=cfg.ollama_options)


def make_cfg(root, state):
    data = copy.deepcopy(config.load().data)
    data["state_dir"] = str(state)
    data["postgres"]["table"] = TABLE
    data["root"] = [{"name": "fx", "kind": "dir", "path": str(root), "ref": "file"}]
    data["rule"] = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"}]
    return config.Config(data, Path("test"))


def write_corpus(root, files):
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


@unittest.skipIf(REASON, REASON or "")
class TestSwap(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.root = Path(self.tmp.name) / "corpus"
        write_corpus(self.root, FILES)
        self.cfg = make_cfg(self.root, Path(self.tmp.name) / "state")
        self.live = self.cfg.data_table
        self.new = self.cfg.next_data_table
        self.old = "data_%s_old" % self.cfg.table

    def tearDown(self):
        HOOK["before"] = None
        for name in (self.live, self.new, self.old):
            store.drop_table(self.cfg, name)
        self.tmp.cleanup()

    def exists(self, name):
        with store.sql(self.cfg) as cur:
            return store._regclass(cur, name)

    def live_names(self):
        """Index and sequence names of the live table, as PGVectorStore creates them."""
        return sorted([TABLE + "_idx", TABLE + "_idx_1", "data_%s_id_seq" % TABLE, "data_%s_pkey" % TABLE])

    def live_relation_names(self):
        with store.sql(self.cfg) as cur:
            return sorted(name for _, name in store.relations(cur, self.live))

    def test_two_full_builds(self):
        from cerebrollm import search
        from cerebrollm.indexer import run_index
        for _ in range(2):
            run_index(self.cfg)
            hits = search.run_search(self.cfg, "how many review rounds does a change get", k=3, mode="hybrid")
            self.assertEqual(hits[0]["path"], "alpha/review.md")
            self.assertTrue(self.exists(self.live))
            self.assertFalse(self.exists(self.new))
            self.assertFalse(self.exists(self.old))
            names = self.live_relation_names()
            self.assertEqual(names, self.live_names())

    def test_search_during_build_reads_live_rows(self):
        from cerebrollm import search
        from cerebrollm.indexer import run_index
        run_index(self.cfg)
        (self.root / "alpha/new.md").write_text("# New\n\nThe marmotquill token appears only in a new file.\n")
        started, release = threading.Event(), threading.Event()

        def hold_after_first_batch(_count):
            if not started.is_set():
                started.set()
                release.wait(120)
        HOOK["before"] = hold_after_first_batch
        errors = []

        def build():
            try:
                run_index(self.cfg)
            except BaseException as exc:                     # noqa: BLE001
                errors.append(exc)
        worker = threading.Thread(target=build)
        with mock.patch("cerebrollm.store.embed_model", hooked_embed_model):
            worker.start()
            self.assertTrue(started.wait(120), "build did not reach its first batch")
            during = search.run_search(self.cfg, "marmotquill", mode="lexical")
            release.set()
            worker.join(300)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(during, [])
        self.assertTrue(search.run_search(self.cfg, "marmotquill", mode="lexical"))

    def test_failed_build_leaves_live_table_and_docstore(self):
        from cerebrollm.indexer import run_index
        run_index(self.cfg)
        live_rows = store.row_count(self.cfg, self.live)
        docstore_before = self.cfg.docstore_path.read_bytes()
        calls = []

        def fail_on_second_batch(count):
            calls.append(count)
            if len(calls) == 2:
                raise RuntimeError("injected failure after the first batch")
        HOOK["before"] = fail_on_second_batch
        with mock.patch("cerebrollm.store.embed_model", hooked_embed_model):
            with self.assertRaises(RuntimeError):
                run_index(self.cfg)
        self.assertEqual(len(calls), 2)
        self.assertEqual(store.row_count(self.cfg, self.live), live_rows)
        self.assertEqual(self.cfg.docstore_path.read_bytes(), docstore_before)
        self.assertFalse(self.exists(self.new))
        self.assertFalse(self.cfg.next_docstore_path.exists())
        self.assertEqual(self.live_relation_names(), self.live_names())

    def test_small_new_table_is_refused(self):
        from cerebrollm.indexer import run_index
        run_index(self.cfg)
        live_rows = store.row_count(self.cfg, self.live)
        docstore_before = self.cfg.docstore_path.read_bytes()
        for p in self.root.rglob("*.md"):
            if p.name != "merge.md":
                p.unlink()
        with self.assertRaises(SystemExit) as caught:
            run_index(self.cfg)
        message = str(caught.exception)
        new_rows = store.row_count(self.cfg, self.new)
        self.assertGreater(new_rows, 0)
        self.assertLess(2 * new_rows, live_rows)
        self.assertIn("store.drop_table", message)
        self.assertIn(str(live_rows), message)
        self.assertEqual(store.row_count(self.cfg, self.live), live_rows)
        self.assertEqual(self.cfg.docstore_path.read_bytes(), docstore_before)
        self.assertTrue(self.exists(self.new))
        self.assertTrue(self.cfg.next_docstore_path.exists())


class TestEmbedOptions(unittest.TestCase):
    def test_embed_model_carries_num_ctx(self):
        model = store.embed_model(config.load())
        self.assertEqual(model.ollama_additional_kwargs, {"num_ctx": 8192})

    def test_query_prefix_goes_before_queries_only(self):
        cfg = config.load()
        cfg.ollama["query_prefix"] = "Instruct: find passages\nQuery:"
        model = store.embed_model(cfg)
        self.assertEqual(model._format_query("hello"), "Instruct: find passages\nQuery: hello")
        self.assertEqual(model._format_text("hello"), "hello")
        del cfg.ollama["query_prefix"]
        self.assertEqual(store.embed_model(cfg)._format_query("hello"), "hello")


class TestModelDigest(unittest.TestCase):
    """store.model_digest with ollama.Client mocked: no Ollama, no model is loaded."""

    def digest(self, name, installed):
        cfg = config.load()
        cfg.ollama["model"] = name
        models = [mock.Mock(model=m, digest="d-" + m) for m in installed]
        with mock.patch("ollama.Client") as client:
            client.return_value.list.return_value = mock.Mock(models=models)
            return store.model_digest(cfg)

    INSTALLED = ["qwen3-embedding:4b", "qwen3-embedding:0.6b", "bge-m3:latest"]

    def test_tagged_name_matches_its_own_tag_not_a_sibling(self):
        self.assertEqual(self.digest("qwen3-embedding:0.6b", self.INSTALLED), "d-qwen3-embedding:0.6b")
        self.assertEqual(self.digest("qwen3-embedding:4b", self.INSTALLED), "d-qwen3-embedding:4b")

    def test_untagged_name_matches_latest(self):
        self.assertEqual(self.digest("bge-m3", self.INSTALLED), "d-bge-m3:latest")

    def test_absent_model_gives_none(self):
        self.assertIsNone(self.digest("qwen3-embedding:8b", self.INSTALLED))
        self.assertIsNone(self.digest("qwen3-embedding", self.INSTALLED))   # no :latest installed


if __name__ == "__main__":
    unittest.main()
