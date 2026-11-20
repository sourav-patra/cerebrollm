"""The [postgres] connection: Unix socket (default) or TCP with host, port and an optional password
read from an environment variable. The first classes need no database. The last class starts its own
throw-away PostgreSQL cluster that listens on 127.0.0.1 only, with password authentication, in a
scratch folder of this test; it skips with the cause when PostgreSQL 16 or pgvector is not installed."""
import asyncio
import copy
import itertools
import os
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import psycopg2
from llama_index.core.schema import TextNode
from llama_index.core.storage.docstore import SimpleDocumentStore
from sqlalchemy import text
from sqlalchemy.exc import OperationalError as SAOperationalError

from cerebrollm import config, indexer, mcp_server, status, store
from tests import SCRATCH

ENV = "CEREBROLLM_TEST_PG_PASSWORD"
SECRET = "p@ss:w/rd#1 x"   # characters that must be percent-encoded in a URL


def make(state_dir=None, **pg):
    """A Config from the shipped one with [postgres] keys replaced: socket_dir is dropped when host is given."""
    data = copy.deepcopy(config.load().data)
    if state_dir is not None:
        data["state_dir"] = str(state_dir)
    if "host" in pg:
        del data["postgres"]["socket_dir"]
    data["postgres"].update(pg)
    return config.Config(data, Path("test"))


class TestSocketIsTheDefault(unittest.TestCase):
    def test_shipped_config_is_a_socket_connection_with_the_same_url(self):
        cfg = config.load()
        sock, port = cfg.pg["socket_dir"], cfg.pg["port"]
        self.assertIsNone(cfg.pg_host)
        self.assertEqual(cfg.sync_url, "postgresql+psycopg2://cerebrollm@/rag_local?host=%s&port=%s" % (sock, port))
        self.assertEqual(cfg.async_url, "postgresql+asyncpg://cerebrollm@/rag_local?host=%s&port=%s" % (sock, port))
        self.assertEqual(cfg.pg_connect_args(), {"host": sock, "port": port, "dbname": "rag_local", "user": "cerebrollm"})
        self.assertEqual(cfg.pg_connection_label(), "postgres connection: unix socket")

    def test_status_json_names_the_connection(self):
        for cfg, label in ((config.load(), "postgres connection: unix socket"),
                           (make(host="127.0.0.1", port=5433), "postgres connection: tcp 127.0.0.1:5433")):
            with mock.patch("cerebrollm.store.read_state", lambda c: {}),                     mock.patch("cerebrollm.store.table_exists", lambda c: False):
                self.assertTrue(status.collect(cfg)["connection"].startswith(label))

    def test_status_for_a_socket_keeps_its_folder_lines(self):
        cfg = config.load()
        with mock.patch("cerebrollm.store.read_state", lambda c: {}), \
                mock.patch("cerebrollm.store.table_exists", lambda c: False), \
                mock.patch("cerebrollm.status.socket_dir_mode", lambda p: "0755"):
            text_out = status.format_status(cfg, status.collect(cfg))
        self.assertIn("postgres connection: unix socket", text_out)
        self.assertIn("postgres socket folder: %s  mode 0755" % cfg.pg["socket_dir"], text_out)
        self.assertIn("WARNING: other local users can reach the database socket", text_out)


