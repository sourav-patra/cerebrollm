"""Tests for eval/check_items_v2.py and the v2 item set. Run: python3 -m unittest eval/test_check_items_v2.py -v
(stdlib only). Group 1 tests use the private items.json when it exists and a synthetic notes folder otherwise.
"""
import builtins
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings
from unittest import mock

for _name in ("CEREBROLLM_ITEMSET", "CEREBROLLM_V2_OUT", "CEREBROLLM_V2_JUDGE"):   # a caller's setting must not steer the tests
    os.environ.pop(_name, None)
warnings.simplefilter("ignore", ResourceWarning)  # the tests open small files without closing them
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_items as V1  # noqa: E402
import check_items_v2 as V2  # noqa: E402
import grade_lib as G  # noqa: E402
import itemset as IS  # noqa: E402
import itemset_config as IC  # noqa: E402
import verify_v2_sources as VS  # noqa: E402


def _corpus():
    try:
        p = V2.corpus_from_study()
    except (OSError, ValueError):
        return None
    return p if os.path.isdir(p) else None


CORPUS = _corpus()
PRIVATE = os.path.expanduser("~/.cerebrollm/private-eval/items.json")


def setUpModule():
    warnings.simplefilter("ignore", ResourceWarning)  # unittest resets the filters before it runs the tests


def gold(it):
    text = " ".join(q["text"] for q in it["quotes"])
    if it["kind"] == "stale":
        text += " " + it["stale"]["current"]["text"]
    return text


def grade_checks(case, items):
    for it in items:
        if it["kind"] == "unanswerable":
            continue
        case.assertTrue(G.grade(it, gold(it))[0], "gold answer fails for " + it["id"])
        case.assertFalse(G.grade(it, "")[0], "empty answer passes for " + it["id"])
        if it["kind"] == "stale":
            case.assertFalse(G.grade(it, it["stale"]["superseded"]["fact"])[0], "superseded-only passes for " + it["id"])


def v1_items():
    return [json.loads(l) for l in open(V1.ITEMS, encoding="utf-8") if l.strip()]


def v3_items():
    return [json.loads(l) for l in open(IS.load("v3").items, encoding="utf-8") if l.strip()]


def public_rows():
    return [json.loads(l) for l in open(IS.load("v2").items, encoding="utf-8") if l.strip()]


def write_rows(path, rows):
    open(path, "w", encoding="utf-8").write("\n".join(json.dumps(r) for r in rows) + "\n")


class PublicSet(unittest.TestCase):
    def test_public_set_passes_the_checker(self):
        fails, items = V2.check_public(corpus=CORPUS)
        self.assertEqual(fails, [])
        self.assertEqual(len(items), 35)

    def test_gold_and_superseded_answers_grade_as_expected(self):
        _, items = V2.check_public(corpus=None)
        grade_checks(self, items)

    def test_questions_are_not_in_the_frozen_set(self):
        _, items = V2.check_public(corpus=None)
        self.assertFalse({i["question"] for i in v1_items()} & {i["question"] for i in items})

    def test_frozen_set_is_intact(self):
        self.assertEqual(len(v1_items()), 70)

    def test_wrong_line_is_caught(self):
        with tempfile.TemporaryDirectory() as t:
            rows = public_rows()
            rows[0]["quotes"][0]["line"] += 1
            p = os.path.join(t, "items.jsonl")
            write_rows(p, rows)
            fails, _ = V2.check_public(path=p, corpus=None)
            self.assertTrue(any("G2-EX-01" in f and "does not contain" in f for f in fails), fails)

    def test_escaping_source_path_is_caught(self):
        with tempfile.TemporaryDirectory() as t:
            rows = public_rows()
            rows[0]["quotes"][0]["path"] = "ollama/../../outside.md"
            p = os.path.join(t, "items.jsonl")
            write_rows(p, rows)
            fails, _ = V2.check_public(path=p, corpus=None)
            self.assertTrue(any("escapes the root" in f for f in fails), fails)

    def test_pre_cutoff_source_is_caught(self):
        with tempfile.TemporaryDirectory() as t:
            src = os.path.join(t, "v2-sources")
            shutil.copytree(V2.SOURCES, src)
            f = os.path.join(src, "ollama", "v0.35.1.md")
            s = open(f, encoding="utf-8").read().replace("Published: 2026-09-29", "Published: 2026-05-01")
            open(f, "w", encoding="utf-8", newline="\n").write(s)
            fails, _ = V2.check_public(sources=src, corpus=None)
            self.assertTrue(any("before 2026-07-01" in x for x in fails), fails)

    def test_wrong_count_is_caught(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "items.jsonl")
            write_rows(p, public_rows()[:-1])
            fails, _ = V2.check_public(path=p, corpus=None)
            self.assertTrue(any("expected 15 group 3" in f for f in fails), fails)


