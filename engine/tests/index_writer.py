"""Subprocess entry for test_index_lock: runs the real `cerebrollm` command line with no Ollama.

    python -m tests.index_writer CONFIG_JSON index [--changed]
    python -m tests.index_writer CONFIG_JSON search QUERY [search flags]

CONFIG_JSON holds the config data as test_index_lock builds it. The embedding model is replaced by a
fixed-vector MockEmbedding of the configured embed_dim and the model digest by a constant, so no model is
called. When the environment variable INDEX_HOLD_DIR is set, the first embed call of the run creates
INDEX_HOLD_DIR/inside and waits until INDEX_HOLD_DIR/release exists, so the test knows this run is inside
the index writer locks while it starts a second one. When INDEX_IDLE_TIMEOUT_MS is set, every connection
opened through store.connect starts with that idle_session_timeout, as a server, database or role default
would give it."""
import json
import os
import sys
import time
from pathlib import Path
from unittest import mock

import psycopg2
from llama_index.core.embeddings import MockEmbedding

from cerebrollm import cli, config

HOLD_SECONDS = 120


class HeldEmbedding(MockEmbedding):
    def _get_text_embeddings(self, texts):
        hold = os.environ.get("INDEX_HOLD_DIR")
        if hold and not (Path(hold) / "inside").exists():
            (Path(hold) / "inside").write_text(str(os.getpid()))
            deadline = time.time() + HOLD_SECONDS
            while not (Path(hold) / "release").exists():
                if time.time() > deadline:
                    raise RuntimeError("index_writer: no release file after %d s" % HOLD_SECONDS)
                time.sleep(0.05)
        return super()._get_text_embeddings(texts)


def connect_with_idle_timeout(cfg):
    return psycopg2.connect(host=cfg.pg["socket_dir"], port=cfg.pg["port"], dbname=cfg.pg["database"],
                            user=cfg.pg["user"],
                            options="-c idle_session_timeout=%s" % os.environ["INDEX_IDLE_TIMEOUT_MS"])


def main(argv):
    data = json.loads(Path(argv[0]).read_text())
    cfg = config.Config(data, Path(argv[0]))
    with mock.patch("cerebrollm.config.load", lambda path=None: cfg), \
            mock.patch("cerebrollm.store.embed_model", lambda c: HeldEmbedding(embed_dim=c.pg["embed_dim"])), \
            mock.patch("cerebrollm.store.model_digest", lambda c: "test-digest"):
        if os.environ.get("INDEX_IDLE_TIMEOUT_MS"):
            with mock.patch("cerebrollm.store.connect", connect_with_idle_timeout):
                return cli.main(argv[1:])
        return cli.main(argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
