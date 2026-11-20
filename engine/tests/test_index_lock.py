"""Index writer locks: two `cerebrollm index` runs never write at once. The writers are real subprocesses
(tests/index_writer.py) on the real Postgres. Each test has its own state directory and a table name with
a random suffix, so two runs of this file never touch each other's tables. The embedding model is a
fixed-vector mock, so Ollama is not needed. Skipped with a message only when the Postgres server cannot
be reached; a wrong database or role fails the tests."""
import copy
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest import mock

import psycopg2
from llama_index.core.storage.docstore import SimpleDocumentStore

from cerebrollm import config, indexer, store
from tests import SCRATCH

ENGINE = Path(__file__).resolve().parent.parent
WAIT = 120   # seconds; every wait in these tests is bounded

FILES = {
    "alpha/review.md": "# Review\n\nA change gets two review rounds. The basaltwren token marks this file.\n",
    "alpha/guide.md": "# Guide\n\nThe guide explains how the pipeline records evidence.\n",
    "beta/merge.md": "# Merge\n\nA pull request merges when both checks pass.\n",
}
NEW_FILE = ("alpha/new.md", "# New\n\nThe lockquasar token appears only in a file added later.\n")
NO_PID_LINE = "index already running: %s is held by another process (this system does not list its process id)"
UNREACHABLE = ("No such file or directory", "Connection refused")   # libpq: no socket, or no listener


def postgres_skip_reason(cfg):
    """A skip reason when the server cannot be reached (socket missing, connection refused); None when
    a connection opens. Any other error, such as a database or role the server rejects, is raised."""
    try:
        conn = store.connect(cfg)
    except psycopg2.OperationalError as exc:
        text = " ".join(str(exc).split())
        if "FATAL" not in text and any(cause in text for cause in UNREACHABLE):
            return "Postgres unavailable: %s" % text
        raise
    conn.close()
    return None


def make_data(root, state, table):
    data = copy.deepcopy(config.load().data)
    data["domain"] = "org"
    data["state_dir"] = str(state)
    data["postgres"]["table"] = table
    data["root"] = [{"name": "fx", "kind": "dir", "path": str(root), "ref": "file"}]
    data["rule"] = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"}]
    return data


def wait_for(path, proc, what):
    """Wait, at most WAIT seconds, until path exists; fail if proc exits first."""
    deadline = time.time() + WAIT
    while not path.exists():
        if proc.poll() is not None:
            raise AssertionError("%s: process exited %s first" % (what, proc.returncode))
        if time.time() > deadline:
            raise AssertionError("%s: not ready after %d s" % (what, WAIT))
        time.sleep(0.05)


def holder_line(lock, pid):
    """The contention line a second run prints for the flock on lock held by process pid: with the id where
    the system lists flock holders (Linux, /proc/locks), without it where it does not (macOS)."""
    if os.path.exists(indexer.LOCKS_FILE):
        return "index already running: %s is held by process %d" % (lock, pid)
    return NO_PID_LINE % lock