class AbsentTerms(unittest.TestCase):
    def setUp(self):
        V2._BLOBS.clear()  # the checker caches file contents per root; each test plants its own folder

    def planted(self, term, **kw):
        with tempfile.TemporaryDirectory() as t:
            rows = public_rows()
            g3 = next(r for r in rows if r["id"] == "G3-UN-01")
            g3["absent_terms"] = [term]
            p = os.path.join(t, "items.jsonl")
            write_rows(p, rows)
            return V2.check_public(path=p, **kw)[0]

    def test_term_in_saved_sources_is_caught_without_a_corpus(self):
        # this repository's own eval/ folder sits under a folder named cerebrollm; the saved sources must still be scanned
        fails = self.planted("Muse Glimmer", corpus=None)
        self.assertTrue(any("G3-UN-01" in f and "occurs in" in f and "v2-sources" in f for f in fails), fails)

    def test_term_in_corpus_is_caught(self):
        with tempfile.TemporaryDirectory() as c:
            os.makedirs(os.path.join(c, "ollama"))
            open(os.path.join(c, "ollama", "x.md"), "w").write("set PLANTED_TERM_X=5m")
            fails = self.planted("planted_term_x", corpus=c)
            self.assertTrue(any("G3-UN-01" in f and "occurs in" in f for f in fails), fails)

    def test_corpus_cerebrollm_eval_folder_is_skipped_but_not_other_folders(self):
        with tempfile.TemporaryDirectory() as c:
            os.makedirs(os.path.join(c, "cerebrollm", "eval"))
            open(os.path.join(c, "cerebrollm", "eval", "q.md"), "w").write("planted_term_y")
            self.assertEqual([f for f in self.planted("planted_term_y", corpus=c) if "G3-UN-01" in f], [])
            V2._BLOBS.clear()
            open(os.path.join(c, "cerebrollm", "other.md"), "w").write("planted_term_y")
            self.assertTrue(any("G3-UN-01" in f for f in self.planted("planted_term_y", corpus=c)))

    def test_missing_corpus_is_caught(self):
        fails, _ = V2.check_public(corpus="/nonexistent-corpus")
        self.assertTrue(any("corpus root not found" in f for f in fails), fails)


class CorpusPath(unittest.TestCase):
    def test_study_toml_path_is_expanded(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "study.toml")
            open(p, "w").write('[corpus]\npath = "$HOME/c"\n')
            with mock.patch.dict(os.environ, {"HOME": "/h"}):
                self.assertEqual(V2.corpus_from_study(p), "/h/c")

    def test_missing_key_is_named(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "study.toml")
            open(p, "w").write("[engine]\npath = 'x'\n")
            with self.assertRaises(ValueError):
                V2.corpus_from_study(p)

    def test_no_hard_coded_path_in_the_checker(self):
        text = open(os.path.join(HERE, "check_items_v2.py"), encoding="utf-8").read()
        self.assertNotIn("DEFAULT_ROOT", text)
        for prefix in ("/ho" + "me/", "/m" + "nt/"):
            self.assertNotIn(prefix, text)


