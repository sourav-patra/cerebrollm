"""cerebrollm status."""
import os
import stat

from . import rules, store


def socket_dir_mode(path):
    """The permission bits of the Postgres socket folder as '0700', or 'missing', 'unreadable', or
    'not checked on Windows' (os.stat reports no real permission bits there)."""
    if os.name == "nt":
        return "not checked on Windows"
    try:
        return "%04o" % stat.S_IMODE(os.stat(path).st_mode)
    except (FileNotFoundError, NotADirectoryError):
        return "missing"
    except PermissionError:
        return "unreadable"


def socket_dir_open(mode):
    """True when a group or other bit is set: another local user can reach the database socket."""
    return mode.isdigit() and int(mode, 8) & 0o077 != 0


def collect(cfg):
    st = store.read_state(cfg)
    out = {"state": st, "tiers": [], "never_violations": None, "chunks": 0, "documents": 0,
           "num_ctx": cfg.ollama_options["num_ctx"], "socket_mode": socket_dir_mode(cfg.pg["socket_dir"])}
    if not store.table_exists(cfg):
        return out
    with store.sql(cfg) as cur:
        cur.execute("select metadata_->>'tier', metadata_->>'status', count(*), "
                    "count(distinct metadata_->>'ref_doc_id') from %s group by 1, 2 order by 1, 2"
                    % cfg.data_table)
        out["tiers"] = [list(r) for r in cur.fetchall()]
        cur.execute("select distinct metadata_->>'path' from %s" % cfg.data_table)
        paths = [r[0] for r in cur.fetchall()]
    out["chunks"] = sum(r[2] for r in out["tiers"])
    out["documents"] = sum(r[3] for r in out["tiers"])
    out["never_violations"] = sum(1 for p in paths if rules.never_reason(p, cfg.never))
    return out


def format_status(cfg, s):
    st = s["state"]
    last = st.get("last_index", {})
    lines = ["cerebrollm status  domain=%s  table=%s" % (cfg.domain, cfg.table),
             "documents %d  chunks %d" % (s["documents"], s["chunks"]),
             "%-4s %-11s %9s %7s" % ("tier", "status", "documents", "chunks")]
    for tier, status, chunks, docs in s["tiers"]:
        lines.append("%-4s %-11s %9d %7d" % (tier, status, docs, chunks))
    lines.append("indexed from never-index paths: %s" % s["never_violations"])
    lines.append("skipped by rule: %d  %s" % (sum(last.get("skipped_rule", {}).values()),
                                              last.get("skipped_rule", {})))
    lines.append("skipped by secret scan: %d" % len(last.get("skipped_secret", [])))
    lines.append("files seen %s  matched no tier rule %s  duplicate paths collapsed %s" % (
        last.get("files_seen"), last.get("no_rule"), last.get("duplicates_collapsed")))
    lines.append("last index: %s  mode=%s  duration=%ss  chunks embedded=%s" % (
        st.get("last_index_time"), last.get("mode"), last.get("duration_s"), last.get("chunks_embedded")))
    lines.append("embedding model: %s  digest: %s  num_ctx: %s" % (
        st.get("embedding_model"), st.get("embedding_digest"), s["num_ctx"]))
    lines.append("postgres socket folder: %s  mode %s" % (cfg.pg["socket_dir"], s["socket_mode"]))
    if socket_dir_open(s["socket_mode"]):
        lines.append("WARNING: other local users can reach the database socket; run: chmod 700 %s" % cfg.pg["socket_dir"])
    return "\n".join(lines)
