"""Template thumbnails for templates/index.html. Re-run after a template changes visibly.
Needs: pip install playwright pillow && playwright install chromium

  python3 tools/thumbs.py            # all
  python3 tools/thumbs.py landing    # one

Each shot starts at a selector that shows what the template is about and is cropped to 16:10.
"""
import functools, http.server, io, sys, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "templates"
SHOTS = {  # name: (selector to start from, colour scheme)
    "landing": (".sb-hero", "dark"),
    "product": (".pd", "light"),
    "checkout": (".co", "light"),
    "service": ("main", "light"),
    "article": (".ar", "light"),
    "pricing": ("#packages", "light"),
    "gallery": ("#collection", "light"),
    "contacts": ("main", "light"),
}
WIDTH, THUMB = 1440, (720, 450)


def main():
    from playwright.sync_api import sync_playwright
    from PIL import Image
    names = sys.argv[1:] or list(SHOTS)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(("localhost", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name in names:
            selector, scheme = SHOTS[name]
            ctx = browser.new_context(viewport={"width": WIDTH, "height": 900}, color_scheme=scheme)
            tab = ctx.new_page()
            base = f"http://localhost:{server.server_port}/"
            tab.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) else r.abort())
            tab.goto(f"{base}templates/{name}.html")
            tab.add_style_tag(content=".viewport-panel,.consent-bar,iframe{visibility:hidden!important}")
            tab.wait_for_timeout(300)
            top = tab.eval_on_selector(selector, "e => e.getBoundingClientRect().top + scrollY")
            png = tab.screenshot(full_page=True, clip={"x": 0, "y": top, "width": WIDTH, "height": WIDTH * 10 / 16})
            Image.open(io.BytesIO(png)).convert("RGB").resize(THUMB, Image.LANCZOS).save(OUT / f"{name}.webp", quality=72)
            print(name, (OUT / f"{name}.webp").stat().st_size, "bytes")
            ctx.close()
        browser.close()
    server.shutdown()


if __name__ == "__main__":
    main()