class TestFlockHolderLookup(unittest.TestCase):
    """The holder lookup on both platforms, with the lock table replaced by a fixture file: no server and
    no /proc/locks needed. The flock is held through a second open file description in this process,
    which a flock on a fresh description is refused for, as it is for another process."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.lock = Path(self.tmp.name) / "index.lock"
        self.lock.touch()
        self.held = os.open(self.lock, os.O_RDONLY)
        self.addCleanup(os.close, self.held)
        fcntl.flock(self.held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.contender = os.open(self.lock, os.O_RDONLY)
        self.addCleanup(os.close, self.contender)

    def lock_table(self, pid):
        """A lock table in the /proc/locks format that lists the held lock under process pid."""
        st = os.fstat(self.held)
        dev = "%02x:%02x:%d" % (os.major(st.st_dev), os.minor(st.st_dev), st.st_ino)
        table = Path(self.tmp.name) / "locks"
        table.write_text("1: POSIX  ADVISORY  WRITE 777 00:01:1 0 EOF\n"
                         "2: FLOCK  ADVISORY  WRITE %d %s 0 EOF\n" % (pid, dev))
        return str(table)

    def take(self):
        with self.assertRaises(SystemExit) as raised:
            indexer._take_flock(self.contender, self.lock)
        return str(raised.exception)

    def test_holder_listed_in_the_lock_table_is_named(self):
        with mock.patch.object(indexer, "LOCKS_FILE", self.lock_table(424242)):
            self.assertEqual(self.take(), "index already running: %s is held by process 424242" % self.lock)

    def test_no_lock_table_gives_the_line_without_a_process_id(self):
        missing = str(Path(self.tmp.name) / "no-such-lock-table")
        with mock.patch.object(indexer, "LOCKS_FILE", missing):
            self.assertIsNone(indexer._flock_holder(self.contender))
            line = self.take()
        self.assertEqual(line, NO_PID_LINE % self.lock)
        self.assertNotRegex(line, r"process \d")

    def test_lock_table_without_the_file_gives_the_line_without_a_process_id(self):
        table = Path(self.tmp.name) / "empty-locks"
        table.write_text("1: POSIX  ADVISORY  WRITE 777 00:01:1 0 EOF\n")
        with mock.patch.object(indexer, "LOCKS_FILE", str(table)):
            self.assertEqual(self.take(), NO_PID_LINE % self.lock)

    def test_holder_released_after_a_failed_attempt_is_overtaken_without_a_lock_table(self):
        """Without a lock table the first attempt fails and no holder is listed; the holder releases the
        lock before the second attempt (here during the pause between them), which takes it."""
        missing = str(Path(self.tmp.name) / "no-such-lock-table")
        pauses = []

        def holder_releases(seconds):
            pauses.append(seconds)
            fcntl.flock(self.held, fcntl.LOCK_UN)
        with mock.patch.object(indexer, "LOCKS_FILE", missing):
            with mock.patch.object(indexer.time, "sleep", holder_releases):
                indexer._take_flock(self.contender, self.lock)   # returns: the flock is taken
        self.assertEqual(len(pauses), 1)


class TestPostgresProbe(unittest.TestCase):
    """The skip decision itself, with store.connect replaced: no server needed."""

    def probe(self, message):
        with mock.patch("cerebrollm.store.connect", side_effect=psycopg2.OperationalError(message)):
            return postgres_skip_reason(config.load())

    def test_unreachable_server_skips(self):
        self.assertIn("Postgres unavailable", self.probe(
            'connection to server on socket "/x/.s.PGSQL.54329" failed: No such file or directory\n'
            "\tIs the server running locally and accepting connections on that socket?"))
        self.assertIn("Postgres unavailable", self.probe(
            'connection to server on socket "/x/.s.PGSQL.54329" failed: Connection refused'))

    def test_rejected_database_or_role_fails(self):
        for message in ('connection to server on socket "/x/.s.PGSQL.54329" failed: FATAL:  database '
                        '"nope" does not exist',
                        'connection to server on socket "/x/.s.PGSQL.54329" failed: FATAL:  role "nope" '
                        "does not exist"):
            with self.subTest(message=message):
                with self.assertRaises(psycopg2.OperationalError):
                    self.probe(message)


class TestIndexLock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reason = postgres_skip_reason(config.load())
        if reason:
            raise unittest.SkipTest(reason)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        base = Path(self.tmp.name)
        self.root = base / "corpus"
        for rel, text in FILES.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        self.hold = base / "hold"
        self.hold.mkdir()
        self.table = "cerebrollm_locktest_" + uuid.uuid4().hex[:10]
        self.data = make_data(self.root, base / "state", self.table)
        self.cfg = config.Config(self.data, Path("test"))
        self.cfg_json = base / "config.json"
        self.cfg_json.write_text(json.dumps(self.data))
        self.procs = []
        self.cfgs = [self.cfg]   # every config whose tables tearDown drops
        self.schemas = []        # schemas a test created; tearDown drops them

    def tearDown(self):
        (self.hold / "release").touch()
        for p in self.procs:
            if p.poll() is None:
                p.kill()
            p.wait(WAIT)
        for cfg in self.cfgs:
            for name in (cfg.data_table, cfg.next_data_table, "data_%s_old" % cfg.table):
                store.drop_table(self.cfg, name)
        with store.sql(self.cfg) as cur:
            for schema in self.schemas:
                cur.execute("drop schema if exists %s cascade" % schema)
        self.tmp.cleanup()

    # --- helpers -------------------------------------------------------------------------------

    def start(self, *args, hold=False, cfg_json=None, env_extra=None):
        env = dict(os.environ)
        env.pop("INDEX_HOLD_DIR", None)
        env.pop("INDEX_IDLE_TIMEOUT_MS", None)
        if hold:
            env["INDEX_HOLD_DIR"] = str(self.hold)
        env.update(env_extra or {})
        p = subprocess.Popen([sys.executable, "-m", "tests.index_writer", str(cfg_json or self.cfg_json)]
                             + list(args), cwd=ENGINE, env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.procs.append(p)
        return p

    def other_config(self, name, **changes):
        """A second config, written as JSON beside the first, whose tables tearDown also drops."""
        data = copy.deepcopy(self.data)
        if "table" in changes:
            data["postgres"]["table"] = changes.pop("table")
        data.update(changes)
        self.cfgs.append(config.Config(data, Path("test")))
        path = Path(self.tmp.name) / ("%s.json" % name)
        path.write_text(json.dumps(data))
        return data, path

    def one_error_line(self, code, out, err):
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        lines = err.strip().splitlines()
        self.assertEqual(len(lines), 1, err)
        return lines[0]

    def run_cli(self, *args, cfg_json=None, env_extra=None):
        p = self.start(*args, cfg_json=cfg_json, env_extra=env_extra)
        out, err = p.communicate(timeout=WAIT)
        return p.returncode, out, err

    def start_holding_writer(self, env_extra=None):
        first = self.start("index", hold=True, env_extra=env_extra)
        try:
            wait_for(self.hold / "inside", first, "holding writer")
        except AssertionError as exc:
            self.fail("%s: %s" % (exc, first.stderr.read() if first.poll() is not None else ""))
        return first

    def release(self, proc):
        (self.hold / "release").touch()
        out, err = proc.communicate(timeout=WAIT)
        self.assertEqual(proc.returncode, 0, err)
        return json.loads(out)

    def search_paths(self, query):
        code, out, err = self.run_cli("search", query, "--mode", "lexical", "--json")
        self.assertEqual(code, 0, err)
        return [h["path"] for h in json.loads(out)]

    def exists(self, name):
        with store.sql(self.cfg) as cur:
            return store._regclass(cur, name)

    def assert_consistent(self, mode, summary=None):
        """One finished run, no leftovers: live table only, docstore.json matches its doc ids,
        state.json names the run's mode."""
        self.assertTrue(self.exists(self.cfg.data_table))
        self.assertFalse(self.exists(self.cfg.next_data_table))
        self.assertFalse(self.exists("data_%s_old" % self.cfg.table))
        self.assertFalse(self.cfg.next_docstore_path.exists())
        docstore = SimpleDocumentStore.from_persist_path(str(self.cfg.docstore_path))
        with store.sql(self.cfg) as cur:
            cur.execute("select distinct metadata_->>'doc_id' from %s" % self.cfg.data_table)
            table_ids = {r[0] for r in cur.fetchall()}
        self.assertEqual(set(docstore.get_all_document_hashes().values()), table_ids)
        state = store.read_state(self.cfg)
        self.assertEqual(state["last_index"]["mode"], mode)
        if summary is not None:
            self.assertEqual(state["last_index"], summary)
            if mode == "full":
                self.assertEqual(store.row_count(self.cfg, self.cfg.data_table), summary["chunks_embedded"])

    def wait_for_idle_expiry(self, timeout_ms):
        """Open a control session with idle_session_timeout timeout_ms, after the writer's lock session,
        leave it idle, and wait (at most 30 s) until the server has ended it. An idle session of the writer
        that has no protection is gone by then, because it went idle first."""
        conn = psycopg2.connect(host=self.cfg.pg["socket_dir"], port=self.cfg.pg["port"],
                                dbname=self.cfg.pg["database"], user=self.cfg.pg["user"],
                                options="-c idle_session_timeout=%d" % timeout_ms)
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("select pg_backend_pid()")
                pid = cur.fetchone()[0]
            deadline = time.time() + 30
            while True:
                time.sleep(0.2)
                with store.sql(self.cfg) as cur:
                    cur.execute("select count(*) from pg_stat_activity where pid = %s", (pid,))
                    if cur.fetchone()[0] == 0:
                        return
                self.assertLess(time.time(), deadline, "the server did not end the idle control session")
        finally:
            conn.close()

    def advisory_lock_free(self):
        """No session holds an advisory lock on the live data table (key as the index run derives it)."""
        key = "hashtextextended(lower(%s), 0)"
        conn = store.connect(self.cfg)
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("select pg_try_advisory_lock(%s)" % key, (self.cfg.data_table,))
                got = cur.fetchone()[0]
                if got:
                    cur.execute("select pg_advisory_unlock(%s)" % key, (self.cfg.data_table,))
                return got
        finally:
            conn.close()

    def index_baseline(self):
        code, out, err = self.run_cli("index")
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def table_refusal(self, name):
        return "index already running: table %s is locked by another index run" % name

    # --- overlapping writers -------------------------------------------------------------------

    def overlap(self, second_args):
        self.index_baseline()
        (self.root / NEW_FILE[0]).write_text(NEW_FILE[1])
        first = self.start_holding_writer()
        line = self.one_error_line(*self.run_cli(*second_args))
        self.assertIsNone(first.poll(), "the first writer must still hold the locks")
        self.assertEqual(line, holder_line(self.cfg.state_dir / "index.lock", first.pid))
        # search takes no lock and reads the live table while the build holds both locks
        self.assertEqual(self.search_paths("basaltwren"), ["alpha/review.md"])
        self.assertEqual(self.search_paths("lockquasar"), [])
        self.assertIsNone(first.poll())
        summary = self.release(first)
        self.assertEqual(summary["mode"], "full")
        self.assert_consistent("full", summary)
        self.assertEqual(self.search_paths("lockquasar"), [NEW_FILE[0]])

    def test_full_and_full_overlap(self):
        self.overlap(["index"])

    def test_full_and_changed_overlap(self):
        self.overlap(["index", "--changed"])

    def test_second_config_on_the_same_table(self):
        """Configs with their own state directory but the same physical table (the name as given, and in
        upper case, which PostgreSQL folds to the same unquoted name) are stopped by the advisory lock."""
        self.index_baseline()
        first = self.start_holding_writer()
        for n, table in enumerate([self.table, self.table.upper()]):
            with self.subTest(table=table):
                other, other_json = self.other_config(
                    "same%d" % n, table=table, state_dir=str(Path(self.tmp.name) / ("state-same%d" % n)))
                line = self.one_error_line(*self.run_cli("index", cfg_json=other_json))
                self.assertEqual(line, self.table_refusal("data_" + table))
                self.assertFalse((Path(other["state_dir"]) / "docstore.json").exists())
        self.assertIsNone(first.poll())
        self.assert_consistent("full", self.release(first))

    def test_second_config_with_another_search_path(self):
        """A run whose search_path starts with another existing schema still contends for the same table
        names: its unqualified DROP of the _next table would reach this run's build table."""
        self.index_baseline()
        schema = "cl_locktest_" + uuid.uuid4().hex[:10]
        with store.sql(self.cfg) as cur:
            cur.execute("create schema %s" % schema)
        self.schemas.append(schema)
        first = self.start_holding_writer()
        _, other_json = self.other_config("path", state_dir=str(Path(self.tmp.name) / "state-path"))
        line = self.one_error_line(*self.run_cli(
            "index", cfg_json=other_json, env_extra={"PGOPTIONS": "-c search_path=%s,public" % schema}))
        self.assertEqual(line, self.table_refusal(self.cfg.data_table))
        self.assertIsNone(first.poll())
        self.assert_consistent("full", self.release(first))

    def test_config_whose_live_table_is_the_build_table(self):
        """A config whose live table is this config's _next table: a full run here rebuilds that table,
        so the other run is refused while this one holds its locks."""
        self.index_baseline()
        first = self.start_holding_writer()
        _, other_json = self.other_config("next", table=self.table + "_next",
                                          state_dir=str(Path(self.tmp.name) / "state-next"))
        line = self.one_error_line(*self.run_cli("index", cfg_json=other_json))
        self.assertEqual(line, self.table_refusal(self.cfg.next_data_table))
        self.assertIsNone(first.poll())
        self.assert_consistent("full", self.release(first))

    def test_lock_session_outlives_the_server_idle_timeout(self):
        """A server that ends idle sessions after one second (set for the writer's connections) does not
        release the table locks while the run embeds: another config on the same table is still refused."""
        self.index_baseline()
        first = self.start_holding_writer(env_extra={"INDEX_IDLE_TIMEOUT_MS": "1000"})
        self.wait_for_idle_expiry(1000)   # the server has ended an idle session opened after the writer's
        self.assertIsNone(first.poll())
        self.assertFalse(self.advisory_lock_free())
        _, other_json = self.other_config("idle", state_dir=str(Path(self.tmp.name) / "state-idle"))
        line = self.one_error_line(*self.run_cli("index", cfg_json=other_json))
        self.assertEqual(line, self.table_refusal(self.cfg.data_table))
        self.assert_consistent("full", self.release(first))

    # --- names PostgreSQL would cut ------------------------------------------------------------

    def refusal(self, table):
        shown = "data_%s_next_id_seq" % table
        return ("refusing to index: the name %r derived from postgres.table is %d bytes and PostgreSQL cuts "
                "names at 63, so another config's table could be the same table. Use a postgres.table of at "
                "most 46 bytes (this one is %d)" % (shown, len(shown.encode()), len(table.encode())))

    def test_overlength_derived_names_are_refused_before_any_lock(self):
        """A table name whose derived names (data_<table>_next, its key and its sequence) pass 63 bytes
        is refused before the lock file, the database or the corpus is touched. The refusal counts bytes,
        not characters. The 54-byte table and its "_nex" neighbour are the pair whose names PostgreSQL
        would otherwise fold into one table; 47 bytes is one past the longest table that works."""
        long_table = self.table + "p" * (54 - len(self.table))
        for table in (long_table, long_table + "_nex", self.table + "\u00e9" * 12,
                      self.table + "q" * (47 - len(self.table)), long_table + "\nfake second line"):
            with self.subTest(table=table):
                _, other_json = self.other_config(
                    "long", table=table, state_dir=str(Path(self.tmp.name) / "state-long"))
                self.cfgs.pop()   # no table is ever created, and tearDown cannot drop a name with a line break
                line = self.one_error_line(*self.run_cli("index", cfg_json=other_json))
                self.assertEqual(line, self.refusal(table))
                self.assertFalse((Path(self.tmp.name) / "state-long").exists())
                for name in ("data_" + table, "data_%s_next" % table, "data_%s_old" % table):
                    self.assertFalse(self.exists(name))

    def test_overlength_refusal_comes_before_any_connection_or_corpus_scan(self):
        """The refusal is the first thing run_index does: a connection to the database or a scan of the
        corpus before it would fail this test."""
        self.other_config("order", table=self.table + "r" * (47 - len(self.table)))
        cfg = self.cfgs[-1]
        with mock.patch("cerebrollm.store.connect", side_effect=AssertionError("connected")),                 mock.patch("cerebrollm.corpus.enumerate_corpus", side_effect=AssertionError("scanned")):
            with self.assertRaises(SystemExit) as caught:
                indexer.run_index(cfg)
        self.assertEqual(str(caught.exception), self.refusal(cfg.table))

    def test_longest_accepted_table_name_indexes_and_swaps(self):
        """46 bytes is the longest table: the sequence data_<table>_next_id_seq is then exactly 63 bytes.
        A full run, a second full run (which swaps over a live table) and a changed run all finish."""
        table = self.table + "b" * (46 - len(self.table))
        _, other_json = self.other_config("edge", table=table, state_dir=str(Path(self.tmp.name) / "state-edge"))
        cfg = self.cfgs[-1]
        embedded = []
        for args in (["index"], ["index"], ["index", "--changed"]):
            code, out, err = self.run_cli(*args, cfg_json=other_json)
            self.assertEqual(code, 0, err)
            embedded.append(json.loads(out)["chunks_embedded"])
        self.assertGreater(embedded[0], 0)
        self.assertEqual(store.row_count(cfg, cfg.data_table), embedded[1])
        self.assertFalse(self.exists(cfg.next_data_table))

    # --- naming the holder ---------------------------------------------------------------------

    def start_flock_holder(self, lock):
        """A plain process that holds the flock on lock; returns once it holds it (bounded wait)."""
        ready = Path(self.tmp.name) / "holder-ready"
        holder = subprocess.Popen(
            [sys.executable, "-c", "import fcntl, os, pathlib, sys, time; fd = os.open(sys.argv[1], os.O_RDONLY); "
             "fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); pathlib.Path(sys.argv[2]).touch(); "
             "time.sleep(%d)" % WAIT, str(lock), str(ready)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.procs.append(holder)
        wait_for(ready, holder, "flock holder")
        return holder

    def test_contender_names_the_kernel_holder_not_the_file_content(self):
        """The holder's process id comes from the kernel lock table: whatever id the file holds is never
        reported, and the file is not rewritten. Where there is no lock table (macOS) the line has no id."""
        self.cfg.state_dir.mkdir(parents=True)
        lock = self.cfg.state_dir / "index.lock"
        lock.write_text("999999\n")
        holder = self.start_flock_holder(lock)
        line = self.one_error_line(*self.run_cli("index"))
        self.assertEqual(line, holder_line(lock, holder.pid))
        self.assertNotIn("999999", line)
        self.assertEqual(lock.read_text(), "999999\n")

    def test_flock_released_before_the_holder_lookup_is_retried(self):
        """A holder that releases the flock between the failed attempt and the /proc/locks lookup is not
        reported without a process id: the run tries the flock again and takes the locks."""
        self.cfg.state_dir.mkdir(parents=True)
        lock = self.cfg.state_dir / "index.lock"
        lock.touch()
        holder = self.start_flock_holder(lock)
        real_lookup = indexer._flock_holder
        calls = []

        def released_meanwhile(fd):
            calls.append(fd)
            if len(calls) == 1:
                holder.kill()
                holder.wait(WAIT)
                return None
            return real_lookup(fd)
        entered = []
        with mock.patch("cerebrollm.indexer._flock_holder", released_meanwhile):
            with indexer.writer_lock(self.cfg):
                entered.append(True)
        self.assertEqual(entered, [True])
        self.assertEqual(len(calls), 1)

    # --- where the lock writes -----------------------------------------------------------------

    def test_lock_file_never_changes_an_existing_file(self):
        """An existing index.lock is only opened read-only: a same-owner digits-only file and a second
        hard link keep their bytes through a full run; a symbolic link and a FIFO are refused."""
        self.cfg.state_dir.mkdir(parents=True)
        lock = self.cfg.state_dir / "index.lock"
        digits = "1" * 40 + "\n"
        lock.write_text(digits)
        self.index_baseline()
        self.assertEqual(lock.read_text(), digits)
        lock.unlink()
        victim = Path(self.tmp.name) / "victim.txt"
        victim.write_text("precious content\n")
        os.link(victim, lock)
        self.index_baseline()
        self.assertEqual(victim.read_text(), "precious content\n")
        lock.unlink()
        lock.symlink_to(victim)
        line = self.one_error_line(*self.run_cli("index"))
        self.assertEqual(line, "refusing to index: lock file %s is a symbolic link; move it away and run again"
                         % lock)
        self.assertEqual(victim.read_text(), "precious content\n")
        lock.unlink()
        os.mkfifo(lock)
        line = self.one_error_line(*self.run_cli("index"))
        self.assertEqual(line, "refusing to index: lock file %s is not a regular file; move it away and run "
                         "again" % lock)

    # --- release -------------------------------------------------------------------------------

    def test_sigkill_releases_both_locks(self):
        self.index_baseline()
        first = self.start_holding_writer()
        first.kill()
        first.wait(WAIT)
        deadline = time.time() + 30   # the server ends the killed session shortly after the socket closes
        while not self.advisory_lock_free():
            self.assertLess(time.time(), deadline, "advisory lock still held after SIGKILL")
            time.sleep(0.2)
        code, out, err = self.run_cli("index")
        self.assertEqual(code, 0, err)
        self.assert_consistent("full", json.loads(out))
        code, out, err = self.run_cli("index", "--changed")
        self.assertEqual(code, 0, err)
        self.assert_consistent("changed", json.loads(out))

    def test_locks_released_when_the_run_raises(self):
        from cerebrollm.indexer import run_index
        (Path(self.tmp.name) / "empty").mkdir()
        empty = config.Config(make_data(Path(self.tmp.name) / "empty", self.cfg.state_dir, self.table),
                              Path("test"))
        for _ in range(2):
            with self.assertRaises(SystemExit) as caught:
                run_index(empty)
            self.assertIn("corpus scan found no files", str(caught.exception))
        self.assertTrue(self.advisory_lock_free())
        self.index_baseline()


if __name__ == "__main__":
    unittest.main()
