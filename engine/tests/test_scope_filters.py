"""Path-prefix and date filters of `search`.

Index tests build a small index in Postgres on a table and state directory of their own, with the
embedding model replaced by a deterministic MockEmbedding subclass for both indexing and the query, so
they need Postgres but not Ollama. Each class gets a table named cerebrollm_scope_<label>_<random>,
refuses to run if that table or the configured table is in use, and drops only its own tables
afterwards. They skip with the cause only when Postgres is unreachable. The argument validation tests of
the CLI and the MCP tool need nothing."""
import contextlib
import copy
import datetime
import io
import os
import re
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

from llama_index.core.embeddings.mock_embed_model import MockEmbedding

from cerebrollm import cli, config, mcp_server, search, store
from tests import SCRATCH

MODES = ("lexical", "vector", "hybrid")
WORD = re.compile(r"[a-z0-9]+")


def postgres_unavailable():
    try:
        with store.sql(config.load()) as cur:
            cur.execute("select 1")
    except Exception as exc:   # noqa: BLE001
        return "Postgres unavailable: %s" % exc
    return None


REASON = postgres_unavailable()


class KeywordEmbedding(MockEmbedding):
    """Two informative dimensions: the share of the word "needle" in the text, and the rest. A text
    that is all "needle" sits next to the query "needle"; a text that mentions it once sits far away."""

    def _vec(self, text):
        words = WORD.findall(text.lower())
        share = words.count("needle") / len(words) if words else 0.0
        return [share, 1.0 - share] + [0.0] * (self.embed_dim - 2)

    def _get_text_embedding(self, text):
        return self._vec(text)

    def _get_query_embedding(self, query):
        return self._vec(query)

    async def _aget_text_embedding(self, text):
        return self._vec(text)

    async def _aget_query_embedding(self, query):
        return self._vec(query)


def make_cfg(root, state, table):
    data = copy.deepcopy(config.load().data)
    data["state_dir"] = str(state)
    data["postgres"]["table"] = table
    data["root"] = [{"name": "fx", "kind": "dir", "path": str(root), "ref": "file"}]
    data["rule"] = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"}]
    return config.Config(data, Path("test"))


def fresh_table(label):
    """A table name no configured index can have: a fixed prefix and a random suffix, per run."""
    name = "cerebrollm_scope_%s_%s" % (label, uuid.uuid4().hex[:10])
    if name == config.load().pg["table"]:
        raise AssertionError("fixture table equals the configured table")
    return name


def index_fixture(testcase, cfg, mtime=None):
    """Index the corpus of cfg into its own fresh tables, with the stand-in embedding model, and
    drop exactly those tables when the test class ends. Never touches another table."""
    for patcher in (mock.patch("cerebrollm.store.embed_model",
                               lambda c: KeywordEmbedding(embed_dim=c.pg["embed_dim"])),
                    mock.patch("cerebrollm.store.model_digest", lambda c: None)):
        patcher.start()
        testcase.addClassCleanup(patcher.stop)
    if mtime is not None:
        patcher = mock.patch("cerebrollm.corpus._mtime", mtime)
        patcher.start()
        testcase.addClassCleanup(patcher.stop)
    own = (cfg.data_table, cfg.next_data_table, "data_%s_old" % cfg.table)
    if cfg.table == config.load().pg["table"] or any(_exists(cfg, name) for name in own):
        raise AssertionError("fixture table %s is in use; refusing to touch it" % cfg.table)
    testcase.addClassCleanup(lambda: [store.drop_table(cfg, name) for name in own])
    from cerebrollm.indexer import run_index
    run_index(cfg)
    return cfg


def _exists(cfg, name):
    with store.sql(cfg) as cur:
        return store._regclass(cur, name)


