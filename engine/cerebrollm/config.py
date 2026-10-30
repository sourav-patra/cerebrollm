"""Load cerebrollm.toml and derive connection strings and paths."""
import os
import sys
import tomllib
from pathlib import Path


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
        self.ollama_options = {"num_ctx": int(self.ollama["num_ctx"])}   # sent to Ollama with each embed call
        self.chunking = data["chunking"]
        self.search = data["search"]
        self.synonyms = data.get("synonyms", {})   # abbreviation -> phrase, both ways, lexical arm only
        self.roots = {r["name"]: r for r in data["root"]}
        self.rules = data["rule"]
        self.never = data["never"]
        self.project_names = data.get("project_names", {})
        self.default_year = data.get("supersession_default_year", 2026)
        base = "@/%s?host=%s&port=%s" % (self.pg["database"], self.pg["socket_dir"], self.pg["port"])
        self.sync_url = "postgresql+psycopg2://%s%s" % (self.pg["user"], base)
        self.async_url = "postgresql+asyncpg://%s%s" % (self.pg["user"], base)

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
