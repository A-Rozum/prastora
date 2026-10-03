"""Reader-mode check: runs Mozilla Readability (the library behind Firefox Reader View) on pages and reports
what it extracts as the main content. If the title or the opening text is wrong here, reader modes and
content-hungry crawlers are likely to get it wrong too. Other browsers use their own heuristics, so treat
this as a strong hint, not a guarantee. Needs: pip install playwright && playwright install chromium

  python3 tools/reader.py                          # all pages, one line each
  python3 tools/reader.py templates/product --show # also writes .snap/reader/<page>.html to open in a browser
"""
import functools, http.server, json, sys, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = (Path(__file__).parent / "vendor" / "Readability.js").read_text(encoding="utf-8")
PARSE = ";(() => { const a = new Readability(document.cloneNode(true)).parse(); if (!a) return null;" \
        " const t = a.textContent.replace(/\\s+/g, ' ').trim();" \
        " return {title: a.title, words: t ? t.split(' ').length : 0, start: t.slice(0, 100), html: a.content}; })()"


def pages(args):
    if args:
        return [a if a.endswith(".html") else a + ".html" for a in args]
    found = sorted(ROOT.rglob("*.html"))
    return [p.relative_to(ROOT).as_posix() for p in found if not {".git", ".snap", "tools"} & set(p.relative_to(ROOT).parts)]


def main():
    from playwright.sync_api import sync_playwright
    show = "--show" in sys.argv
    names = pages([a for a in sys.argv[1:] if a != "--show"])

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(("localhost", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        tab = browser.new_page()
        for name in names:
            tab.goto(f"http://localhost:{server.server_port}/{name}")
            result = tab.evaluate(LIB + PARSE)
            if not result:
                print(f"{name}: NOTHING EXTRACTED")
                continue
            print(f"{name}: \"{result['title']}\", {result['words']} words – {result['start']}")
            if show:
                out = ROOT / ".snap" / "reader" / name
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(f"<meta charset=utf-8><title>{result['title']}</title><h1>{result['title']}</h1>{result['html']}", encoding="utf-8")
        browser.close()
    server.shutdown()


if __name__ == "__main__":
    main()