class PrivateSet(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.t)
        self.root = os.path.join(self.t, "notes")
        os.makedirs(os.path.join(self.root, "proj"))
        self.note = os.path.join(self.root, "proj", "a.md")
        open(self.note, "w", encoding="utf-8", newline="\n").write("one\nthe limit is 42 widgets\nthree\n")
        self.sha = hashlib.sha256(open(self.note, "rb").read()).hexdigest()
        # files a check must never open
        self.forbidden = []
        for name in ("excluded-dir", "demo-wt-1", "scratch-x"):
            os.makedirs(os.path.join(self.root, name))
            f = os.path.join(self.root, name, "a.md")
            shutil.copy(self.note, f)
            self.forbidden.append(os.path.realpath(os.path.dirname(f)))
        self.outside = os.path.join(self.t, "outside.md")
        shutil.copy(self.note, self.outside)
        self.forbidden.append(os.path.realpath(self.outside))
        self.item = {"id": "G1-EX-01", "set": "scored", "group": 1, "kind": "exact", "source": "proj",
                     "question": "q", "key_facts": ["42"],
                     "quotes": [{"path": "proj/a.md", "line": 2, "text": "limit is 42"}],
                     "pick": {"notes": [{"path": "proj/a.md", "sha256": self.sha, "line_start": 2, "line_end": 2}], "why": "w"}}

    def run_check(self, item):
        """(failures, paths opened during the check)"""
        p = os.path.join(self.t, "items.json")
        json.dump([item], open(p, "w"))
        real, opened = builtins.open, []

        def spy(file, *a, **k):
            if isinstance(file, (str, bytes, os.PathLike)):
                opened.append(os.path.realpath(file))
            return real(file, *a, **k)
        with mock.patch("builtins.open", spy):
            fails = V2.check_private(p, self.root, never=("excluded-dir",), skip=("*-wt-*", "scratch-*"))[0]
        return fails, opened

    def assert_nothing_forbidden_opened(self, opened):
        for o in opened:
            for f in self.forbidden:
                self.assertFalse(o == f or o.startswith(f + os.sep), "opened a forbidden path: " + o)

    def variant(self, path, where="quote"):
        item = json.loads(json.dumps(self.item))
        item["source"] = path.split("/")[0]
        if where == "quote":
            item["quotes"][0]["path"] = path
        item["pick"]["notes"][0]["path"] = path if where == "quote" else "proj/a.md"
        if where == "uncited":
            item["pick"]["notes"].append({"path": path, "sha256": self.sha, "line_start": 1, "line_end": 3})
            item["source"] = "proj"
        return item

    def test_good_item_passes(self):
        fails, opened = self.run_check(self.item)
        self.assertEqual(fails, [])
        self.assertIn(os.path.realpath(self.note), opened)

    def test_changed_note_is_caught(self):
        open(self.note, "a").write("more\n")
        self.assertTrue(any("changed since it was picked" in f for f in self.run_check(self.item)[0]))

    def test_wrong_quote_is_caught(self):
        self.item["quotes"][0]["text"] = "limit is 43"
        self.assertTrue(any("does not contain" in f for f in self.run_check(self.item)[0]))

    def test_line_outside_recorded_range_is_caught(self):
        self.item["pick"]["notes"][0]["line_end"] = 1
        self.assertTrue(any("outside the recorded range" in f for f in self.run_check(self.item)[0]))

    def test_excluded_and_escaping_paths_are_rejected_before_any_read(self):
        cases = ["excluded-dir/a.md", "./excluded-dir/a.md", "proj/../excluded-dir/a.md", "EXCLUDED-DIR/a.md",
                 "demo-wt-1/a.md", "./demo-wt-1/a.md", "scratch-x/a.md", "proj/../scratch-x/a.md",
                 "../outside.md", "proj/../../outside.md", self.outside]
        for path in cases:
            for where in ("quote", "uncited"):
                with self.subTest(path=path, where=where):
                    fails, opened = self.run_check(self.variant(path, where))
                    self.assertTrue(any("excluded folder" in f or "escapes the root" in f or "not a relative" in f
                                        for f in fails), fails)
                    self.assert_nothing_forbidden_opened(opened)

    def test_stale_block_paths_are_rejected_before_any_read(self):
        item = json.loads(json.dumps(self.item))
        item["kind"] = "stale"
        q = {"path": "proj/a.md", "line": 2, "text": "limit is 42", "fact": "f"}
        item["stale"] = {"superseded": dict(q, path="./excluded-dir/a.md"), "current": q, "markers": ["m"], "basis": "b"}
        fails, opened = self.run_check(item)
        self.assertTrue(any("excluded folder" in f for f in fails), fails)
        self.assert_nothing_forbidden_opened(opened)

    def test_link_into_an_excluded_folder_is_rejected_before_any_read(self):
        try:
            os.symlink(os.path.join(self.root, "excluded-dir"), os.path.join(self.root, "proj", "link"))
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not available")
        fails, opened = self.run_check(self.variant("proj/link/a.md"))
        self.assertTrue(any("excluded folder" in f for f in fails), fails)
        self.assert_nothing_forbidden_opened(opened)

    def test_public_id_collision_is_caught(self):
        p = os.path.join(self.t, "items.json")
        json.dump([self.item], open(p, "w"))
        self.assertTrue(any("duplicate id" in f for f in V2.check_private(p, self.root, {"G1-EX-01"})[0]))

    def test_sources_file_is_parsed(self):
        p = os.path.join(self.t, "SOURCES.txt")
        open(p, "w").write("\n".join(["# c", "projects_folder: /x/", "never_open: excluded-dir, other", "skip: *-wt-*, scratch-*", ""]))
        self.assertEqual(V2.read_sources(p), {"projects_folder": "/x/", "never_open": ["excluded-dir", "other"], "skip": ["*-wt-*", "scratch-*"]})

    @unittest.skipUnless(os.path.isfile(PRIVATE) and os.path.isfile(os.path.join(os.path.dirname(PRIVATE), "SOURCES.txt")),
                         "private set or SOURCES.txt not present")
    def test_real_private_set(self):
        src = V2.read_sources(os.path.join(os.path.dirname(PRIVATE), "SOURCES.txt"))
        if not os.path.isdir(src["projects_folder"]):
            self.skipTest("projects folder not present")
        fails, items = V2.check_private(PRIVATE, src["projects_folder"], never=src["never_open"], skip=src["skip"])
        self.assertEqual(fails, [])
        grade_checks(self, items)