class TestTcpConfig(unittest.TestCase):
    def test_host_and_port_make_a_tcp_url_without_a_password(self):
        cfg = make(host="127.0.0.1", port=5433)
        self.assertEqual(cfg.sync_url, "postgresql+psycopg2://cerebrollm@127.0.0.1:5433/rag_local")
        self.assertEqual(cfg.async_url, "postgresql+asyncpg://cerebrollm@127.0.0.1:5433/rag_local")
        self.assertEqual(cfg.pg_connect_args(), {"host": "127.0.0.1", "hostaddr": "127.0.0.1", "port": 5433,
                                                  "dbname": "rag_local", "user": "cerebrollm",
                                                  "connect_timeout": config.PG_CONNECT_TIMEOUT})
        self.assertEqual(make(host="::1", port=5433).pg_connect_args()["hostaddr"], "::1")
        self.assertEqual(cfg.pg_connection_label(),
                         "postgres connection: tcp 127.0.0.1:5433  user cerebrollm  no password")

    def test_password_comes_from_the_named_variable_and_is_encoded_in_the_url(self):
        with mock.patch.dict(os.environ, {ENV: SECRET}):
            cfg = make(host="localhost", port=54329, password_env=ENV)
        self.assertIn("cerebrollm:p%40ss%3Aw%2Frd%231 x@127.0.0.1:54329/rag_local", cfg.sync_url)
        self.assertIn("cerebrollm:p%40ss%3Aw%2Frd%231 x@127.0.0.1:54329/rag_local", cfg.async_url)
        self.assertEqual(cfg.pg_connect_args()["password"], SECRET)

    def test_the_label_names_the_variable_and_never_the_password(self):
        with mock.patch.dict(os.environ, {ENV: SECRET}):
            cfg = make(host="localhost", port=54329, password_env=ENV)
        label = cfg.pg_connection_label()
        self.assertIn("password from $" + ENV, label)
        self.assertNotIn(SECRET, label)
        with mock.patch("cerebrollm.store.read_state", lambda c: {}), \
                mock.patch("cerebrollm.store.table_exists", lambda c: False):
            out = status.format_status(cfg, status.collect(cfg))
        self.assertIn("postgres connection: tcp 127.0.0.1:54329  user cerebrollm  password from $" + ENV, out)
        self.assertNotIn(SECRET, out)
        self.assertNotIn("socket folder", out)

    def test_an_ipv6_host_is_bracketed_in_the_url(self):
        self.assertIn("@[::1]:54329/rag_local", make(host="::1", port=54329).sync_url)

    def test_unset_or_empty_variable_is_refused_by_name(self):
        env = {k: v for k, v in os.environ.items() if k != ENV}
        for value in (None, ""):
            with mock.patch.dict(os.environ, env, clear=True):
                if value is not None:
                    os.environ[ENV] = value
                with self.assertRaisesRegex(ValueError, ENV):
                    make(host="127.0.0.1", port=54329, password_env=ENV)

    def test_host_with_socket_dir_is_refused(self):
        data = copy.deepcopy(config.load().data)
        data["postgres"]["host"] = "127.0.0.1"   # socket_dir is still there
        with self.assertRaisesRegex(ValueError, "both set"):
            config.Config(data, Path("test"))

    def test_neither_host_nor_socket_dir_is_refused(self):
        data = copy.deepcopy(config.load().data)
        del data["postgres"]["socket_dir"]
        with self.assertRaisesRegex(ValueError, "socket_dir .* or host"):
            config.Config(data, Path("test"))

    def test_password_env_without_host_is_refused(self):
        data = copy.deepcopy(config.load().data)
        data["postgres"]["password_env"] = ENV
        with self.assertRaisesRegex(ValueError, "password_env applies to a TCP"):
            config.Config(data, Path("test"))

    def test_loopback_hosts_pass_and_are_normalised(self):
        for host, kept in (("127.0.0.1", "127.0.0.1"), ("::1", "::1"), (" 127.0.0.1 ", "127.0.0.1"),
                           ("localhost", "127.0.0.1"), ("LocalHost", "127.0.0.1")):   # localhost is read as 127.0.0.1
            cfg = make(host=host, port=54329)
            self.assertEqual(cfg.pg_host, kept)
            self.assertEqual(cfg.pg_connect_args()["hostaddr"], kept)   # libpq connects to exactly this address

    def test_remote_hosts_are_refused_and_allow_remote_does_not_exist(self):
        for host in ("192.168.1.5", "db.example.com", "127.0.0.1.example.com", "10.0.0.2", "localhost evil", "127.0.0.2", "127.1", "0.0.0.0", "::ffff:127.0.0.1", "[::1]",
                     "127.0.0.1" + chr(10) + "Start it with: rm -rf x"):
            with self.assertRaisesRegex(ValueError, r"postgres\.host = .* is not a loopback address; remote "
                                                    r"databases are not supported in this release"):
                make(host=host, port=54329)
        with self.assertRaisesRegex(ValueError, "remote databases are not supported"):
            make(host="10.0.0.2", port=54329, allow_remote=True)   # no such switch for PostgreSQL

    def test_a_long_host_is_cut_in_the_message(self):
        with self.assertRaises(ValueError) as caught:
            make(host="h" * 500, port=54329)
        self.assertLess(len(str(caught.exception)), 300)

    def test_port_must_be_an_integer_from_1_to_65535(self):
        for port in (54329.5, 0, 65536, -1, "54329", True, None):
            with self.assertRaisesRegex(ValueError, r"postgres\.port"):
                make(host="127.0.0.1", port=port)
        for port in (1, 65535):
            self.assertEqual(make(host="127.0.0.1", port=port).pg_connect_args()["port"], port)

    def test_blank_host_is_refused(self):
        for host in ("", "  ", 5):
            with self.assertRaisesRegex(ValueError, "postgres.host"):
                make(host=host, port=54329)

    def test_mcp_down_message_for_tcp_names_host_and_port_not_pg_ctl(self):
        cfg = make(host="127.0.0.1", port=54329)
        with mock.patch.object(mcp_server, "_config", lambda: cfg):
            out = mcp_server._down_message(psycopg2.OperationalError("connection refused"))
        self.assertIn("Postgres is not reachable at 127.0.0.1:54329", out)
        self.assertIn("docker compose up -d", out)
        self.assertNotIn("pg_ctl", out)
        self.assertNotIn("\n", out)




