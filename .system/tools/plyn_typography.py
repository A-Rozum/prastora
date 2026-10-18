"""House typography (norms/typography.md): the dash is U+2013 (–). Rewrites U+2014 and U+2015 in text files;
a long dash written between two words without spaces gets spaces (word – word); between digits it stays closed (2026–2027).
A project whose owner chose another dash has typography.yaml at its root with `dash: em`; its files stay as they are.

    python plyn_typography.py <repo> [paths…]   default: files staged in <repo> (git diff --cached)
Exit code 0; prints the files it changed. land (plyn_land.py, workflows/land.yml) runs it on every landing."""
import pathlib, re, subprocess, sys

LONG = "\u2014\u2015"
BETWEEN = re.compile(r"(?<=[^\W\d])[" + LONG + r"](?=[^\W\d])")  # between letters; digits keep a closed range (2026–2027)
ANY = re.compile("[" + LONG + "]")

def house(text):
    return ANY.sub("\u2013", BETWEEN.sub(" \u2013 ", text))

def opted_out(repo):
    f = pathlib.Path(repo) / "typography.yaml"
    return f.exists() and re.search(r"^\s*dash:\s*em\b", f.read_text(encoding="utf-8"), re.M) is not None

def apply(repo, paths=None):
    repo = pathlib.Path(repo)
    if opted_out(repo): return []
    if paths is None:
        out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=AM"], cwd=repo, capture_output=True, text=True).stdout
        paths = [p for p in out.splitlines() if p]
    changed = []
    for rel in paths:
        p = repo / rel
        try: text = p.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError): continue
        new = house(text)
        if new != text:
            p.write_bytes(new.encode("utf-8")); changed.append(rel)
    return changed

if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    changed = apply(repo, sys.argv[2:] or None)
    if changed: print("House dash set in: " + ", ".join(changed))
