"""Command line: cerebrollm index | search | ask | verify | status | mcp."""
import argparse
import json
import sys

from . import __version__, config


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cerebrollm", description=__doc__)
    ap.add_argument("--config", help="path to cerebrollm.toml")
    ap.add_argument("--version", action="version", version="cerebrollm " + __version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("index", help="build or update the index")
    p.add_argument("--changed", action="store_true", help="re-embed only changed files; keep the rest")

    p = sub.add_parser("search", help="search the index")
    p.add_argument("query")
    p.add_argument("--k", type=int)
    p.add_argument("--mode", choices=["lexical", "vector", "hybrid"])
    p.add_argument("--all-status", action="store_true", help="include draft and superseded; no tier boost")
    p.add_argument("--project")
    p.add_argument("--synonyms", action="store_true", default=None, help="apply the [synonyms] table to the lexical arm (off by default)")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("ask", help="answer a question from the index; print it only if a citation verifies")
    p.add_argument("question")
    p.add_argument("--model", default="gpt-oss:20b", help="generator (an allowed chat model in models.toml)")
    p.add_argument("--think", choices=["low", "medium", "high", "off"], help="thinking level sent to Ollama")
    p.add_argument("--no-rerank", action="store_true", help="skip the reranker: the generator gets the search top 8")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("verify", help="check a quote against the source and the indexed sha256")
    p.add_argument("path")
    p.add_argument("quote")
    p.add_argument("--ref")

    p = sub.add_parser("status", help="counts, skips, last index")
    p.add_argument("--json", action="store_true")

    sub.add_parser("mcp", help="serve search and verify over MCP on stdio (read-only)")

    args = ap.parse_args(argv)
    cfg = config.load(args.config)

    if args.cmd == "index":
        from .indexer import run_index
        print(json.dumps(run_index(cfg, changed=args.changed), indent=2))
    elif args.cmd == "search":
        from . import search
        results = search.run_search(cfg, args.query, args.k, args.mode, args.all_status, args.project, args.synonyms)
        results = search.cap_text(results, cfg.search["token_budget"])
        print(search.to_json(results) if args.json else search.format_hits(results))
    elif args.cmd == "ask":
        from . import answer
        try:
            res = answer.ask(cfg, args.question, args.model, args.think, not args.no_rerank)
        except Exception as exc:  # noqa: BLE001 - a failed run must never look like an answer
            print("cerebrollm ask failed: %s: %s" % (type(exc).__name__, " ".join(str(exc).split())[:300]),
                  file=sys.stderr)
            return 2
        print(answer.to_json(res) if args.json else answer.format_result(res))
    elif args.cmd == "verify":
        from .verify import run_verify
        code, detail = run_verify(cfg, args.path, args.quote, args.ref)
        print("%s  %s" % (code, detail))
        return 0 if code == "OK" else 1
    elif args.cmd == "status":
        from . import status
        s = status.collect(cfg)
        print(json.dumps(s, indent=2) if args.json else status.format_status(cfg, s))
    elif args.cmd == "mcp":
        from . import mcp_server
        mcp_server.run(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
