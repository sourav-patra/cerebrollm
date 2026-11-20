#!/usr/bin/env python3
"""Write a cerebrollm config that indexes the saved sources of an item set into a corpus, table and state folder of
its own. Stdlib only.

The shipped engine/cerebrollm.toml indexes one corpus folder into one table. A benchmark must not write into that
corpus or replace that table, so the config written here is the shipped one with four changes for the set NAME:
the corpus root is $HOME/cerebrollm-corpus-NAME, the table is chunks_NAME, the state folder is
$HOME/.cerebrollm/NAME, and one tier rule is added for each top-level folder of the set's sources folder that has no
rule yet (the shipped file has rules only for the v2 folders).

Usage: python3 eval/itemset_config.py NAME OUT [--force]   (NAME as in eval/itemset-NAME.toml, for example v3)
OUT must be under this repository or under $HOME/.cerebrollm. An existing OUT is not replaced without --force; the
file is written to a new temporary file beside OUT and installed with one atomic step.
Then set CEREBROLLM_CONFIG=OUT for `index` and for every run of `run_v2.py --set NAME`; see eval/ITEMS-v3.md.
"""
import os
import re
import sys
import tempfile
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import itemset as IS  # noqa: E402

ENGINE_CONFIG = os.path.join(HERE, "..", "engine", "cerebrollm.toml")
FOLDER_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")   # goes unescaped into a TOML string and a glob
RULE = '\n[[rule]]\nroot = "notes"\nglob = "%s/**/*.md"\ntier = "T3"\nstatus = "current"\n'


def folders(itemset):
    """The top-level folders of the set's sources. Raises ValueError for a name other than letters, digits, '.', '_'
    and '-' (not starting with '.', '_' or '-'), which the generated rule could not hold as it is."""
    names = sorted(d for d in os.listdir(itemset.sources) if os.path.isdir(os.path.join(itemset.sources, d)))
    bad = [d for d in names if not FOLDER_NAME.match(d)]
    if bad:
        raise ValueError("source folder names may hold only letters, digits, '.', '_' and '-': %s"
                         % ", ".join(repr(d) for d in bad))
    return names


def corpus_name(itemset):
    return "cerebrollm-corpus-" + itemset.name


def config_text(itemset, base=None):
    """The shipped config with the corpus root, table and state folder of the set, and one rule for each source folder
    that has none. Rules are checked in order and the first match wins. Raises ValueError when the shipped file no
    longer has the lines this replaces."""
    if base is None:
        with open(ENGINE_CONFIG, encoding="utf-8") as f:   # universal newlines
            base = f.read()
    text = base if base.endswith("\n") else base + "\n"
    for old, new in (('state_dir = "$HOME/.cerebrollm"', 'state_dir = "$HOME/.cerebrollm/%s"' % itemset.name),
                     ('table = "chunks"', 'table = "chunks_%s"' % itemset.name),
                     ('path = "$HOME/cerebrollm-corpus"', 'path = "$HOME/%s"' % corpus_name(itemset))):
        if text.count(old) != 1:
            raise ValueError("the shipped config no longer has exactly one line starting %r" % old)
        text = text.replace(old, new)
    for d in folders(itemset):
        if 'glob = "%s/**/*.md"' % d not in base:
            text += RULE % d
    return text


def default_roots():
    return [os.path.realpath(os.path.join(HERE, "..")), os.path.realpath(os.path.expanduser("~/.cerebrollm"))]


def inside(path, root):
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:   # another drive
        return False


def write_config(itemset, out, force=False, roots=None):
    """Write config_text to `out`: refuse a destination outside `roots` (default: this repository and
    $HOME/.cerebrollm), build the whole text first and parse it, write it to a temporary file created exclusively
    beside `out`, and install it with one atomic step: a hard link, which fails when `out` exists, or with force a
    rename over it. A failure leaves an existing `out` as it was and no temporary file."""
    folder = os.path.realpath(os.path.dirname(os.path.abspath(out)))
    dest = os.path.join(folder, os.path.basename(out))
    if not any(inside(dest, r) for r in (roots if roots is not None else default_roots())):
        raise ValueError("%s is outside the permitted folders (this repository and $HOME/.cerebrollm)" % out)
    if not os.path.isdir(folder):
        raise ValueError("folder %s does not exist" % folder)
    text = config_text(itemset)
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ValueError("the generated config is not valid TOML (%s); nothing written" % e) from None
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".itemset-config-")   # created with O_EXCL
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.chmod(tmp, 0o644)
        if force:
            os.replace(tmp, dest)
        else:
            os.link(tmp, dest)   # fails with FileExistsError when dest exists, also when it appeared a moment ago
    except FileExistsError:
        raise FileExistsError("%s exists; pass --force to replace it" % out) from None
    finally:
        if os.path.lexists(tmp):
            os.remove(tmp)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    force = "--force" in argv
    argv = [a for a in argv if a != "--force"]
    if len(argv) != 2:
        print(__doc__)
        return 2
    itemset = IS.load(argv[0])
    try:
        write_config(itemset, argv[1], force)
    except (OSError, ValueError) as e:
        print("not written: %s" % e)
        return 1
    print("wrote %s: corpus ~/%s, table chunks_%s, state ~/.cerebrollm/%s, rules for: %s"
          % (argv[1], corpus_name(itemset), itemset.name, itemset.name, ", ".join(folders(itemset))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