class ItemSets(unittest.TestCase):
    def test_v2_settings_are_the_counts_the_checker_once_hard_coded(self):
        s = IS.load("v2")
        self.assertEqual(s.want, {(2, "exact"): 10, (2, "paraphrase"): 7, (2, "stale"): 3, (3, "unanswerable"): 15})
        self.assertEqual((s.cutoff, s.judge, s.target_pct), ("2026-07-01", "gpt-oss:20b", None))
        self.assertEqual((s.total, s.n_answerable, s.n_unanswerable), (35, 20, 15))

    def test_unknown_set_is_refused(self):
        for name in ("nope", "../items-v2"):
            with self.assertRaises(SystemExit):
                IS.load(name)

    def test_v3_passes_the_checker(self):
        s = IS.load("v3")
        fails, items = V2.check_public(corpus=CORPUS, itemset=s)
        self.assertEqual(fails, [])
        self.assertEqual(len(items), s.total)

    def test_v3_is_large_enough_for_a_printed_bound_under_two_percent(self):
        s = IS.load("v3")
        self.assertGreaterEqual(s.total, 154)
        self.assertLess(round(300 / s.total, 1), 2.0)
        self.assertEqual(len({i["id"] for i in v3_items()}), s.total)

    def test_v3_proportions_are_close_to_v2(self):
        s2, s3 = IS.load("v2"), IS.load("v3")
        for kind in ("exact", "paraphrase", "stale", "unanswerable"):
            self.assertAlmostEqual(s3.kind_count(kind) / s3.total, s2.kind_count(kind) / s2.total, delta=0.05, msg=kind)

    def test_v3_gold_and_superseded_answers_grade_as_expected(self):
        grade_checks(self, v3_items())

    def _v3_item(self, item_id):
        return next(i for i in v3_items() if i["id"] == item_id)

    def _accepts(self, item_id, answer):
        return G.key_facts_ok(self._v3_item(item_id), G.tokens(answer))[0]

    def test_v3_st_08_key_fact_needs_the_exact_build(self):
        for answer in ("build 25.5.5", "It updates to build 25.5.5."):
            self.assertTrue(self._accepts("V3-ST-08", answer), answer)
        for answer in ("build 25.5.4", "25.5", "build 25.4.4"):
            self.assertFalse(self._accepts("V3-ST-08", answer), answer)

    def test_v3_st_14_key_fact_needs_the_exact_jiter_version(self):
        for answer in ("jiter v0.19.0", "jiter 0.19.0", "v 0.19.0"):
            self.assertTrue(self._accepts("V3-ST-14", answer), answer)
        for answer in ("0.19.1", "0.18.0", "19.0"):
            self.assertFalse(self._accepts("V3-ST-14", answer), answer)

    def test_v3_questions_are_not_in_the_v2_set(self):
        self.assertFalse({i["question"] for i in public_rows()} & {i["question"] for i in v3_items()})

    def test_v3_stale_items_cite_two_different_releases(self):
        stale = [i for i in v3_items() if i["kind"] == "stale"]
        self.assertEqual(len(stale), IS.load("v3").kind_count("stale"))
        for it in stale:
            self.assertNotEqual(it["stale"]["superseded"]["path"], it["stale"]["current"]["path"], it["id"])

    def test_v3_wrong_count_is_caught(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "items.jsonl")
            write_rows(p, v3_items()[1:])
            fails, _ = V2.check_public(path=p, corpus=None, itemset=IS.load("v3"))
            self.assertTrue(any("expected 50 group 2 exact items, found 49" in f for f in fails), fails)

    def test_duplicate_question_is_caught(self):
        with tempfile.TemporaryDirectory() as t:
            rows = v3_items()
            rows[1]["question"] = rows[0]["question"].upper()
            p = os.path.join(t, "items.jsonl")
            write_rows(p, rows)
            fails, _ = V2.check_public(path=p, corpus=None, itemset=IS.load("v3"))
            self.assertTrue(any(f.startswith("duplicate question") for f in fails), fails)

    def test_v3_pre_cutoff_source_is_caught(self):
        s = IS.load("v3")
        with tempfile.TemporaryDirectory() as t:
            src = os.path.join(t, "v3-sources")
            shutil.copytree(s.sources, src)
            f = os.path.join(src, "uv", "0.13.6.md")
            text = open(f, encoding="utf-8").read().replace("Published: 2026-10-27", "Published: 2026-05-01")
            open(f, "w", encoding="utf-8", newline="\n").write(text)
            fails, _ = V2.check_public(sources=src, corpus=None, itemset=s)
            self.assertTrue(any("before 2026-07-01" in x for x in fails), fails)

    def test_config_for_v3_has_its_own_corpus_table_and_state_and_one_rule_per_source_folder(self):
        import tomllib
        with open(IC.ENGINE_CONFIG, encoding="utf-8") as f:   # universal newlines, as itemset_config reads it
            base = f.read()
        shipped, text = tomllib.loads(base), IC.config_text(IS.load("v3"))
        cfg = tomllib.loads(text)
        self.assertEqual((cfg["state_dir"], cfg["postgres"]["table"], [r["path"] for r in cfg["root"]]),
                         ("$HOME/.cerebrollm/v3", "chunks_v3", ["$HOME/cerebrollm-corpus-v3"]))
        self.assertNotEqual((shipped["state_dir"], shipped["postgres"]["table"], shipped["root"][0]["path"]),
                            (cfg["state_dir"], cfg["postgres"]["table"], cfg["root"][0]["path"]))   # the shipped ones are not reused
        added = cfg["rule"][len(shipped["rule"]):]
        self.assertEqual([(r["root"], r["glob"], r["tier"], r["status"]) for r in added],
                         [("notes", d + "/**/*.md", "T3", "current") for d in ("pydantic", "ruff", "uv")])
        for key in ("ollama", "chunking", "search", "never"):   # everything else is the shipped file's
            self.assertEqual(cfg[key], shipped[key], key)
        self.assertEqual(cfg["postgres"]["embed_dim"], shipped["postgres"]["embed_dim"])

    def test_config_refuses_a_shipped_file_that_no_longer_has_the_lines_it_replaces(self):
        with self.assertRaisesRegex(ValueError, "no longer has exactly one line"):
            IC.config_text(IS.load("v3"), base='domain = "x"\n')

    def test_v3_sources_are_the_folders_the_items_point_into(self):
        used = {q["path"].split("/")[0] for it in v3_items() for q in it["quotes"]}
        self.assertEqual(used, set(IC.folders(IS.load("v3"))))


