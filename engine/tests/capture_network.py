"""Network capture check (LLD I-09): run cerebrollm commands and list every address they connect to.

    python tests/capture_network.py OUT.txt -- index --changed
    python tests/capture_network.py OUT.txt -- search "a question"
    python tests/capture_network.py OUT.txt -- ask "a question"

A Python audit hook records each socket.connect and socket.getaddrinfo (httpx, the Ollama client, asyncpg,
Hugging Face). Appends the distinct addresses to OUT.txt and exits 1 if any is off this machine.
shortcut: libpq (psycopg2) connects in C and is not seen; its target is the Unix socket set in
cerebrollm.toml. Use `strace -f -e trace=connect` where it is installed to cover C code too.
Needs live PostgreSQL and Ollama, so CI does not run it."""
import ipaddress
import os
import sys

LOCAL_NAMES = {"localhost"}


def is_local(addr):
    if isinstance(addr, (str, bytes)):   # AF_UNIX path
        return True
    host = addr[0]
    if host in LOCAL_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False   # a host name that needs DNS


def describe(addr):
    if isinstance(addr, (str, bytes)):   # home folder written as ~ so a saved capture names no user
        path = addr.decode() if isinstance(addr, bytes) else addr
        return "unix:" + path.replace(os.path.expanduser("~"), "~", 1)
    return "%s:%s" % (addr[0], addr[1])


def main(argv):
    out, sep, cmd = argv[0], argv[1], argv[2:]
    assert sep == "--" and cmd, __doc__
    seen = {}

    def hook(event, args):
        if event == "socket.connect":
            seen.setdefault(describe(args[1]), is_local(args[1]))
        elif event == "socket.getaddrinfo":
            seen.setdefault("lookup:%s" % args[0], is_local((args[0], args[1])))

    sys.addaudithook(hook)
    from cerebrollm import cli
    rc = cli.main(cmd)
    bad = sorted(a for a, ok in seen.items() if not ok)
    with open(out, "a", encoding="utf-8") as f:
        f.write("$ cerebrollm %s  (exit %s)\n" % (" ".join(cmd), rc))
        for a in sorted(seen):
            f.write("  %s %s\n" % ("local " if seen[a] else "REMOTE", a))
        f.write("  result: %s\n" % ("FAIL, off-machine: %s" % bad if bad else "only loopback and Unix sockets"))
    return 1 if bad else 0


def _self_check():
    assert is_local("/home/u/.cerebrollm/pg16/sock/.s.PGSQL.54329") and is_local(("127.0.0.1", 11434))
    assert is_local(("::1", 11434)) and is_local(("localhost", 11434))
    assert not is_local(("10.0.0.5", 11434)) and not is_local(("huggingface.co", 443))


if __name__ == "__main__":
    _self_check()
    sys.exit(main(sys.argv[1:]))
