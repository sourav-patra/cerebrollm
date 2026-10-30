"""Tests for eval/check_items_v2.py and the v2 item set. Run: python3 -m unittest eval/test_check_items_v2.py -v
(stdlib only). Group 1 tests use the private items.json when it exists and a synthetic notes folder otherwise.
"""
import builtins
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
import warnings
from unittest import mock

warnings.simplefilter("ignore", ResourceWarning)  # the tests open small files without closing them
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_items as V1  # noqa: E402
import check_items_v2 as V2  # noqa: E402
import grade_lib as G  # noqa: E402


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


def public_rows():
    return [json.loads(l) for l in open(V2.PUBLIC, encoding="utf-8") if l.strip()]


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


if __name__ == "__main__":
    unittest.main()
