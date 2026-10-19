"""Plyń base typography (plyn-standard norms/typography.md): one permitted form for each problematic character in prose.
  dash            U+2014, U+2015 -> U+2013 (–); between two words written without spaces it gets spaces (word – word),
                  between digits it stays closed (2026–2027)
  double quotes   « » “ ” „ ‟ -> "
  single quotes   ‘ ’ ‚ ‛ ‹ › -> '
Only prose files are touched (.md, .markdown, .txt); inside them code blocks, inline code and front matter keep
their characters. Code files are left as they are.

A project outside Plyń may set its own rules in typography.yaml at its root:
  dash: em | keep      leave dashes as written
  quotes: keep         leave quotation marks and apostrophes as written
  hook: <path>         the project's own commit hook, run after this one (by A-Rozum/plyn tools/hooks/pre-commit)

    python plyn_typography.py <repo> [paths…]   default: files staged in <repo> (git diff --cached)
Prints the files it changed. Applied at every commit by the hook that A-Rozum/plyn tools/setup.sh installs, and on
every landing by plyn_land.py and workflows/land.yml."""
import pathlib, re, subprocess, sys

PROSE = {".md", ".markdown", ".txt"}
BETWEEN = re.compile(r"(?<=[^\W\d])[\u2014\u2015](?=[^\W\d])")
DASH = re.compile("[\u2014\u2015]")
DOUBLE = re.compile("[\u00ab\u00bb\u201c\u201d\u201e\u201f]")
SINGLE = re.compile("[\u2018\u2019\u201a\u201b\u2039\u203a]")
CODE = re.compile(r"\A---\n.*?\n---[ \t]*$|^[ \t]*(```|~~~)[^\n]*\n.*?^[ \t]*\1[^\n]*$|`[^`\n]+`", re.M | re.S)

def settings(repo):
    f = pathlib.Path(repo) / "typography.yaml"
    text = f.read_text(encoding="utf-8") if f.exists() else ""
    get = lambda key: (re.search(rf"^{key}:\s*['\"]?([^'\"\s#]+)", text, re.M) or [None, ""])[1]
    return {"dash": get("dash") not in ("em", "keep"), "quotes": get("quotes") != "keep", "hook": get("hook")}

def house(text, dash=True, quotes=True):
    def fix(s):
        if dash: s = DASH.sub("\u2013", BETWEEN.sub(" \u2013 ", s))
        if quotes: s = SINGLE.sub("'", DOUBLE.sub('"', s))
        return s
    out, last = [], 0
    for m in CODE.finditer(text):
        out.append(fix(text[last:m.start()])); out.append(m.group(0)); last = m.end()
    out.append(fix(text[last:]))
    return "".join(out)

def opted_out(repo):
    s = settings(repo)
    return not (s["dash"] or s["quotes"])

def staged(repo):
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=AM"], cwd=repo, capture_output=True, text=True).stdout
    return [p for p in out.splitlines() if p]

def apply(repo, paths=None):
    repo = pathlib.Path(repo)
    s = settings(repo)
    if not (s["dash"] or s["quotes"]): return []
    changed = []
    for rel in staged(repo) if paths is None else paths:
        if pathlib.PurePath(rel).suffix.lower() not in PROSE: continue
        p = repo / rel
        try: text = p.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError): continue
        new = house(text, s["dash"], s["quotes"])
        if new != text:
            p.write_bytes(new.encode("utf-8")); changed.append(rel)
    return changed

if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    changed = apply(repo, sys.argv[2:] or None)
    if changed: print("Base typography set in: " + ", ".join(changed))