class SourceTools(unittest.TestCase):
    def itemset(self):
        return IS.load("v3")

    def test_config_is_not_written_over_an_existing_file_without_force(self):
        with tempfile.TemporaryDirectory() as t:
            out = os.path.join(t, "c.toml")
            open(out, "w").write("keep me")
            with self.assertRaisesRegex(FileExistsError, "pass --force"):
                IC.write_config(self.itemset(), out, roots=[t])
            self.assertEqual(open(out).read(), "keep me")
            IC.write_config(self.itemset(), out, force=True, roots=[t])
            self.assertIn('glob = "uv/**/*.md"', open(out).read())
            self.assertEqual(os.listdir(t), ["c.toml"])   # no temporary file is left behind

    def test_config_that_appears_between_the_check_and_the_install_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as t:
            out = os.path.join(t, "c.toml")
            real = IC.tempfile.mkstemp

            def other_writer_wins(*a, **k):   # the destination is created after the checks, before the install
                open(out, "w").write("the other writer")
                return real(*a, **k)
            with mock.patch.object(IC.tempfile, "mkstemp", other_writer_wins):
                with self.assertRaises(FileExistsError):
                    IC.write_config(self.itemset(), out, roots=[t])
            self.assertEqual(open(out).read(), "the other writer")
            self.assertEqual(os.listdir(t), ["c.toml"])

    def test_config_refuses_a_source_folder_name_it_cannot_write_as_it_is(self):
        with tempfile.TemporaryDirectory() as t:
            out = os.path.join(t, "c.toml")
            for name in ('x"y', "x y", "x*", "-x"):
                with mock.patch.object(IC.os, "listdir", return_value=["uv", name]), \
                        mock.patch.object(IC.os.path, "isdir", return_value=True):
                    with self.assertRaisesRegex(ValueError, "source folder names may hold only"):
                        IC.write_config(self.itemset(), out, roots=[t])
            self.assertEqual(os.listdir(t), [])
        with mock.patch.object(IC.os, "listdir", return_value=["uv", "ruff-2.x_y"]), \
                mock.patch.object(IC.os.path, "isdir", return_value=True):
            self.assertEqual(IC.folders(self.itemset()), ["ruff-2.x_y", "uv"])

    def test_config_that_does_not_parse_is_not_installed(self):
        with tempfile.TemporaryDirectory() as t:
            out = os.path.join(t, "c.toml")
            with mock.patch.object(IC, "config_text", return_value='glob = "a"b/**/*.md"\n'):
                with self.assertRaisesRegex(ValueError, "not valid TOML"):
                    IC.write_config(self.itemset(), out, roots=[t])
            self.assertEqual(os.listdir(t), [])
            IC.write_config(self.itemset(), out, roots=[t])   # the shipped config with the v3 rules parses
            self.assertIn('glob = "uv/**/*.md"', open(out).read())

    def test_config_failure_leaves_the_destination_and_no_temporary_file(self):
        with tempfile.TemporaryDirectory() as t:
            out = os.path.join(t, "c.toml")
            open(out, "w").write("keep me")
            with mock.patch.object(IC, "config_text", side_effect=OSError("engine config unreadable")):
                with self.assertRaises(OSError):
                    IC.write_config(self.itemset(), out, force=True, roots=[t])
            self.assertEqual(open(out).read(), "keep me")
            self.assertEqual(os.listdir(t), ["c.toml"])

    def test_config_is_written_only_under_the_repository_or_the_cerebrollm_home(self):
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as elsewhere:
            with self.assertRaisesRegex(ValueError, "outside the permitted folders"):
                IC.write_config(self.itemset(), os.path.join(elsewhere, "c.toml"), roots=[t])
            with self.assertRaisesRegex(ValueError, "outside the permitted folders"):
                IC.write_config(self.itemset(), os.path.join(t, "..", os.path.basename(elsewhere), "c.toml"), roots=[t])
            self.assertEqual(os.listdir(elsewhere), [])
            outside = not any(os.path.realpath(elsewhere).startswith(r + os.sep) for r in IC.default_roots())
            if outside:   # a temporary folder inside the repository or ~/.cerebrollm is a permitted destination
                self.assertEqual(IC.main(["v3", os.path.join(elsewhere, "c.toml")]), 1)   # the command line uses the real roots
                self.assertEqual(os.listdir(elsewhere), [])
            self.assertEqual([os.path.realpath(os.path.join(HERE, "..")), os.path.realpath(os.path.expanduser("~/.cerebrollm"))],
                             IC.default_roots())
            link = os.path.join(t, "link")
            try:
                os.symlink(elsewhere, link)
            except (OSError, NotImplementedError):
                return
            with self.assertRaisesRegex(ValueError, "outside the permitted folders"):   # a link out of the root is followed
                IC.write_config(self.itemset(), os.path.join(link, "c.toml"), roots=[os.path.realpath(t)])

    def test_verifier_fails_on_a_missing_or_empty_folder(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(SystemExit, "not found"):
                VS.check_folder(os.path.join(t, "none"))
            with self.assertRaisesRegex(SystemExit, "no file under"):
                VS.check_folder(t)

    def test_verifier_counts_a_file_without_a_release_url_as_a_difference(self):
        with tempfile.TemporaryDirectory() as t:
            open(os.path.join(t, "a.md"), "w").write("URL: https://example.com/x\nPublished: 2026-07-01\n\nbody\n")
            self.assertEqual(VS.check_folder(t, fetcher=lambda url: self.fail("no fetch for this file")), (1, 1))

    def test_verifier_compares_body_and_date_with_the_api_answer_for_both_line_endings(self):
        text = "URL: https://github.com/o/r/releases/tag/v1\nPublished: 2026-07-01\nFetched: x\nVia: y\n\nbody\nline two\n"
        for ending in ("\n", "\r\n"):
            with tempfile.TemporaryDirectory() as t:
                open(os.path.join(t, "a.md"), "w", newline="").write(text.replace("\n", ending))
                seen = []

                def fetcher(url):
                    seen.append(url)
                    return {"body": "body\r\nline two\r\n", "published_at": "2026-07-01T10:00:00Z"}
                self.assertEqual(VS.check_folder(t, fetcher=fetcher), (1, 0), repr(ending))
                self.assertEqual(seen, ["https://api.github.com/repos/o/r/releases/tags/v1"])
                self.assertEqual(VS.check_folder(t, fetcher=lambda u: {"body": "other", "published_at": "2026-07-01"}), (1, 1))

    def test_token_goes_only_to_https_api_github_and_is_dropped_on_every_redirect(self):
        req = VS.request_for("https://api.github.com/repos/o/r/releases/tags/v1", "SECRET")
        self.assertEqual(req.get_header("Authorization"), "Bearer SECRET")
        for url in ("https://example.com/x", "http://api.github.com/x"):
            self.assertIsNone(VS.request_for(url, "SECRET").get_header("Authorization"), url)
        self.assertIsNone(VS.request_for("https://api.github.com/x").get_header("Authorization"))
        handler = VS._KeepTokenAtTheApi()
        for target in ("https://objects.example.net/file", "http://api.github.com/other",   # another host; downgrade
                       "https://api.github.com/other"):                                      # the same origin
            new = handler.redirect_request(req, None, 302, "Found", {}, target)
            self.assertIsNotNone(new, target)
            self.assertIsNone(new.get_header("Authorization"), target)
            self.assertNotIn("Authorization", {k.capitalize() for k in new.unredirected_hdrs}, target)

    def test_set_flag_wins_over_a_bad_environment_value_in_the_checker(self):
        env = dict(os.environ, CEREBROLLM_ITEMSET="no-such-set")
        here = os.path.dirname(os.path.abspath(__file__))
        run = lambda *a: subprocess.run([sys.executable, os.path.join(here, "check_items_v2.py"), *a],  # noqa: E731
                                        capture_output=True, text=True, cwd=here, env=env)
        ok = run("--set", "v3", "--corpus", os.path.join(here, "no-such-corpus"))
        self.assertNotIn("unknown item set", ok.stdout + ok.stderr)   # it got as far as the corpus check
        self.assertIn("corpus root not found", ok.stdout)
        bad = run("--corpus", os.path.join(here, "no-such-corpus"))
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("unknown item set 'no-such-set'", bad.stderr)

    def test_an_environment_value_that_is_not_loadable_does_not_defeat_an_explicit_set(self):
        import tomllib
        real = IS.load
        calls = []

        def broken_then_real(name=None):
            calls.append(name)
            if len(calls) == 1:
                raise tomllib.TOMLDecodeError("bad toml")
            return real(name)
        with mock.patch.object(IS, "load", broken_then_real):
            settings, error = IS.load_early()
        self.assertEqual(settings.name, "v2")
        self.assertIsInstance(error, SystemExit)
        self.assertIn("bad toml", str(error))

    def test_the_v2_guide_names_its_set_so_a_stale_environment_does_not_change_its_command(self):
        text = open(os.path.join(HERE, "GRADING-v2.md"), encoding="utf-8").read()
        self.assertIn("python3 eval/check_items_v2.py --set v2 [--private", text)

    def test_notice_links_the_licence_evidence_of_the_three_new_projects(self):
        text = open(os.path.join(HERE, "..", "NOTICE"), encoding="utf-8").read()
        for link in ("https://github.com/astral-sh/ruff/blob/main/LICENSE", "https://github.com/astral-sh/uv/blob/main/LICENSE-MIT",
                     "https://github.com/astral-sh/uv/blob/main/LICENSE-APACHE", "https://github.com/pydantic/pydantic/blob/main/LICENSE"):
            self.assertIn(link, text)
        self.assertIn("for the four projects with a pinned commit", text)

    def test_runbook_paragraphs_are_short_and_it_never_writes_into_the_indexed_corpus(self):
        text = open(os.path.join(HERE, "ITEMS-v3.md"), encoding="utf-8").read()
        import re
        paragraphs, cur, fenced = [], [], False
        for line in text.splitlines():   # a paragraph ends at a blank line, a list item, a heading or a table row
            if line.strip().startswith("```"):
                fenced = not fenced
                continue
            starts = re.match(r"\s*(\d+\.|-)\s", line) or line.startswith(("#", "|"))
            if fenced or not line.strip() or starts:
                paragraphs.append(" ".join(cur))
                cur = [] if (fenced or not line.strip() or line.startswith(("#", "|"))) else [line]
            else:
                cur.append(line)
        paragraphs.append(" ".join(cur))
        for para in paragraphs:
            self.assertLessEqual(len(para.split()), 60, para[:60])
        self.assertIn("mkdir ~/cerebrollm-corpus-v3 &&\n", text)   # copies nothing into a folder that exists
        self.assertIn("diff -r eval/v3-sources ~/cerebrollm-corpus-v3 &&\n", text)   # indexes nothing after a difference
        self.assertIn("cp -r eval/v3-sources/. ~/cerebrollm-corpus-v3/", text)
        copies = [l for l in text.splitlines() if l.strip().startswith("cp ")]
        self.assertTrue(copies and all("~/cerebrollm-corpus-v3" in l for l in copies), copies)


if __name__ == "__main__":
    unittest.main()
