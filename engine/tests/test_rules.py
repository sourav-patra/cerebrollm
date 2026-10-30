import unittest

from cerebrollm import config, rules

CFG = config.load()

TIER_TABLE = [
    # (root, relative path, expected (tier, status) or None)
    ("example-repo", "docs/specs/POLICY.md", ("T1", "locked")),
    ("example-repo", "docs/specs/sub/TRD.md", ("T1", "locked")),
    ("example-repo", "README.md", ("T3", "current")),
    ("example-repo", "AGENTS.md", ("T3", "current")),
    ("example-repo", "docs/overview.md", ("T3", "current")),
    ("example-repo", "docs/agents/notes.md", ("T3", "current")),
    ("example-repo", "tools/check.md", None),
    ("notes", "Project A/locked/LLD-PROJECT-2026-10-13.md", ("T1", "locked")),
    ("notes", "shared/ADR-example-lock-2026-10-24.md", ("T1", "locked")),
    ("notes", "shared/POLICY-baseline-2026-10-22.md", ("T1", "locked")),
    ("notes", "shared/PRINCIPLES-locked.md", ("T1", "locked")),
    ("notes", "shared/PRINCIPLES-reviewed.md", ("T2", "current")),
    ("notes", "Project A/notes/BACKLOG.md", ("T2", "current")),
    ("notes", "Project A/notes/sub/notes.md", None),
    ("notes", "Project A/journal/JOURNAL_daily-2026-10-25.md", ("T2", "current")),
    ("notes", "Project A/journal/STATUS-19-oct-project.md", ("T2", "current")),
    ("notes", "Project A/journal/Preferences.md", None),
    ("notes", "project/INDEX.md", ("T2", "current")),
    ("notes", "shared/NOTES-MAP.md", ("T2", "current")),
    ("notes", "shared/drafts/plan-2026-10-26/PLAN.md", ("T4", "draft")),
    ("notes", "Project A/drafts/example/x/y.md", ("T4", "draft")),
    ("notes", "project/drafts/x.md", None),
    ("notes", "project/journal/notes.md", None),
]

NEVER_TABLE = [
    ("Project A/notes/evidence/a.md", True),
    ("project/runs/2026/a.md", True),
    ("project/run/a.md", True),
    ("project/logs/a.md", True),
    ("project/scratch-notes/a.md", True),
    ("project/stage-a3/a.md", True),
    ("project/sim2/a.md", True),
    ("project/archive/a.md", True),
    ("project/.obsidian/a.md", True),
    ("project/a.log", True),
    ("project/a.json", True),
    ("project/a.jsonl", True),
    ("project/a.patch", True),
    ("project/a.map", True),
    ("project/a.lock", True),
    ("project/a.sha256", True),
    ("docs/records/reviews/v1/evidence/checks.md", True),
    ("research/EVAL-SET-r1.md", True),
    ("research/PLAN.md", True),
    ("research/doc-b.md", True),
    ("research/deep/notes.md", True),
    ("research0/PLAN.md", False),   # prefix ends with the slash
    ("project/notes/a.md", False),
    ("project/drafts/a.md", False),
    ("docs/overview.md", False),
]

SUPERSESSION_TABLE = [
    # names in one directory -> the names that stay current
    (["GUIDE-X-REV3-2026-10-18.md", "GUIDE-X-2026-10-11.md"], {"GUIDE-X-REV3-2026-10-18.md"}),
    (["verdict-from-qa.md", "verdict-from-qa-r2.md", "verdict-from-qa-r3.md"], {"verdict-from-qa-r3.md"}),
    (["JOURNAL_ops-2026-10-20.md", "JOURNAL_ops-2026-10-25.md", "JOURNAL_ops-2026-10-19.md"],
     {"JOURNAL_ops-2026-10-20.md", "JOURNAL_ops-2026-10-25.md", "JOURNAL_ops-2026-10-19.md"}),
    (["handover-ops-2026-10-20.md", "handover-ops-2026-10-25.md"], {"handover-ops-2026-10-25.md"}),
    (["spec-rev9.md", "spec-rev16.md"], {"spec-rev16.md"}),
    (["TRD-a-2026-10-20.md", "TRD-a-2026-10-20-r2.md"], {"TRD-a-2026-10-20-r2.md"}),
    (["a-17-oct-2026.md", "a-18-oct.md"], {"a-18-oct.md"}),
    (["alpha.md", "beta.md"], {"alpha.md", "beta.md"}),           # different families
    (["same-2026-10-20.md", "same-2026-10-20-evening.md"], {"same-2026-10-20.md", "same-2026-10-20-evening.md"}),
    (["org-v3.md", "org-v3-reviewed.md"], {"org-v3.md", "org-v3-reviewed.md"}),  # suffix word is not a token
]


