"""Load cerebrollm.toml and derive connection strings and paths."""
import os
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy.engine import URL


def data_file(name):
    """cerebrollm.toml and models.toml: beside the package in a source checkout, else <prefix>/share/cerebrollm (wheel).
    shortcut: sys.prefix only, so a wheel installed with --user or --target needs --config / CEREBROLLM_CONFIG."""
    here = Path(__file__).resolve().parent.parent / name
    return here if here.exists() else Path(sys.prefix) / "share" / "cerebrollm" / name


DEFAULT_CONFIG = data_file("cerebrollm.toml")


class Config:
    def __init__(self, data, path):
        self.data = data
        self.path = path
        self.domain = data["domain"]
        self.state_dir = Path(os.path.expanduser(data["state_dir"]))
        self.pg = data["postgres"]
        self.ollama = data["ollama"]
        check_ollama_url(self.ollama)
        self.ollama_options = {"num_ctx": int(self.ollama["num_ctx"])}   # sent to Ollama with each embed call
        self.chunking = data["chunking"]
        self.search = data["search"]
        self.synonyms = data.get("synonyms", {})   # abbreviation -> phrase, both ways, lexical arm only
        self.roots = {r["name"]: r for r in data["root"]}
        for name in self.roots:   # also_at keys are "root:path", so a colon in a name would make them ambiguous
            if ":" in name:
                raise ValueError("root name must not contain ':': %r" % name)
        self.rules = data["rule"]
        self.never = data["never"]
        self.project_names = data.get("project_names", {})
        self.default_year = data.get("supersession_default_year", 2026)
        self.pg_host = check_postgres(self.pg)
        self.pg_password = postgres_password(self.pg)
        if self.pg_host is None:   # Unix socket: the default
            base = "@/%s?host=%s&port=%s" % (self.pg["database"], self.pg["socket_dir"], self.pg["port"])
            self.sync_url = "postgresql+psycopg2://%s%s" % (self.pg["user"], base)
            self.async_url = "postgresql+asyncpg://%s%s" % (self.pg["user"], base)
        else:
            self.sync_url = self._tcp_url("postgresql+psycopg2")
            self.async_url = self._tcp_url("postgresql+asyncpg")

    def _tcp_url(self, driver):
        url = URL.create(driver, username=self.pg["user"], password=self.pg_password, host=self.pg_host,
                         port=self.pg["port"], database=self.pg["database"])
        return url.render_as_string(hide_password=False)   # the password is percent-encoded; the URL is never printed

    def pg_connect_args(self):
        """Keyword arguments for psycopg2.connect: the socket folder as host, or the TCP host and password."""
        args = {"host": self.pg_host or self.pg["socket_dir"], "port": self.pg["port"],
                "dbname": self.pg["database"], "user": self.pg["user"]}
        if self.pg_host is not None:
            # hostaddr makes libpq connect to exactly this numeric address; without it PGHOSTADDR or a
            # name lookup could pick the destination
            args["hostaddr"] = self.pg_host
            args["connect_timeout"] = PG_CONNECT_TIMEOUT   # a peer that accepts and then stalls must not hang a command
        if self.pg_password is not None:
            args["password"] = self.pg_password
        return args

    def pg_connection_label(self):
        """One line for `status`: which connection the engine uses. Never contains the password."""
        if self.pg_host is None:
            return "postgres connection: unix socket"
        env = self.pg.get("password_env")
        auth = "password from $%s" % env if env else "no password"
        return "postgres connection: tcp %s:%s  user %s  %s" % (self.pg_host, self.pg["port"], self.pg["user"], auth)

    def pg_down_hint(self):
        """The data directory of the socket-based cluster, from which the 'Postgres is not reachable'
        message builds its pg_ctl command; None for TCP, where the engine does not know how the server
        was started."""
        return None if self.pg_host is not None else self.pg["socket_dir"].rsplit("/", 1)[0]

    @property
    def table(self):
        return self.pg["table"]

    @property
    def data_table(self):
        return "data_" + self.pg["table"]   # PGVectorStore prefixes its table name

    @property
    def next_table(self):
        return self.pg["table"] + "_next"   # a full rebuild fills this table, then swaps it in

    @property
    def next_data_table(self):
        return "data_" + self.next_table

    @property
    def docstore_path(self):
        return self.state_dir / "docstore.json"

    @property
    def next_docstore_path(self):
        return self.state_dir / "docstore.next.json"

    @property
    def state_path(self):
        return self.state_dir / "state.json"

    def project_for(self, root, rel_path):
        if root["kind"] == "git":
            return root["project"]
        top = rel_path.split("/", 1)[0]
        return self.project_names.get(top, top.lower().replace(" ", "-"))


