"""Template thumbnails for templates/index.html. Re-run after a template changes visibly.
Needs: pip install playwright pillow && playwright install chromium

  python3 tools/thumbs.py            # all
  python3 tools/thumbs.py landing    # one
  python3 tools/thumbs.py --why      # the landing on a laptop, a desktop and a 4K screen, as is and as a conventional
                                     # fluid layout (fixed type, 1200px container), for the figure in why.html

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
    "dashboard": (".db-main", "light"),
    "service": (".sv-hero", "dark"),
    "article": (".ar", "light"),
    "pricing": ("#packages", "light"),
    "gallery": (".pe-head", "light"),
    "contacts": ("#locations", "dark"),
}
WIDTH, THUMB = 1440, (720, 450)


WHY_SIZES = ((1024, 640), (1440, 900), (3840, 2160))  # laptop, desktop, 4K at 100%
FLUID = ":root{--space-inline:max(4rem,calc((100vw - 1200px) / 2))!important}html{font-size:10px!important}"


def why_shots(browser, base):
    from PIL import Image
    out = ROOT / "assets" / "why"
    out.mkdir(parents=True, exist_ok=True)
    for kind, extra in (("prastora", ""), ("fluid", FLUID)):
        for width, height in WHY_SIZES:
            ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme="dark")
            tab = ctx.new_page()
            tab.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) else r.abort())
            tab.goto(f"{base}templates/landing.html")
            tab.add_style_tag(content=".viewport-reading,.load-reading{visibility:hidden!important}" + extra)
            tab.wait_for_timeout(300)
            png = tab.screenshot()
            img = Image.open(io.BytesIO(png)).convert("RGB")
            img = img.resize((round(width * 0.47), round(height * 0.47)), Image.LANCZOS)
            path = out / f"{kind}-{width}.webp"
            img.save(path, quality=70)
            print(path.name, path.stat().st_size, "bytes")
            ctx.close()


def main():
    from playwright.sync_api import sync_playwright
    from PIL import Image
    why = "--why" in sys.argv
    names = [a for a in sys.argv[1:] if a != "--why"] or ([] if why else list(SHOTS))

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(("localhost", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        if why:
            why_shots(browser, f"http://localhost:{server.server_port}/")
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