class TestTiers(unittest.TestCase):
    def test_table(self):
        for root, path, expected in TIER_TABLE:
            with self.subTest(path=path):
                self.assertEqual(rules.classify(root, path, CFG.rules), expected)

    def test_rule_order_t1_before_t2(self):
        # a shared-folder ADR matches both the ADR rule and the top-level rule; T1 comes first
        self.assertEqual(rules.classify("notes", "shared/ADR-x.md", CFG.rules), ("T1", "locked"))


class TestNever(unittest.TestCase):
    def test_table(self):
        for path, never in NEVER_TABLE:
            with self.subTest(path=path):
                self.assertEqual(rules.never_reason(path, CFG.never) is not None, never)


class TestSupersession(unittest.TestCase):
    def run_family(self, names, texts=None):
        entries = [{"root": "notes", "path": "P/" + n, "status": "current",
                    "text": (texts or {}).get(n, "")} for n in names]
        rules.apply_supersession(entries)
        return {e["path"][2:] for e in entries if e["status"] == "current"}

    def test_table(self):
        for names, current in SUPERSESSION_TABLE:
            with self.subTest(names=names):
                self.assertEqual(self.run_family(names), current)

    def test_other_directory_is_not_a_family(self):
        entries = [{"root": "notes", "path": "A/x-r1.md", "status": "current", "text": ""},
                   {"root": "notes", "path": "B/x-r2.md", "status": "current", "text": ""}]
        rules.apply_supersession(entries)
        self.assertEqual([e["status"] for e in entries], ["current", "current"])

    def test_status_line(self):
        self.assertEqual(self.run_family(["a.md"], {"a.md": "# T\nStatus: superseded by b\n"}), set())
        self.assertEqual(self.run_family(["a.md"], {"a.md": "> **Status:** SUPERSEDED\n"}), set())
        self.assertEqual(self.run_family(["a.md"], {"a.md": "Status: not superseded\n"}), {"a.md"})
        self.assertEqual(self.run_family(["a.md"], {"a.md": "Status: draft\nThis supersedes b.\n"}), {"a.md"})
        self.assertEqual(self.run_family(["a.md"], {"a.md": "The status of x is superseded\n"}), {"a.md"})

    def test_status_value_must_start_with_superseded(self):
        # a phrase inside a status value does not make the whole file superseded
        self.assertEqual(self.run_family(["a.md"], {"a.md": "Status: current view. Everything below is "
                                                            "individual details may be superseded by a later note.\n"}),
                         {"a.md"})
        self.assertEqual(self.run_family(["a.md"], {"a.md": "Status: supersedes a.md\n"}), {"a.md"})
        self.assertEqual(self.run_family(["a.md"], {"a.md": "Status: never superseded\n"}), {"a.md"})

    def test_superseded_by_line(self):
        self.assertEqual(self.run_family(["a.md"], {"a.md": "Superseded by b.md\n"}), set())
        self.assertEqual(self.run_family(["a.md"], {"a.md": "superseded by b.md\n"}), set())
        self.assertEqual(self.run_family(["a.md"], {"a.md": "Text. Superseded by b.md\n"}), {"a.md"})

    def test_status_window_is_thirty_lines(self):
        late = "filler\n" * 30 + "Status: superseded\n"
        self.assertEqual(self.run_family(["a.md"], {"a.md": late}), {"a.md"})

    def test_journal_files_are_never_superseded_by_family(self):
        names = ["JOURNAL_daily-2026-10-22.md", "JOURNAL_daily-2026-10-21.md",
                 "JOURNAL_daily-2026-10-20.md"]
        self.assertEqual(self.run_family(names), set(names))

    def test_journal_file_does_not_supersede_a_family_member(self):
        entries = [{"root": "notes", "path": "M/JOURNAL_x-r2.md", "status": "current", "text": ""},
                   {"root": "notes", "path": "M/JOURNAL_x-r1.md", "status": "current", "text": ""},
                   {"root": "notes", "path": "M/x-r1.md", "status": "current", "text": ""},
                   {"root": "notes", "path": "M/x-r2.md", "status": "current", "text": ""}]
        rules.apply_supersession(entries)
        status = {e["path"]: e["status"] for e in entries}
        self.assertEqual(status["M/JOURNAL_x-r1.md"], "current")
        self.assertEqual(status["M/x-r1.md"], "superseded")

    def test_family_key(self):
        self.assertEqual(rules.family("GUIDE-PROJECT-REV3-2026-10-18.md")[0], "guide-project")
        self.assertEqual(rules.family("GUIDE-PROJECT-2026-10-11.md")[0], "guide-project")
        self.assertGreater(rules.family("x-r3.md")[1], rules.family("x-r2.md")[1])
        self.assertGreater(rules.family("x-2026-10-25.md")[1], rules.family("x-2026-10-24.md")[1])