class TestStalledPeer(unittest.TestCase):
    """A listener that accepts connections and never answers: every TCP path must reach its own driver
    timeout (not fail early on bad arguments) and give up within a bound."""
    LIMIT = 6   # seconds; the timeout is patched to 1

    def setUp(self):
        self.listener = socket.socket()
        self.addCleanup(self.listener.close)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(8)   # the kernel completes the handshake; nothing ever reads or replies
        patch = mock.patch.object(config, "PG_CONNECT_TIMEOUT", 1)
        patch.start()
        self.addCleanup(patch.stop)
        self.cfg = make(host="127.0.0.1", port=self.listener.getsockname()[1])

    def assertTimesOut(self, attempt, exc, diagnostic=None):
        start = time.monotonic()
        with self.assertRaises(exc) as caught:
            attempt()
        elapsed = time.monotonic() - start
        self.assertGreaterEqual(elapsed, 0.8)   # the timeout ran; an argument error would return at once
        self.assertLess(elapsed, self.LIMIT)
        if diagnostic:
            self.assertIn(diagnostic, str(caught.exception))
        self.listener.setblocking(False)
        conn, _ = self.listener.accept()   # the driver really connected to this listener
        conn.close()

    def test_direct_sql(self):
        def attempt():
            with store.sql(self.cfg):
                pass
        self.assertTimesOut(attempt, psycopg2.OperationalError, "timeout expired")

    def test_the_sync_engine(self):
        def attempt():
            with store.tcp_engines(self.cfg)[0].connect():
                pass
        self.assertTimesOut(attempt, SAOperationalError, "timeout expired")

    def test_the_async_engine(self):
        async def connect():
            engine = store.tcp_engines(self.cfg)[1]
            try:
                async with engine.connect():
                    pass
            finally:
                await engine.dispose()
        self.assertTimesOut(lambda: asyncio.run(connect()), TimeoutError)


PG_BIN = Path("/usr/lib/postgresql/16/bin")
EXTENSION_DIR = Path("/usr/share/postgresql/16/extension")   # Debian and Ubuntu layout


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def cluster_problem(pg_bin=PG_BIN, extension_dir=EXTENSION_DIR):
    """Why the live-cluster tests cannot run, or None. It only looks at files, so it cannot raise."""
    if not (pg_bin / "initdb").exists():
        return "PostgreSQL 16 server binaries not found in %s" % pg_bin
    if not (extension_dir / "vector.control").exists():
        return "pgvector is not installed for PostgreSQL 16 (no vector.control in %s)" % extension_dir
    return None


