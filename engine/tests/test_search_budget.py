"""Opt-in output budget (CLI --budget, MCP budget and offset) with stub hits: no database, no model.

The GOLDEN values were produced by the code of origin/main (before the budget existed) from the same
fixtures; they pin that output without --budget, budget and offset is unchanged."""
import contextlib
import hashlib
import io
import json
import os
import re
import unittest
from unittest import mock

import httpx
import psycopg2

from cerebrollm import cli, config, mcp_server, search
from tests.stubs import DepthSensitiveSearch, FakeSearch, hit, patched_search

# The repository's own configuration, never the host's CEREBROLLM_CONFIG: the fixed outputs below
# depend on its [search] token_budget.
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cerebrollm.toml")


class FixedConfig(unittest.TestCase):
    """The MCP tool reads a cached configuration; pin it for each test and restore it afterwards."""

    def setUp(self):
        patcher = mock.patch.object(mcp_server, "_cfg", config.load(CONFIG_PATH))
        patcher.start()
        self.addCleanup(patcher.stop)


BUDGETS = (50, 200, 2000)
COUNTS = (1, 5, 50)


def make_hits(n, text_len=600, **kw):
    return [hit(i + 1, text=("t%d " % (i + 1)) * (text_len // 3), **kw) for i in range(n)]


def run_cli(hits, *args):
    out = io.StringIO()
    with patched_search(FakeSearch(hits)), contextlib.redirect_stdout(out):
        code = cli.main(["--config", CONFIG_PATH, "search", "q", "--k", str(len(hits))] + list(args))
    return code, out.getvalue()


def shown_ranks(text):
    return [int(m) for m in re.findall(r"^#(\d+) score=", text, re.M)]


# The stub header is about 85 characters; this path makes it longer than the largest budget used here (8000).
OVERSIZED = "very/long/segment/" * 500 + "doc.md"


class TestBudgetCli(unittest.TestCase):
    def variants(self, n):
        yield "normal", make_hits(n)
        yield "huge text", make_hits(n, text_len=30000)
        yield "oversized headers", make_hits(n, path=OVERSIZED)
        mixed = make_hits(n)
        if n > 1:
            mixed[1] = dict(mixed[1], path=OVERSIZED)   # rank 2 cannot fit, so ranks 3 and later go with it
        yield "second header oversized", mixed

    def test_text_output_stays_within_budget_and_counts_what_it_dropped(self):
        for budget in BUDGETS:
            for n in COUNTS:
                for name, hits in self.variants(n):
                    with self.subTest(budget=budget, n=n, variant=name):
                        code, out = run_cli(hits, "--budget", str(budget))
                        self.assertEqual(code, 0)
                        self.assertLessEqual(len(out), budget * 4)          # includes print's newline
                        last = out.rstrip("\n").splitlines()[-1]
                        ranks = shown_ranks(out)
                        self.assertEqual(ranks, list(range(1, len(ranks) + 1)))   # rank order kept, no gaps
                        dropped = n - len(ranks)
                        if dropped:
                            self.assertEqual(last, "dropped: %d (ranks %d-%d)" % (dropped, len(ranks) + 1, n))
                        else:
                            self.assertEqual(last, "dropped: 0")

    def test_json_output_has_the_four_keys_and_stays_within_budget(self):
        for budget in BUDGETS:
            for n in COUNTS:
                for name, hits in self.variants(n):
                    with self.subTest(budget=budget, n=n, variant=name):
                        code, out = run_cli(hits, "--json", "--budget", str(budget))
                        self.assertEqual(code, 0)
                        self.assertLessEqual(len(out), budget * 4)
                        data = json.loads(out)
                        self.assertEqual(set(data), {"hits", "dropped", "dropped_ranks", "budget_tokens"})
                        self.assertEqual(data["budget_tokens"], budget)
                        ranks = [h["rank"] for h in data["hits"]]
                        self.assertEqual(ranks, list(range(1, len(ranks) + 1)))
                        self.assertEqual(data["dropped"], n - len(ranks))
                        expected = [len(ranks) + 1, n] if data["dropped"] else []
                        self.assertEqual(data["dropped_ranks"], expected)

    def test_everything_that_fits_is_shown_whole(self):
        hits = [hit(1, text="alpha body"), hit(2, text="beta body")]
        code, out = run_cli(hits, "--budget", "2000")
        self.assertEqual(out,
                         "#1 score=0.5000 T1 locked alpha/review.md L1-3@file example | Review sha=abababababab\n"
                         "alpha body\n\n"
                         "#2 score=0.5000 T1 locked alpha/review.md L1-3@file example | Review sha=abababababab\n"
                         "beta body\n"
                         "dropped: 0\n")
        code, out = run_cli(hits, "--json", "--budget", "2000")
        self.assertEqual(json.loads(out), {"hits": hits, "dropped": 0, "dropped_ranks": [],
                                           "budget_tokens": 2000})

    def test_lowest_ranks_go_first_and_the_last_kept_hit_is_trimmed_not_its_header(self):
        hits = make_hits(5, text_len=330)   # header about 85 characters; a hit with its text is about 420
        code, out = run_cli(hits, "--budget", "200")   # 800 characters
        self.assertEqual(shown_ranks(out), [1, 2])
        self.assertEqual(out.rstrip("\n").splitlines()[-1], "dropped: 3 (ranks 3-5)")
        header = "#2 score=0.5000 T1 locked alpha/review.md L1-3@file example | Review sha=abababababab"
        self.assertIn("\n" + header + "\n", out)                 # the trimmed hit keeps its whole header
        self.assertIn(search.TRUNCATED.strip(), out)       # and says its text was cut
        self.assertIn(hits[0]["text"].strip(), out)        # rank 1 is whole

    def test_a_trimmed_hit_is_marked_in_json(self):
        code, out = run_cli(make_hits(5, text_len=330), "--json", "--budget", "400")
        hits = json.loads(out)["hits"]
        self.assertTrue(hits[-1]["truncated"])
        self.assertGreaterEqual(len(hits), 2)
        self.assertTrue(all("truncated" not in h for h in hits[:-1]))

    def test_oversized_header_shows_no_hit_and_reports_all_dropped(self):
        code, out = run_cli(make_hits(3, path=OVERSIZED), "--budget", "50")
        self.assertEqual(out, "dropped: 3 (ranks 1-3)\n")
        code, out = run_cli(make_hits(3, path=OVERSIZED), "--json", "--budget", "50")
        self.assertEqual(json.loads(out), {"hits": [], "dropped": 3, "dropped_ranks": [1, 3], "budget_tokens": 50})

    def test_no_hits_at_all(self):
        code, out = run_cli([], "--budget", "50")
        self.assertEqual(out, "dropped: 0\n")
        code, out = run_cli([], "--json", "--budget", "50")
        self.assertEqual(json.loads(out), {"hits": [], "dropped": 0, "dropped_ranks": [], "budget_tokens": 50})

    def test_budget_replaces_the_configured_token_budget(self):
        # The configured budget (2000 tokens) would trim a 20000-character text; 20000 tokens does not.
        text = "w" * 20000
        code, out = run_cli([hit(1, text=text)], "--budget", "20000")
        self.assertIn(text, out)
        self.assertNotIn(search.TRUNCATED.strip(), out)

    def test_budget_outside_the_accepted_range_is_refused(self):
        for bad in ("0", "49", "20001", "-5"):
            with self.subTest(budget=bad), contextlib.redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as ctx:
                run_cli([hit(1)], "--budget", bad)
            self.assertEqual(ctx.exception.code, 2)


class TestBudgetMcp(FixedConfig):
    def test_whole_result_stays_within_budget_and_ranks_keep_order(self):
        for budget in BUDGETS:
            for n in COUNTS:
                for text_len in (600, 30000):
                    with self.subTest(budget=budget, n=n, text_len=text_len):
                        hits = make_hits(n, text_len=text_len)
                        with patched_search(FakeSearch(hits)):
                            out = mcp_server.search_tool("q", k=n, budget=budget)
                        self.assertLessEqual(len(out), budget * 4)
                        ranks = shown_ranks(out)
                        self.assertEqual(ranks, list(range(1, len(ranks) + 1)))
                        self.assertEqual(out.count(mcp_server.BEGIN), len(ranks))
                        self.assertEqual(out.count(mcp_server.END), len(ranks))
                        dropped = n - len(ranks)
                        last = out.splitlines()[-1]
                        if dropped:
                            self.assertTrue(last.startswith("Dropped rank"), last)
                            if ranks:
                                self.assertIn("to fit budget %d; call search with offset=%d" % (budget, len(ranks) + 1), last)
                            else:
                                self.assertIn("budget %d is too small for one hit" % budget, last)
                        else:
                            self.assertEqual(last, "Page 1: no further page.")

    def test_footer_names_the_dropped_ranks_and_the_offset(self):
        with patched_search(FakeSearch(make_hits(5, text_len=100))):
            out = mcp_server.search_tool("q", k=5, budget=200)   # 800 characters: two whole hits, a trimmed third
        self.assertEqual(shown_ranks(out), [1, 2, 3])
        self.assertIn("t3 t3 t3 t3 [...]", out)
        self.assertEqual(out.splitlines()[-1], "Dropped ranks 4-5 to fit budget 200; call search with offset=4.")

    def test_one_dropped_hit_is_named_in_the_singular(self):
        with patched_search(FakeSearch(make_hits(4, text_len=100))):
            out = mcp_server.search_tool("q", k=4, budget=200)
        self.assertEqual(shown_ranks(out), [1, 2, 3])
        self.assertEqual(out.splitlines()[-1], "Dropped rank 4 to fit budget 200; call search with offset=4.")

    def test_no_hit_fits_says_so(self):
        with patched_search(FakeSearch(make_hits(3))):
            out = mcp_server.search_tool("q", k=3, budget=50)
        self.assertEqual(shown_ranks(out), [])
        self.assertLessEqual(len(out), 200)
        self.assertEqual(out.splitlines()[-1],
                         "Dropped ranks 1-3: budget 50 is too small for one hit.")

    def test_an_oversized_header_is_dropped_with_everything_after_it(self):
        hits = make_hits(4)
        hits[1] = dict(hits[1], path=OVERSIZED)
        with patched_search(FakeSearch(hits)):
            out = mcp_server.search_tool("q", k=4, budget=2000)
        self.assertEqual(shown_ranks(out), [1])
        self.assertEqual(out.splitlines()[-1], "Dropped ranks 2-4 to fit budget 2000; call search with offset=2.")

    def test_offset_paging_reaches_every_dropped_hit(self):
        hits = make_hits(25, text_len=300)
        for k in (10, 3):
            with self.subTest(k=k):
                seen, offset, calls = [], 1, 0
                with patched_search(FakeSearch(hits)):
                    while offset and calls < 100:
                        out = mcp_server.search_tool("q", k=k, budget=200, offset=offset)
                        self.assertLessEqual(len(out), 800)
                        seen += shown_ranks(out)
                        m = re.search(r"call search with offset=(\d+)", out.splitlines()[-1])
                        offset = int(m.group(1)) if m else 0
                        calls += 1
                self.assertEqual(seen, list(range(1, 26)))                # every hit once, in order
                self.assertLess(calls, 100)

    def test_a_dropped_page_can_be_continued_with_offset(self):
        hits = make_hits(12, text_len=300)
        with patched_search(FakeSearch(hits)):
            out = mcp_server.search_tool("q", k=6, page=2, budget=200)
        ranks = shown_ranks(out)
        self.assertEqual(ranks[0], 7)
        first_dropped = ranks[-1] + 1
        self.assertTrue(out.splitlines()[-1].endswith("offset=%d." % first_dropped))
        with patched_search(FakeSearch(hits)):
            again = mcp_server.search_tool("q", k=6, budget=200, offset=first_dropped)
        self.assertEqual(shown_ranks(again)[0], first_dropped)

    def test_offset_without_budget(self):
        fake = FakeSearch(make_hits(8, text_len=30))
        with patched_search(fake):
            out = mcp_server.search_tool("q", k=2, offset=3)
        self.assertEqual(fake.calls[0]["k"], mcp_server.RANK_POOL)   # one depth whatever the offset
        self.assertEqual(shown_ranks(out), [3, 4])
        self.assertEqual(out.splitlines()[-1], "Offset 3: another page exists, call search with offset=5.")
        with patched_search(fake):
            out = mcp_server.search_tool("q", k=2, offset=7)
        self.assertEqual(shown_ranks(out), [7, 8])
        self.assertEqual(out.splitlines()[-1], "Offset 7: no further page.")
        with patched_search(fake):
            out = mcp_server.search_tool("q", k=2, offset=9)
        self.assertIn("No hits at offset 9.", out)

    def test_invalid_budget_and_offset_do_not_search(self):
        fake = FakeSearch(make_hits(3))
        with patched_search(fake):
            for bad in (0, 49, 20001, -1):
                self.assertIn("Invalid budget", mcp_server.search_tool("q", budget=bad))
            for bad in (0, -1, 5001):
                self.assertIn("Invalid offset", mcp_server.search_tool("q", offset=bad))
            self.assertIn("offset and page 2 or more cannot be combined",
                          mcp_server.search_tool("q", offset=1, page=2))
        self.assertEqual(fake.calls, [])
        with patched_search(fake):
            mcp_server.search_tool("q", k=50, offset=5000)
            mcp_server.search_tool("q", budget=50)
            mcp_server.search_tool("q", budget=20000, offset=1, page=1)
        self.assertEqual(len(fake.calls), 3)


class TestRankLimits(FixedConfig):
    def test_minimum_budget_holds_at_the_top_of_the_pool(self):
        hits = make_hits(300, text_len=3)
        cases = (({"page": 4}, "Dropped ranks 151-200: budget 50 is too small for one hit."),
                 ({"offset": 151}, "Dropped ranks 151-200: budget 50 is too small for one hit."),
                 ({"offset": 200}, "Dropped rank 200: budget 50 is too small for one hit."))
        for kw, last in cases:
            with self.subTest(**kw), patched_search(FakeSearch(hits)):
                out = mcp_server.search_tool("q", k=50, budget=50, **kw)
            self.assertLessEqual(len(out), 200)
            self.assertEqual(shown_ranks(out), [])
            self.assertEqual(out.splitlines()[-1], last)

    def test_advertised_offsets_are_accepted_and_inside_the_pool(self):
        # Starting offsets chosen around the pool edge and the accepted maximum, for three k and with
        # and without a budget; every offset a last line advertises is then called once more.
        hits = make_hits(300, text_len=3)
        for k in (1, 7, 50):
            for off in (1, 2, 149, 150, 151, 199, 200, 201, 4999, 5000):
                for budget in (None, 200):
                    with self.subTest(k=k, offset=off, budget=budget), patched_search(FakeSearch(hits)):
                        out = mcp_server.search_tool("q", k=k, offset=off, budget=budget)
                        self.assertFalse(out.startswith("Invalid"), out)
                        for m in re.findall(r"offset=(\d+)", out.splitlines()[-1]):
                            self.assertTrue(1 <= int(m) <= mcp_server.RANK_POOL, out.splitlines()[-1])
                            again = mcp_server.search_tool("q", k=k, offset=int(m), budget=budget)
                            self.assertFalse(again.startswith("Invalid"), again)

    def test_the_rank_limit_is_reported_not_advertised(self):
        with patched_search(FakeSearch(make_hits(300, text_len=3))):
            for off, k in ((200, 50), (151, 50), (200, 1), (250, 5)):
                out = mcp_server.search_tool("q", k=k, offset=off)
                self.assertEqual(out.splitlines()[-1],
                                 "Offset %d: rank limit 200 reached; no ranks past it can be returned." % off)
            self.assertEqual(shown_ranks(mcp_server.search_tool("q", k=50, offset=151)), list(range(151, 201)))
            out = mcp_server.search_tool("q", k=1, offset=199)
            self.assertEqual(out.splitlines()[-1], "Offset 199: another page exists, call search with offset=200.")
        with patched_search(FakeSearch(make_hits(10, text_len=3))):   # fewer hits than the pool: plain end
            self.assertEqual(mcp_server.search_tool("q", k=5, offset=8).splitlines()[-1], "Offset 8: no further page.")


class TestStableDepth(FixedConfig):
    def test_continuation_does_not_repeat_or_skip_when_the_order_depends_on_depth(self):
        # Hit 120 jumps to rank 1 once more than 60 hits are asked for, as fused retrieval arms can
        # do. A fetch depth that followed the offset would change the order between two calls.
        hits = [hit(i + 1, text="doc%03d" % (i + 1)) for i in range(300)]
        fake = DepthSensitiveSearch(hits, promoted=119, deeper_than=60)
        seen, offset, calls = [], 1, 0
        with patched_search(fake):
            while offset and calls < 100:
                out = mcp_server.search_tool("q", k=8, offset=offset)
                seen += re.findall(r"^(doc[0-9]{3})$", out, re.M)
                found = re.search(r"call search with offset=([0-9]+)", out.splitlines()[-1])
                offset = int(found.group(1)) if found else 0
                calls += 1
        deep = ["doc120"] + ["doc%03d" % i for i in range(1, 201) if i != 120]
        self.assertEqual(seen, deep[:200])   # the one order a deep fetch gives, each hit once
        self.assertEqual({c["k"] for c in fake.calls}, {200})
        self.assertIn("rank limit 200 reached", out.splitlines()[-1])

    def test_budget_continuation_with_a_depth_sensitive_order(self):
        hits = [hit(i + 1, text="doc%03d" % (i + 1)) for i in range(300)]
        fake = DepthSensitiveSearch(hits, promoted=119, deeper_than=60)
        seen, offset, calls = [], 1, 0
        with patched_search(fake):
            while offset and calls < 100:
                out = mcp_server.search_tool("q", k=20, budget=200, offset=offset)
                seen += re.findall(r"^#([0-9]+) score=", out, re.M)
                found = re.search(r"call search with offset=([0-9]+)", out.splitlines()[-1])
                offset = int(found.group(1)) if found else 0
                calls += 1
        self.assertEqual(seen, [str(i) for i in range(1, 201)])
        self.assertEqual({c["k"] for c in fake.calls}, {200})


class TestFitterEdges(unittest.TestCase):
    def test_a_short_hit_that_fits_whole_is_kept_when_its_marked_form_is_longer(self):
        # Budget 2 tokens, one byte for print's newline: 7 characters. "a#1" fits; the marked form
        # " [...]#1" would not, and the second hit cannot fit at all.
        hits = [{"rank": 1, "text": "a"}, {"rank": 2, "text": "x" * 500}]

        def render(shown, dropped):
            return "|".join(h["text"] for h in shown) + "#%d" % len(dropped)

        shown, dropped = search.fit_budget(hits, 2, render, extra=1)
        self.assertEqual(shown, [hits[0]])
        self.assertEqual(dropped, [hits[1]])

    def test_cli_keeps_a_complete_first_hit_that_fits_exactly(self):
        # Budget 50 is 200 characters. For each path length the output is predicted from the literal
        # header, so the case where the whole hit just fits (and its marked form does not) is covered.
        exact = 0
        for n in range(40, 130):
            path = "p" * n
            header = "#1 score=0.5000 T1 locked %s L1-3@file example | Review sha=abababababab" % path
            whole = header + "\nb\n" + "dropped: 1 (ranks 2-2)" + "\n"
            hits = [hit(1, text="b", path=path), hit(2, text="c", path=OVERSIZED)]
            code, out = run_cli(hits, "--budget", "50")
            if len(whole) <= 200:
                self.assertEqual(out, whole, n)
                exact += len(whole) == 200
            else:
                self.assertLessEqual(len(out), 200)
        self.assertEqual(exact, 1)   # one path length lands on exactly 200 characters


class TestErrorLines(FixedConfig):
    def test_an_error_line_stays_within_the_budget(self):
        for exc in (RuntimeError("x" * 300), psycopg2.OperationalError("y " * 200),
                    httpx.ConnectError("z" * 300)):
            for budget in (50, 200):
                with self.subTest(exc=type(exc).__name__, budget=budget), \
                        patched_search(FakeSearch([], error=exc)):
                    out = mcp_server.search_tool("q", budget=budget)
                self.assertLessEqual(len(out), budget * 4)
                self.assertNotIn("\n", out)
                self.assertTrue(out.startswith(("cerebrollm failed: RuntimeError", "Postgres is not reachable",
                                                "Ollama is not reachable")), out)

    def test_the_start_command_survives_the_cut_when_it_can(self):
        with patched_search(FakeSearch([], error=httpx.ConnectError("z" * 300))):
            out = mcp_server.search_tool("q", budget=50)
        self.assertTrue(out.endswith("Start it with: ollama serve"), out)

    def test_without_budget_the_error_line_is_as_before(self):
        with patched_search(FakeSearch([], error=RuntimeError("x" * 400))):
            out = mcp_server.search_tool("q")
        self.assertEqual(out, "cerebrollm failed: RuntimeError: " + "x" * 300)


class TestRerankContinuation(FixedConfig):
    def test_continuation_resumes_in_the_same_reranked_order(self):
        hits = [hit(i + 1, text="doc%03d" % (i + 1)) for i in range(80)]

        def scorer(query, texts):   # the higher the number, the better: later search hits move to the front
            return [float(t[3:]) for t in texts]

        fake = FakeSearch(hits)
        seen, offset, calls = [], 1, 0
        with patched_search(fake), mock.patch("cerebrollm.rerank.score", scorer):
            while offset and calls < 30:
                out = mcp_server.search_tool("q", k=20, rerank=True, budget=200, offset=offset)
                self.assertLessEqual(len(out), 800)
                for rank, text in re.findall(r"^#(\d+) score=[^\n]*\n([^\n]*)$", out, re.M):
                    expected = "doc%03d" % (51 - int(rank))   # the pool is search hits 1-50, best score first
                    self.assertTrue(expected.startswith(text.replace("[...]", "").strip()), (rank, text))
                seen += shown_ranks(out)
                m = re.search(r"call search with offset=(\d+)", out.splitlines()[-1])
                offset = int(m.group(1)) if m else 0
                calls += 1
        self.assertEqual(seen, list(range(1, 51)))   # every pool position once, in order
        self.assertEqual({c["k"] for c in fake.calls}, {50})   # one fixed pool on every call
        self.assertIn("rank limit 50 reached", out.splitlines()[-1])


class TestFitBudgetCost(unittest.TestCase):
    def test_renders_grow_with_the_logarithm_of_the_hits(self):
        for name, hits in (("oversized first header", make_hits(1000, path=OVERSIZED)),
                           ("normal", make_hits(1000))):
            calls = []

            def render(shown, dropped):
                calls.append(1)
                return search.format_hits(shown) + "dropped: %d" % len(dropped)

            with self.subTest(name):
                shown, dropped = search.fit_budget(hits, 50 if name.startswith("over") else 2000, render)
                self.assertEqual(len(shown) + len(dropped), 1000)
                self.assertLessEqual(len(calls), 60)   # 1000 hits: not 500,000 hit renderings

    def test_one_thousand_hits_with_an_oversized_first_header(self):
        code, out = run_cli(make_hits(1000, path=OVERSIZED), "--budget", "50")
        self.assertEqual(out, "dropped: 1000 (ranks 1-1000)\n")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def golden_outputs():
    """Outputs of the default paths on fixed fixtures; the GOLDEN values come from origin/main."""
    short = [hit(1, text="first body"), hit(2, text="second body", also_at=["root:copy.md"])]
    long_hits = make_hits(8, text_len=10000)
    out = {}
    out["cli_text_short"] = run_cli(short)[1]
    out["cli_json_short"] = run_cli(short, "--json")[1]
    out["cli_text_capped"] = run_cli(long_hits)[1]
    out["cli_json_capped"] = run_cli(long_hits, "--json")[1]
    with patched_search(FakeSearch(make_hits(5, text_len=60))):
        out["mcp_page1"] = mcp_server.search_tool("q", k=2)
        out["mcp_page2"] = mcp_server.search_tool("q", k=2, page=2)
        out["mcp_last"] = mcp_server.search_tool("q", k=2, page=3)
        out["mcp_past_end"] = mcp_server.search_tool("q", k=2, page=4)
    with patched_search(FakeSearch(long_hits)):
        out["mcp_capped"] = mcp_server.search_tool("q", k=8)
    long_headers = make_hits(16, text_len=10000, path="root/%s/doc.md" % ("segment-" * 25),
                             heading_path=" > ".join("Heading %d" % j for j in range(20)))
    with patched_search(FakeSearch(long_headers)):
        out["mcp_long_headers_p2"] = mcp_server.search_tool("q", k=8, page=2)
    return out


GOLDEN = {   # name: (length, sha256), from the code of origin/main
    "cli_text_short": (220, "9644895eaf9a930297cf784e8a6c6e9d55906bdf35fc3c965f0957dfbeebfc7f"),
    "cli_json_short": (886, "437b2bab59076bfda404bee0d3b6cac4c4f9e325e09340a6a61a88618b1b4dd2"),
    "cli_text_capped": (8008, "1f0231c0bd0c34bb85e7077026116fba0ef32caaaf87e8fe9c2f4699b74ce2e6"),
    "cli_json_capped": (10835, "5cdc4dc56d2d2825954b4e72af1cc6e5ab6be3567bf02e23fd96122d0dd58665"),
    "mcp_page1": (556, "625f3113c341c374aa96f58de67717cfd6ea8c737da59e8a6acaedf0663b7150"),
    "mcp_page2": (556, "6e6640aaa8f55dfa4af095da1780be4be1b9ea3a3ab12a20ecb691c8cdd7d71d"),
    "mcp_last": (329, "ff9181c0d192f61e01e24c044230ee2138203e0272ef798f9e18d8707304158a"),
    "mcp_past_end": (150, "431a72c8eb91b928fd5bd41699be0bbe92fec73b98737971f7a6672fde60af24"),
    "mcp_capped": (7955, "10fde5896a5467474ca411999bd6aa0de25674d0dd277a40889590c116f5032f"),
    "mcp_long_headers_p2": (7962, "8ce95f90267d267a67f4b7d8ac4dd12347818761e316e30589eb29d09dd9e847"),
}


class TestDefaultOutputUnchanged(FixedConfig):
    def test_outputs_without_budget_or_offset_match_origin_main(self):
        got = golden_outputs()
        self.assertEqual(set(got), set(GOLDEN))
        for name, text in got.items():
            with self.subTest(name):
                self.assertEqual((len(text), digest(text)), GOLDEN[name])

    def test_the_short_cli_text_is_exactly_what_format_hits_printed_before(self):
        short = [hit(1, text="first body"), hit(2, text="second body", also_at=["root:copy.md"])]
        self.assertEqual(run_cli(short)[1],
                         "#1 score=0.5000 T1 locked alpha/review.md L1-3@file example | Review sha=abababababab\n"
                         "first body\n\n"
                         "#2 score=0.5000 T1 locked alpha/review.md L1-3@file example | Review sha=abababababab "
                         "also_at=[root:copy.md]\n"
                         "second body\n\n")