class TestDuplicates(unittest.TestCase):
    @staticmethod
    def entry(root, path, sha, tier="T1", status="locked"):
        return {"root": root, "path": path, "sha256": sha, "tier": tier, "status": status}

    def test_copies_collapse_to_the_newest_folder(self):
        entries = [
            self.entry("example-repo", "docs/a/r3/N.md", "s1"),
            self.entry("example-repo", "docs/a/r5/N.md", "s1"),
            self.entry("example-repo", "docs/a/r4/N.md", "s1"),
            self.entry("example-repo", "docs/a/r4/O.md", "s2"),
        ]
        kept, removed = rules.collapse_duplicates(entries)
        self.assertEqual(removed, 2)
        by_path = {e["path"]: e for e in kept}
        self.assertEqual(set(by_path), {"docs/a/r5/N.md", "docs/a/r4/O.md"})
        self.assertEqual(by_path["docs/a/r5/N.md"]["also_at"],
                         ["example-repo:docs/a/r3/N.md",
                          "example-repo:docs/a/r4/N.md"])
        self.assertEqual(by_path["docs/a/r4/O.md"]["also_at"], [])

    def test_copies_across_tiers_keep_the_highest_authority(self):
        # a current T2 file with a copy under drafts/ keeps its T2 entry; the draft is only listed
        entries = [
            self.entry("notes", "Project A/drafts/example/A.md", "s1", "T4", "draft"),
            self.entry("notes", "Project A/notes/A.md", "s1", "T2", "current"),
            self.entry("example-repo", "docs/a/x/A.md", "s1", "T1", "locked"),
        ]
        kept, removed = rules.collapse_duplicates(entries)
        self.assertEqual(removed, 2)
        self.assertEqual(len(kept), 1)
        self.assertEqual((kept[0]["tier"], kept[0]["status"]), ("T1", "locked"))
        self.assertEqual(kept[0]["also_at"], ["notes:Project A/drafts/example/A.md",
                                              "notes:Project A/notes/A.md"])

    def test_active_copy_beats_superseded_and_draft_beats_superseded(self):
        entries = [
            self.entry("notes", "Project A/notes/B.md", "s2", "T2", "superseded"),
            self.entry("notes", "Project A/drafts/x/B.md", "s2", "T4", "draft"),
        ]
        kept, _ = rules.collapse_duplicates(entries)
        self.assertEqual((kept[0]["path"], kept[0]["status"]),
                         ("Project A/drafts/x/B.md", "draft"))

    def test_copies_across_roots_collapse(self):
        entries = [self.entry("notes", "Project A/locked/L.md", "s1"),
                   self.entry("example-repo", "docs/a/L.md", "s1")]
        kept, removed = rules.collapse_duplicates(entries)
        self.assertEqual(removed, 1)
        self.assertEqual(kept[0]["path"], "docs/a/L.md")          # "docs" sorts after "Project A"
        self.assertEqual(kept[0]["also_at"], ["notes:Project A/locked/L.md"])


class TestSecrets(unittest.TestCase):
    def test_hits(self):
        self.assertTrue(rules.secret_hit("-----BEGIN RSA PRIVATE KEY-----"))
        self.assertTrue(rules.secret_hit("key " + "AKIA" + "ABCDEFGHIJKLMNOP" + " here"))   # built at runtime
        self.assertTrue(rules.secret_hit("token = ghp_" + "a1" * 20))
        self.assertTrue(rules.secret_hit('api_key: "abcd1234abcd1234abcd1234abcd"'))

    def test_clean(self):
        self.assertIsNone(rules.secret_hit("sk-first-and-then-some-more-words-here"))
        self.assertIsNone(rules.secret_hit("the token budget is 2000"))
        self.assertIsNone(rules.secret_hit("password: see the vault"))


class TestGlob(unittest.TestCase):
    """full_match semantics of pathlib 3.13: ** spans zero or more directories, matching is case-sensitive."""

    def test_cases(self):
        from pathlib import PurePosixPath as P
        for path, glob, want in [
            ("a.md", "**/*.md", True), ("x/y/a.md", "**/*.md", True), ("x/a.txt", "**/*.md", False),
            ("docs/specs/d/N.md", "docs/specs/**/*.md", True), ("docs/specs/N.md", "docs/specs/**/*.md", True),
            ("README.md", "README.md", True), ("docs/README.md", "README.md", False),
            ("A/INDEX.md", "*/INDEX.md", True), ("A/B/INDEX.md", "*/INDEX.md", False),
            ("a.MD", "**/*.md", False), ("shared/ADR-1.md", "shared/ADR-*.md", True),
        ]:
            self.assertEqual(rules.full_match(P(path), glob), want, (path, glob))


class TestPublicCorpusRules(unittest.TestCase):
    def test_each_source_folder_is_t3_current(self):
        for folder in ["llama_index", "ollama", "pgvector", "promptfoo", "cerebrollm"]:
            for rel in ["%s/a.md" % folder, "%s/docs/b/c.md" % folder]:
                self.assertEqual(rules.classify("notes", rel, CFG.rules), ("T3", "current"), rel)
        self.assertIsNone(rules.classify("notes", "other/a.md", CFG.rules))


if __name__ == "__main__":
    unittest.main()