class TestClusterProbe(unittest.TestCase):
    def test_a_machine_without_the_server_or_pgvector_gets_a_reason_not_an_error(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as empty:
            nothing = Path(empty) / "absent"
            self.assertIn("server binaries not found", cluster_problem(pg_bin=nothing, extension_dir=nothing))
            (Path(empty) / "initdb").write_text("")
            self.assertIn("pgvector is not installed", cluster_problem(pg_bin=Path(empty), extension_dir=nothing))
            (Path(empty) / "vector.control").write_text("")
            self.assertIsNone(cluster_problem(pg_bin=Path(empty), extension_dir=Path(empty)))


PROBLEM = cluster_problem()


def candidate_ports(n=5):
    """Fresh free ports, one per start attempt."""
    return (free_port() for _ in range(n))


class Cluster:
    """A throw-away PostgreSQL 16 cluster in a scratch folder: loopback TCP only, password authentication.
    Create it, register close() as a cleanup first, then initdb() and start(). close() stops a running
    server, checks it has exited, and only then removes the folder. Server messages are in English
    (LC_ALL=C) so a port collision can be recognised on any host."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.dir = Path(self.tmp.name)
        self.data = self.dir / "pg"
        self.port = None

    def pg(self, *args, check=False):
        return subprocess.run([str(PG_BIN / args[0])] + list(args[1:]), capture_output=True, text=True,
                              env=dict(os.environ, LC_ALL="C"), check=check)

    def initdb(self):
        pwfile = self.dir / "pw"
        pwfile.write_text(SECRET)
        self.pg("initdb", "-D", str(self.data), "-U", "cerebrollm", "--auth=scram-sha-256",
                "--pwfile=%s" % pwfile, check=True)
        with open(self.data / "postgresql.conf", "a") as f:
            f.write("listen_addresses = '127.0.0.1'" + chr(10) + "unix_socket_directories = ''" + chr(10))

    def start(self, ports):
        """Start on the first port that works. Only a port collision in this attempt's own log moves on to
        the next port (a port that was free a moment ago can be taken before the server binds it); any
        other failure raises."""
        for attempt, port in enumerate(ports):
            log = self.dir / ("server-%d.log" % attempt)
            started = self.pg("pg_ctl", "-D", str(self.data), "-l", str(log), "-w", "start", "-o", "-p %d" % port)
            if started.returncode == 0:
                self.port = port
                return port
            logged = log.read_text(errors="replace") if log.exists() else ""
            if "Address already in use" not in logged:
                raise RuntimeError("pg_ctl start failed on port %s: %s %s %s"
                                   % (port, started.stdout, started.stderr, logged))
        raise RuntimeError("every candidate port was taken")

    def running(self):
        return self.pg("pg_ctl", "-D", str(self.data), "status").returncode == 0

    def close(self):
        if self.running():
            self.pg("pg_ctl", "-D", str(self.data), "-m", "fast", "-w", "stop")
            if self.running():
                raise RuntimeError("test cluster is still running; its folder %s was left in place" % self.dir)
        self.tmp.cleanup()


@unittest.skipIf(PROBLEM, PROBLEM or "")
class TestStartRetry(unittest.TestCase):
    def new_cluster(self):
        cluster = Cluster()
        self.addCleanup(cluster.close)
        cluster.initdb()
        return cluster

    def busy_port(self):
        busy = socket.socket()
        self.addCleanup(busy.close)
        busy.bind(("127.0.0.1", 0))
        busy.listen(1)
        return busy.getsockname()[1]

    def test_a_taken_port_moves_on_to_the_next_candidate(self):
        cluster = self.new_cluster()
        busy, free = self.busy_port(), free_port()
        self.assertEqual(cluster.start(iter([busy, free])), free)
        self.assertTrue(cluster.running())

    def test_only_this_attempts_own_log_decides_a_retry(self):
        cluster = self.new_cluster()
        # attempt 0 collides (its log says so); attempt 1 fails for another reason and must not be retried
        with self.assertRaisesRegex(RuntimeError, "pg_ctl start failed on port 70000"):
            cluster.start(iter([self.busy_port(), 70000, free_port()]))
        self.assertFalse(cluster.running())

    def test_running_out_of_candidates_is_an_error(self):
        cluster = self.new_cluster()
        with self.assertRaisesRegex(RuntimeError, "every candidate port was taken"):
            cluster.start(iter([self.busy_port()]))


@unittest.skipIf(PROBLEM, PROBLEM or "")
class TestAgainstATcpCluster(unittest.TestCase):
    """A real TCP connection with password authentication, on a cluster that exists only for this class."""

    @classmethod
    def setUpClass(cls):
        cls.cluster = Cluster()
        cls.addClassCleanup(cls.cluster.close)   # registered before anything starts
        env = mock.patch.dict(os.environ, {ENV: SECRET})
        env.start()
        cls.addClassCleanup(env.stop)
        cls.cluster.initdb()
        cls.port = cls.cluster.start(candidate_ports())
        cls.cfg = make(host="127.0.0.1", port=cls.port, password_env=ENV, database="postgres")

    def test_sql_connects_over_tcp_with_the_password(self):
        with store.sql(self.cfg) as cur:
            cur.execute("select inet_server_addr()::text, inet_server_port()")
            addr, port = cur.fetchone()
        self.assertEqual((addr, port), ("127.0.0.1/32", self.port))   # NULL on a Unix-socket connection

    def test_client_environment_defaults_cannot_change_the_destination(self):
        # libpq would take the network address from PGHOSTADDR (and host and port from PGHOST, PGPORT) when
        # the connection does not name them; every TCP path must still reach the configured loopback server
        poisoned = {"PGHOSTADDR": "192.0.2.1", "PGHOST": "192.0.2.1", "PGPORT": "9"}
        with mock.patch.dict(os.environ, poisoned), mock.patch.object(config, "PG_CONNECT_TIMEOUT", 3):
            with store.sql(self.cfg) as cur:
                cur.execute("select inet_server_addr()::text")
                self.assertEqual(cur.fetchone()[0], "127.0.0.1/32")
            sync_engine, async_engine = store.tcp_engines(self.cfg)
            with sync_engine.connect() as conn:
                self.assertEqual(conn.execute(text("select inet_server_addr()::text")).scalar(), "127.0.0.1/32")

            async def where():
                async with async_engine.connect() as conn:
                    return (await conn.execute(text("select inet_server_addr()::text"))).scalar()
            self.assertEqual(asyncio.run(where()), "127.0.0.1/32")

    def test_a_wrong_password_is_refused(self):
        with mock.patch.dict(os.environ, {ENV: "not-the-password"}):
            wrong = make(host="127.0.0.1", port=self.port, password_env=ENV, database="postgres")
            with self.assertRaises(psycopg2.OperationalError):
                with store.sql(wrong):
                    pass

    def test_the_vector_store_and_the_async_url_connect(self):
        table = "tcp_unit_test"
        cfg = make(host="127.0.0.1", port=self.port, password_env=ENV, database="postgres", table=table)
        try:
            node = TextNode(text="tcp check", embedding=[0.5] * cfg.pg["embed_dim"])
            # creates the vector extension and the tables, then inserts, through the SQLAlchemy URL; the
            # cluster's user is a superuser, as POSTGRES_USER is in the Docker image
            store.vector_store(cfg).add([node])
            self.assertTrue(store.table_exists(cfg))
            self.assertEqual(store.row_count(cfg, cfg.data_table), 1)

            async def ask():
                _, engine = store.tcp_engines(cfg)   # the async engine the vector store uses, with its timeout
                try:
                    async with engine.connect() as conn:
                        return (await conn.execute(text("select 41 + 1"))).scalar()
                finally:
                    await engine.dispose()
            self.assertEqual(asyncio.run(ask()), 42)
        finally:
            store.drop_table(cfg, cfg.data_table)
            self.assertFalse(store.table_exists(cfg))

    def test_database_identity_names_the_cluster_and_the_database(self):
        identity = store.database_identity(self.cfg)
        system_id, name = identity.split("/")
        self.assertTrue(system_id.isdigit())
        self.assertEqual(name, "postgres")

    def test_changed_index_is_refused_on_an_empty_database_with_a_foreign_state_folder(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            root, state = Path(tmp) / "corpus", Path(tmp) / "state"
            root.mkdir()
            (root / "a.md").write_text("# A\n\nsome text\n")
            cfg = make(state_dir=state, host="127.0.0.1", port=self.port, password_env=ENV, database="postgres",
                       table="state_guard_test")
            cfg.roots = {"fx": {"name": "fx", "kind": "dir", "path": str(root), "ref": "file"}}
            cfg.rules = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"}]
            state.mkdir()
            SimpleDocumentStore().persist(str(cfg.docstore_path))   # hashes written for another database
            with self.assertRaisesRegex(SystemExit, "refusing --changed"):
                indexer.run_index(cfg, changed=True)
            self.assertFalse(store.table_exists(cfg))   # nothing was written


class TestStateMatchesDatabase(unittest.TestCase):
    """indexer.check_state_matches_database with the database replaced by fakes."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.cfg = make(state_dir=self.tmp.name)

    def check(self, docstore, stored, live, rows):
        if docstore:
            SimpleDocumentStore().persist(str(self.cfg.docstore_path))
        with mock.patch.object(store, "read_state", lambda c: {"database_identity": stored} if stored else {}), \
                mock.patch.object(store, "database_identity", lambda c: live), \
                mock.patch.object(store, "row_count", lambda c, t: rows):
            indexer.check_state_matches_database(self.cfg)

    def test_a_state_folder_written_for_another_database_is_refused(self):
        with self.assertRaisesRegex(SystemExit, "full `cerebrollm index`.*own state_dir"):
            self.check(docstore=True, stored="1/rag_local", live="2/rag_local", rows=40)

    def test_an_empty_database_with_a_docstore_is_refused(self):
        with self.assertRaisesRegex(SystemExit, "refusing --changed"):
            self.check(docstore=True, stored="1/rag_local", live="1/rag_local", rows=0)
        with self.assertRaisesRegex(SystemExit, "refusing --changed"):
            self.check(docstore=True, stored=None, live="1/rag_local", rows=0)   # a state folder from before identities

    def test_a_matching_or_unidentified_database_with_rows_passes(self):
        self.check(docstore=True, stored="1/rag_local", live="1/rag_local", rows=40)
        self.check(docstore=True, stored=None, live="1/rag_local", rows=40)   # older state.json: nothing to compare
        self.check(docstore=True, stored="1/rag_local", live=None, rows=40)   # the server hides its identity

    def test_no_docstore_means_nothing_to_check(self):
        self.check(docstore=False, stored="1/x", live="2/x", rows=0)


if __name__ == "__main__":
    unittest.main()