def build_index(testcase, files, mtimes, label):
    """Write the files, index them, and clean up with the test class. Returns the config."""
    tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
    testcase.addClassCleanup(tmp.cleanup)
    root = Path(tmp.name) / "corpus"
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    cfg = make_cfg(root, Path(tmp.name) / "state", fresh_table(label))
    return index_fixture(testcase, cfg, lambda r, rel, commit: mtimes.get(rel, "2020-06-01T00:00:00+00:00"))


def make_git_repo(repo, date):
    """Commit everything under repo with a fixed identity and date. The host's Git configuration (a
    signing requirement, hooks, a template) is ignored, so the fixture does not depend on it."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date, GIT_AUTHOR_NAME="t",
               GIT_AUTHOR_EMAIL="t@example.com", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
    off = ["-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", "-c", "core.hooksPath=" + os.devnull]
    for cmd in (["init", "-q"], ["add", "-A"], [*off, "commit", "-q", "-m", "fixture"]):
        subprocess.run(["git", "-C", str(repo), *cmd], check=True, env=env, capture_output=True)


def build_git_index(testcase, repos, label):
    """repos: {root name: (project, {path: text}, commit date)}; one git root each, ref HEAD."""
    tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
    testcase.addClassCleanup(tmp.cleanup)
    data = copy.deepcopy(config.load().data)
    data["state_dir"] = str(Path(tmp.name) / "state")
    data["postgres"]["table"] = fresh_table(label)
    data["root"], data["rule"] = [], []
    for name, (project, files, date) in repos.items():
        repo = Path(tmp.name) / name
        for rel, text in files.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text)
        make_git_repo(repo, date)
        data["root"].append({"name": name, "kind": "git", "path": str(repo), "ref": "HEAD", "project": project})
        data["rule"].append({"root": name, "glob": "**/*.md", "tier": "T2", "status": "current"})
    return index_fixture(testcase, config.Config(data, Path("test")))   # mtime = the commit date


FILES = {
    "alpha/b/one.md": "# One\n\nmarker text of the first file under alpha b.\n",
    "alpha/b/deep/two.md": "# Two\n\nmarker text of the second file under alpha b deep.\n",
    "alpha/bc.md": "# Sibling\n\nmarker text of a sibling whose name starts like the prefix.\n",
    "alpha/exact.md": "# Exact\n\nmarker text of a file that a whole-path prefix names.\n",
    "alpha/b_/x.md": "# Underscore\n\nmarker text under a folder with an underscore.\n",
    "alpha/bx/y.md": "# Wildcard\n\nmarker text under a folder that an unescaped underscore would match.\n",
    "alpha/100%/z.md": "# Percent\n\nmarker text under a folder with a percent sign.\n",
    "alpha/100x/z.md": "# Percent twin\n\nmarker text under a folder an unescaped percent sign would match.\n",
    "alpha/it's:odd/n.md": "# Quote\n\nmarker text under a folder with a quote and a colon.\n",
    "alpha/q\\:r/s.md": "# Backslash\n\nmarker text under a folder with a backslash before a colon.\n",
    "beta/one.md": "# Beta\n\nmarker text of a file in the other project.\n",
    "beta/b/three.md": "# Beta b\n\nmarker text of a beta file under a b folder.\n",
    "odd/badday.md": "# Bad day\n\nmarker text of a file whose stored date has no such day.\n",
    "odd/garbage.md": "# Garbage\n\nmarker text of a file whose stored date is not a date.\n",
}
# The same instant as 2026-01-01T00:00:00Z written with three different offsets, and neighbours.
MTIMES = {
    "alpha/b/one.md": "2026-01-01T05:30:00+05:30",
    "alpha/b/deep/two.md": "2025-12-31T23:59:59+00:00",
    "alpha/bc.md": "2026-01-01T00:00:01+00:00",
    "alpha/exact.md": "2026-01-02T00:00:00+00:00",
    "alpha/b_/x.md": "2026-01-01T00:00:00-08:00",    # 2026-01-01T08:00:00Z
    "alpha/bx/y.md": "2026-01-01T23:59:59+00:00",
    "alpha/100%/z.md": "2026-01-03T00:00:00+00:00",
    "alpha/100x/z.md": "2026-01-03T00:00:00+00:00",
    "alpha/it's:odd/n.md": "2026-01-04T00:00:00+00:00",
    "alpha/q\\:r/s.md": "2026-01-05T00:00:00+00:00",
    "beta/one.md": "2026-01-01T12:00:00-08:00",      # 2026-01-01T20:00:00Z
    "beta/b/three.md": "2025-06-01T00:00:00+00:00",
    "odd/badday.md": "2026-02-30T00:00:00Z",           # shaped like a date, rejected by a timestamp cast
    "odd/garbage.md": "not a date",
}


def paths(results):
    return sorted(r["path"] for r in results)


@unittest.skipIf(REASON, REASON or "")
class TestScopeOnIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = build_index(cls, FILES, MTIMES, "small")

    def run_scoped(self, mode, **kw):
        return search.run_search(self.cfg, "marker", k=50, mode=mode, **kw)

    def test_every_file_is_indexed(self):
        for mode in MODES:
            self.assertEqual(paths(self.run_scoped(mode)), sorted(FILES), mode)

    def test_prefix_stops_at_a_segment_boundary(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="alpha/b")),
                                 ["alpha/b/deep/two.md", "alpha/b/one.md"])
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="alpha/b/")),
                                 ["alpha/b/deep/two.md", "alpha/b/one.md"])
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="alpha/b/deep")),
                                 ["alpha/b/deep/two.md"])

    def test_prefix_equal_to_a_whole_path_matches_it_only(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="alpha/bc.md")), ["alpha/bc.md"])
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="alpha/bc")), [])
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="alpha/exact.md")), ["alpha/exact.md"])

    def test_prefix_wildcard_characters_are_literal(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="alpha/b_")), ["alpha/b_/x.md"])
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="alpha/100%")), ["alpha/100%/z.md"])

    def test_paths_with_quote_colon_and_backslash_survive_the_filter(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="alpha/it's:odd")), ["alpha/it's:odd/n.md"])
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="alpha/q\\:r")), ["alpha/q\\:r/s.md"])
                # a date filter puts every matching path, odd ones included, into one IN list
                got = paths(self.run_scoped(mode, since="2026-01-03", until="2026-01-05"))
                self.assertEqual(got, ["alpha/100%/z.md", "alpha/100x/z.md", "alpha/it's:odd/n.md",
                                       "alpha/q\\:r/s.md"])

    def test_offsets_that_name_one_instant_compare_equal(self):
        same = ("2026-01-01T00:00:00Z", "2026-01-01T05:30:00+05:30", "2025-12-31T16:00:00-08:00",
                "2026-01-01T00:00:00")   # no offset: UTC
        for mode in MODES:
            for t in same:
                with self.subTest(mode=mode, t=t):
                    since = paths(self.run_scoped(mode, path_prefix="alpha/b", since=t))
                    until = paths(self.run_scoped(mode, path_prefix="alpha/b", until=t))
                    self.assertEqual(since, ["alpha/b/one.md"])                      # one.md is at the instant
                    self.assertEqual(until, ["alpha/b/deep/two.md", "alpha/b/one.md"])   # one.md is not after it

    def test_date_boundaries(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                # a bare since is 00:00 UTC: the file at exactly 2026-01-02T00:00:00Z is in, 23:59:59 the day before is out
                self.assertIn("alpha/exact.md", paths(self.run_scoped(mode, since="2026-01-02")))
                self.assertNotIn("alpha/bx/y.md", paths(self.run_scoped(mode, since="2026-01-02")))
                self.assertIn("alpha/bx/y.md", paths(self.run_scoped(mode, since="2026-01-01")))
                # a bare until is the whole day: 23:59:59 is in, the next midnight is out
                day = paths(self.run_scoped(mode, until="2026-01-01"))
                self.assertIn("alpha/bx/y.md", day)
                self.assertIn("beta/one.md", day)
                self.assertNotIn("alpha/exact.md", day)
                # a single day
                self.assertEqual(paths(self.run_scoped(mode, since="2026-01-01", until="2026-01-01")),
                                 ["alpha/b/one.md", "alpha/b_/x.md", "alpha/bc.md", "alpha/bx/y.md", "beta/one.md"])
                # a date-time until is inclusive
                self.assertEqual(paths(self.run_scoped(mode, since="2026-01-02", until="2026-01-02T00:00:00Z")),
                                 ["alpha/exact.md"])

    def test_a_stored_date_that_cannot_be_read_excludes_only_its_own_document(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="odd")),
                                 ["odd/badday.md", "odd/garbage.md"])
                got = paths(self.run_scoped(mode, since="2025-01-01", until="2026-12-31"))
                self.assertIn("alpha/b/one.md", got)
                self.assertFalse([p for p in got if p.startswith("odd/")])
                self.assertEqual(paths(self.run_scoped(mode, path_prefix="odd", since="2000-01-01")), [])

    def test_hits_are_checked_again_so_a_stale_lookup_cannot_admit_an_out_of_range_document(self):
        """A full index swap between the lookup and the retrieval could pair a document id admitted under
        its old date with a row of the new table dated outside the range. Simulated with a lookup that
        returns every document id."""
        every = ["org:%s:file:%s" % (p.split("/")[0], p) for p in FILES]
        with mock.patch("cerebrollm.search.scope_doc_ids", return_value=every):
            for mode in MODES:
                with self.subTest(mode=mode):
                    got = paths(self.run_scoped(mode, since="2026-01-02", until="2026-01-03"))
                    self.assertEqual(got, ["alpha/100%/z.md", "alpha/100x/z.md", "alpha/exact.md"])
                    got = paths(self.run_scoped(mode, path_prefix="alpha/b"))
                    self.assertEqual(got, ["alpha/b/deep/two.md", "alpha/b/one.md"])

    def test_scope_combines_with_project(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertEqual(paths(self.run_scoped(mode, project="beta", path_prefix="b")), [])
                self.assertEqual(paths(self.run_scoped(mode, project="beta", path_prefix="beta/b")),
                                 ["beta/b/three.md"])
                self.assertEqual(paths(self.run_scoped(mode, project="alpha", path_prefix="beta")), [])
                self.assertEqual(paths(self.run_scoped(mode, project="beta", since="2026-01-01")), ["beta/one.md"])
                self.assertEqual(paths(self.run_scoped(mode, project="alpha", until="2026-01-01")),
                                 ["alpha/b/deep/two.md", "alpha/b/one.md", "alpha/b_/x.md", "alpha/bc.md",
                                  "alpha/bx/y.md"])

    def test_empty_scope_returns_no_hits_without_running_the_retrievers(self):
        with mock.patch("cerebrollm.search.VectorStoreIndex.from_vector_store") as index:
            index.return_value.as_retriever.side_effect = AssertionError("retriever must not run")
            self.assertEqual(search.run_search(self.cfg, "marker", path_prefix="nowhere"), [])

    def test_without_scope_arguments_the_scope_query_never_runs(self):
        with mock.patch("cerebrollm.search.scope_doc_ids", side_effect=AssertionError("scope query ran")):
            for mode in MODES:
                self.assertEqual(paths(self.run_scoped(mode)), sorted(FILES))
                self.assertEqual(paths(search.run_search(self.cfg, "marker", k=50, mode=mode, path_prefix="",
                                                         since=None, until=None)), sorted(FILES))

    def test_a_scope_that_matches_everything_changes_nothing(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                plain = search.run_search(self.cfg, "marker", k=50, mode=mode)
                scoped = search.run_search(self.cfg, "marker", k=50, mode=mode, path_prefix="/")
                self.assertEqual(plain, scoped)

    def test_bad_dates_raise_before_any_query(self):
        for since, until in (("nope", None), (None, "2026-13-01"), ("", None), (None, ""),
                             ("2026-02-01", "2026-01-01"),
                             ("2026-01-02T00:00:00Z", "2026-01-01")):
            with self.subTest(since=since, until=until):
                with self.assertRaisesRegex(ValueError, "^Invalid date"):
                    search.run_search(self.cfg, "marker", since=since, until=until)

    def test_the_scope_query_matches_the_stored_mtime_as_an_instant(self):
        got = search.scope_doc_ids(self.cfg, False, None, since="2026-01-01T00:00:00Z", until="2026-01-01T00:00:00Z")
        self.assertEqual(got, ["org:alpha:file:alpha/b/one.md"])


HOT = {"hot/h%02d.md" % i: "# Hot\n\n" + "needle " * 30 + "hot%02d\n" % i for i in range(50)}
COLD = {"cold/c%02d.md" % i: "# Cold\n\nthe needle appears once among many other words, cold%02d, in a long "
                             "passage of filler text about nothing else\n" % i for i in range(10)}
BULK_DOCS = int(os.environ.get("CEREBROLLM_SCOPE_BULK_DOCS", "1000"))   # raise it to measure longer path lists
BULK = {"bulk/b%05d.md" % i: "# Bulk\n\nbulkword filler number %d\n" % i for i in range(BULK_DOCS)}


@unittest.skipIf(REASON, REASON or "")
class TestScopeBeyondTheCandidateLimit(unittest.TestCase):
    """50 passages that outrank the 10 in cold/ for the query, and 1,000 others for a long path list."""

    @classmethod
    def setUpClass(cls):
        cls.cfg = build_index(cls, {**HOT, **COLD, **BULK}, {}, "big")

    def test_a_filtered_query_returns_k_hits_that_lie_beyond_the_unfiltered_top_k(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                top = search.run_search(self.cfg, "needle", k=50, mode=mode)
                self.assertEqual(len(top), 50)
                self.assertTrue(all(r["path"].startswith("hot/") for r in top))   # cold/ is beyond the top 50
                fetch = max(5 * self.cfg.search["fetch_factor"], 40)
                self.assertLess(fetch, 50)                                          # a post-filter would see no cold/ hit
                got = search.run_search(self.cfg, "needle", k=5, mode=mode, path_prefix="cold")
                self.assertEqual(len(got), 5)
                self.assertTrue(all(r["path"].startswith("cold/") for r in got))
                self.assertEqual([r["rank"] for r in got], [1, 2, 3, 4, 5])

    def test_a_long_path_list(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                got = search.run_search(self.cfg, "bulkword", k=50, mode=mode, path_prefix="bulk")
                self.assertEqual(len(got), 50)
                self.assertTrue(all(r["path"].startswith("bulk/") for r in got))
        self.assertEqual(len(search.scope_doc_ids(self.cfg, False, None, path_prefix="bulk")), len(BULK))


class TestGitFixture(unittest.TestCase):
    def test_a_host_that_signs_commits_does_not_break_the_fixture(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            hostile = Path(tmp) / "gitconfig"
            hostile.write_text("[commit]\n\tgpgsign = true\n[tag]\n\tgpgsign = true\n"
                               "[gpg]\n\tprogram = %s\n" % os.devnull)
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "a.md").write_text("text\n")
            with mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(hostile), "GIT_CONFIG_COUNT": "1",
                                              "GIT_CONFIG_KEY_0": "commit.gpgsign", "GIT_CONFIG_VALUE_0": "true"}):
                make_git_repo(repo, "2026-01-01T00:00:00+00:00")
            out = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%cI"], check=True,
                                 capture_output=True, text=True).stdout.strip()
            # some git versions print a UTC date with "Z", others with "+00:00"; compare the instant
            self.assertEqual(datetime.datetime.fromisoformat(out),
                             datetime.datetime.fromisoformat("2026-01-01T00:00:00+00:00"))


@unittest.skipIf(REASON, REASON or "")
class TestScopeAcrossRoots(unittest.TestCase):
    """Two git roots that both hold README.md, with different text and commit dates."""

    @classmethod
    def setUpClass(cls):
        cls.cfg = build_git_index(cls, {
            "old": ("one", {"README.md": "# Old\n\nmarker text of the older readme. " + "needle " * 20 + "\n"}, "2026-01-10T10:00:00+00:00"),
            "new": ("two", {"README.md": "# New\n\nmarker text of the newer readme, which mentions the needle once among other words.\n",
                            "docs/new-only.md": "# Only\n\nmarker text only in the newer root.\n"},
                    "2026-03-01T10:00:00+00:00"),
        }, "roots")

    def test_a_date_bound_never_admits_the_same_path_of_another_root(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                got = search.run_search(self.cfg, "marker", k=50, mode=mode, since="2026-02-01")
                self.assertEqual(sorted((r["project"], r["path"]) for r in got),
                                 [("two", "README.md"), ("two", "docs/new-only.md")])
                got = search.run_search(self.cfg, "marker", k=50, mode=mode, until="2026-02-01")
                self.assertEqual([(r["project"], r["path"]) for r in got], [("one", "README.md")])

    def test_the_better_ranked_readme_of_the_other_root_does_not_take_the_only_slot(self):
        """The older README outranks the newer one for the query; with k=1 a filter that let it through
        would leave the answer empty."""
        self.assertEqual(search.scope_doc_ids(self.cfg, False, None, since="2026-02-01"),
                         ["org:two:HEAD:README.md", "org:two:HEAD:docs/new-only.md"])
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertEqual([(r["project"], r["path"]) for r in
                                  search.run_search(self.cfg, "needle", k=50, mode=mode)][0], ("one", "README.md"))
                got = search.run_search(self.cfg, "needle", k=1, mode=mode, since="2026-02-01")
                self.assertEqual([(r["project"], r["path"]) for r in got], [("two", "README.md")])

    def test_both_retrievers_filter_on_document_identity_not_on_path(self):
        """The hit check would hide a path-only filter unless more than the candidate limit of
        wrong-root rows competed, so the filter handed to the retrievers is inspected directly."""
        seen = []
        real = search.VectorStoreIndex.as_retriever

        def spy(index, **kw):
            seen.append(kw["filters"])
            return real(index, **kw)

        with mock.patch.object(search.VectorStoreIndex, "as_retriever", spy):
            search.run_search(self.cfg, "needle", k=1, mode="hybrid", since="2026-02-01")
        self.assertEqual(len(seen), 2)   # one per arm
        for filters in seen:
            scope = [f for f in filters.filters if f.key == "ref_doc_id"]
            self.assertEqual(len(scope), 1)
            self.assertEqual(sorted(v.replace("\\:", ":") for v in scope[0].value),   # colons are escaped for the store
                             ["org:two:HEAD:README.md", "org:two:HEAD:docs/new-only.md"])
            self.assertFalse([f for f in filters.filters if f.key == "path"])

    def test_a_path_prefix_keeps_both_roots_and_project_picks_one(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                got = search.run_search(self.cfg, "marker", k=50, mode=mode, path_prefix="README.md")
                self.assertEqual(sorted(r["project"] for r in got), ["one", "two"])
                got = search.run_search(self.cfg, "marker", k=50, mode=mode, path_prefix="README.md",
                                        project="one", until="2026-02-01")
                self.assertEqual([(r["project"], r["path"]) for r in got], [("one", "README.md")])


class TestParsing(unittest.TestCase):
    def utc(self, *a):
        return search.datetime.datetime(*a, tzinfo=search.datetime.timezone.utc)

    def test_a_bare_date(self):
        self.assertEqual(search.parse_instant("2026-01-31"), (self.utc(2026, 1, 31), False))
        self.assertEqual(search.parse_instant("2026-01-31", upper=True), (self.utc(2026, 2, 1), True))
        self.assertEqual(search.parse_instant("2026-12-31", upper=True), (self.utc(2027, 1, 1), True))

    def test_a_date_time(self):
        self.assertEqual(search.parse_instant("2026-01-31T09:30:00"), (self.utc(2026, 1, 31, 9, 30), False))
        self.assertEqual(search.parse_instant("2026-01-31T09:30:00Z", upper=True), (self.utc(2026, 1, 31, 9, 30), False))
        when, _ = search.parse_instant("2026-01-31T09:30:00+05:30")
        self.assertEqual(when, self.utc(2026, 1, 31, 4, 0))

    def test_the_last_day_has_an_upper_bound(self):
        when, exclusive = search.parse_instant("9999-12-31", upper=True)
        self.assertFalse(exclusive)
        self.assertEqual(when, search.datetime.datetime.max.replace(tzinfo=search.datetime.timezone.utc))
        self.assertEqual(search.parse_scope("2026-01-01", "9999-12-31")[1], when)
        self.assertEqual(search.parse_instant("9999-12-31"), (self.utc(9999, 12, 31), False))
        lo, hi, ex = search.parse_scope(None, "9999-12-31")
        self.assertTrue(search.in_scope("a.md", "9999-12-31T23:59:59+00:00", "", lo, hi, ex))

    def test_only_the_t_separator_is_a_date_time(self):
        self.assertEqual(search.parse_instant("2026-01-01T12:00:00"), (self.utc(2026, 1, 1, 12), False))
        self.assertEqual(search.parse_instant("20260101T120000"), (self.utc(2026, 1, 1, 12), False))
        for bad in ("2026-01-01X12:00:00", "2026-01-01 12:00:00", "2026-01-01t12:00:00", "2026-01-01_12:00",
                    "2026-01-01T"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "^Invalid date"):
                    search.parse_instant(bad)

    def test_bad_input(self):
        for bad in ("", "tomorrow", "2026-02-30", "2026-13-01", "31/01/2026", "2026-01-31T25:00:00"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "^Invalid date"):
                    search.parse_instant(bad)

    def test_range(self):
        self.assertEqual(search.parse_scope(None, None), (None, None, False))
        self.assertEqual(search.parse_scope("2026-01-01", "2026-01-01")[2], True)
        search.parse_scope("2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z")   # equal bounds are a valid instant
        with self.assertRaisesRegex(ValueError, "^Invalid date range"):
            search.parse_scope("2026-01-02", "2026-01-01")
        for bad in ("", " "):   # only None means not given
            with self.assertRaisesRegex(ValueError, "^Invalid date"):
                search.parse_scope(bad, None)
            with self.assertRaisesRegex(ValueError, "^Invalid date"):
                search.parse_scope(None, bad)
        with self.assertRaisesRegex(ValueError, "^Invalid date range") as ctx:
            search.parse_scope("2026-02-01\n", "2026-01-01\r\n")
        self.assertEqual(len(str(ctx.exception).splitlines()), 1)

    def test_in_scope(self):
        lo, hi, ex = search.parse_scope("2026-01-01", "2026-01-01")
        self.assertTrue(search.in_scope("a/b.md", "2026-01-01T10:00:00+00:00", "a", lo, hi, ex))
        self.assertFalse(search.in_scope("ab.md", "2026-01-01T10:00:00+00:00", "a", lo, hi, ex))
        self.assertFalse(search.in_scope("a/b.md", "2026-01-02T00:00:00+00:00", "", lo, hi, ex))
        self.assertFalse(search.in_scope("a/b.md", None, "", lo, hi, ex))
        self.assertFalse(search.in_scope("a/b.md", "2026-02-30T00:00:00Z", "", lo, hi, ex))
        self.assertTrue(search.in_scope("a/b.md", None, "a/b.md", None, None, False))


class TestCli(unittest.TestCase):
    def run_cli(self, *argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                cli.main(["search", "query", *argv])
        return ctx.exception.code, err.getvalue()

    def test_a_bad_date_is_an_argparse_error(self):
        for flag in ("--since", "--until"):
            with self.subTest(flag=flag):
                code, err = self.run_cli(flag, "yesterday")
                self.assertEqual(code, 2)
                self.assertIn("Invalid date 'yesterday'", err)

    def test_an_empty_date_is_an_argparse_error(self):
        for flag in ("--since", "--until"):
            with self.subTest(flag=flag):
                code, err = self.run_cli(flag, "")
                self.assertEqual(code, 2)
                self.assertIn("Invalid date", err)

    def test_since_after_until_is_an_argparse_error(self):
        code, err = self.run_cli("--since", "2026-02-01", "--until", "2026-01-01")
        self.assertEqual(code, 2)
        self.assertIn("Invalid date range", err)

    def test_the_flags_reach_run_search_and_are_absent_when_unset(self):
        with mock.patch("cerebrollm.search.run_search", return_value=[]) as run, contextlib.redirect_stdout(io.StringIO()):
            cli.main(["search", "query"])
            cli.main(["search", "query", "--project", "p", "--path-prefix", "a/b", "--since", "2026-01-01",
                      "--until", "2026-01-31T10:00:00Z"])
        first, second = run.call_args_list
        self.assertEqual(first.kwargs, {})
        self.assertEqual(first.args[1:], ("query", None, None, False, None, None))
        self.assertEqual(second.kwargs, {"path_prefix": "a/b", "since": "2026-01-01", "until": "2026-01-31T10:00:00Z"})
        self.assertEqual(second.args[5], "p")


class RecordingSearch:
    def __init__(self):
        self.calls = []

    def __call__(self, cfg, query, k=None, mode=None, all_status=False, project=None, synonyms=None, **scope):
        self.calls.append(scope)
        return []


class TestMcp(unittest.TestCase):
    def call(self, **kw):
        fake = RecordingSearch()
        with mock.patch("cerebrollm.search.run_search", fake):
            return mcp_server.search_tool("query", **kw), fake.calls

    def test_the_arguments_reach_run_search_and_are_absent_when_unset(self):
        out, calls = self.call()
        self.assertEqual(calls, [{}])
        self.assertTrue(out.endswith("Page 1: no further page."))
        _, calls = self.call(path_prefix="a/b", since="2026-01-01", until="2026-01-31")
        self.assertEqual(calls, [{"path_prefix": "a/b", "since": "2026-01-01", "until": "2026-01-31"}])

    def test_a_bad_date_is_one_line_and_nothing_runs(self):
        for kw in ({"since": "soon"}, {"until": "2026-02-30"}, {"since": "2026-02-01", "until": "2026-01-01"},
                   {"since": ""}, {"until": ""}, {"since": "2026-02-01\n", "until": "2026-01-01"},
                   {"since": "2026-02-01", "until": "2026-01-01\r\n"}, {"since": "a\nb"}):
            with self.subTest(kw=kw):
                out, calls = self.call(**kw)
                self.assertTrue(out.startswith("Invalid date"), out)
                self.assertEqual(len(out.splitlines()), 1)
                self.assertEqual(calls, [])

    def test_the_tool_lists_the_arguments_and_describes_them(self):
        import asyncio
        tool = next(t for t in asyncio.run(mcp_server.server.list_tools()) if t.name == "search")
        for name in ("path_prefix", "since", "until"):
            self.assertIn(name, tool.description)
            self.assertIn(name, tool.input_schema["properties"])
            self.assertNotIn(name, tool.input_schema.get("required", []))


if __name__ == "__main__":
    unittest.main()