def check_postgres(pg):
    """The [postgres] connection mode: the TCP host when `host` is set, None for the Unix socket
    (`socket_dir`, the default). Exactly one of the two must be given; password_env needs host. A TCP
    host must be the IP literal 127.0.0.1 or ::1 (`localhost` is read as 127.0.0.1, so no name lookup
    decides the destination) and the port an integer from 1 to 65535: remote databases are not supported
    in this release (the connection has no sslmode setting). Returns the numeric address to connect to."""
    host = pg.get("host")
    if host is not None:
        address = PG_LOOPBACK.get(host.strip().lower()) if isinstance(host, str) else None
        if address is None:
            raise ValueError("postgres.host = %.60r is not a loopback address; remote databases are not "
                             "supported in this release. Use 127.0.0.1 or ::1" % (host,))
        if "socket_dir" in pg:
            raise ValueError("postgres.host and postgres.socket_dir are both set; keep one: host for TCP, "
                             "socket_dir for the Unix socket")
        port = pg.get("port")
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ValueError("postgres.port = %.20r must be an integer from 1 to 65535" % (port,))
        return address
    if "socket_dir" not in pg:
        raise ValueError("[postgres] needs socket_dir (Unix socket) or host (TCP)")
    if "password_env" in pg:
        raise ValueError("postgres.password_env applies to a TCP connection; set postgres.host as well")
    return None


def postgres_password(pg):
    """The password from the environment variable named by postgres.password_env, or None when that key
    is not set. The file holds the variable's name only; a missing or empty variable is refused by name."""
    env = pg.get("password_env")
    if env is None:
        return None
    if not isinstance(env, str) or not env:
        raise ValueError("postgres.password_env must be the name of an environment variable, got %r" % (env,))
    value = os.environ.get(env)
    if not value:
        raise ValueError("postgres.password_env names %s, which is not set (or empty); export it before "
                         "running cerebrollm" % env)
    return value


LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
PG_LOOPBACK = {"127.0.0.1": "127.0.0.1", "::1": "::1", "localhost": "127.0.0.1"}   # host as written -> address connected to
PG_CONNECT_TIMEOUT = 10   # seconds, for a PostgreSQL TCP connection (psycopg2 and asyncpg)


def check_ollama_url(ollama):
    """Refuse an Ollama base_url off this machine unless [ollama] allow_remote = true: documents and
    questions are sent to it."""
    host = urlsplit(ollama["base_url"]).hostname
    if host not in LOOPBACK_HOSTS and ollama.get("allow_remote") is not True:
        raise ValueError("ollama.base_url = %r is not a loopback address; documents and questions would leave "
                         "this machine. Use 127.0.0.1, or set allow_remote = true in [ollama] to allow it"
                         % ollama["base_url"])


PATH_KEYS = {"state_dir", "socket_dir", "path"}


def expand_paths(node, where=""):
    """Expand ~ and $VARS in path-valued keys; refuse a value whose variable is unset."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = "%s.%s" % (where, key) if where else key
            if key in PATH_KEYS and isinstance(value, str):
                expanded = os.path.expanduser(os.path.expandvars(value))
                if "$" in expanded:
                    raise ValueError("%s = %r uses an unset environment variable; set it or edit "
                                     "cerebrollm.toml" % (here, value))
                node[key] = expanded
            else:
                expand_paths(value, here)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            expand_paths(item, "%s[%d]" % (where, i))
    return node


def load(path=None):
    path = Path(path or os.environ.get("CEREBROLLM_CONFIG") or DEFAULT_CONFIG)
    with open(path, "rb") as f:
        return Config(expand_paths(tomllib.load(f)), path)
