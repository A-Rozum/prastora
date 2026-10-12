"""Browser checks for the real-site example; requires Python Playwright and Chromium."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
REGIMES = [(390, 844), (1440, 900), (2560, 1440), (320, 568), (863, 339), (734, 232)]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/'
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width, height in REGIMES:
                for scheme in ('light', 'dark'):
                    context = browser.new_context(viewport={'width': width, 'height': height}, color_scheme=scheme)
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    for name in ('expertise', 'expertise-experts'):
                        page.goto(base + f'templates/{name}.html')
                        if name == 'expertise-experts':
                            page.locator('[data-consent-reopen]').click()
                        expect(page.locator('[data-consent-demo]')).to_be_visible()
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (name, width, scheme, 'horizontal overflow')
                        theme = page.locator('[data-theme-toggle]')
                        expect(theme).to_be_visible()
                        theme.click()
                        assert page.locator('html').get_attribute('data-scheme') == ('dark' if scheme == 'light' else 'light')
                        theme.click()
                        nav = page.locator('.desktop-nav') if width > 800 else page.locator('.mobile-nav nav')
                        if width <= 800:
                            page.locator('.mobile-nav > summary').click()
                        nav.locator('.nav-dropdown > summary').first.click()
                        expect(nav.get_by_role('link', name='Правовые заключения', exact=True)).to_be_visible()
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (name, width, 'menu overflow')
                        page.keyboard.press('Escape')
                        assert nav.locator('.nav-dropdown[open]').count() == 0
                        page.locator('[data-consent-reject]').click()
                        page.evaluate('window.scrollTo(0, 700)')
                        top = page.locator('.css-top').bounding_box()['y']
                        assert abs(top) < 1 if height > 480 else top < 0, (width, height, 'sticky regime')
                    assert not errors, errors
                    context.close()

            context = browser.new_context(viewport={'width': 1440, 'height': 900})
            page = context.new_page()
            errors, requests = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: requests.append(request))
            page.goto(base + 'templates/expertise-experts.html')
            page.locator('[data-consent-reject]').click()
            assert page.locator('[data-expert-card]:visible').count() == 6
            page.locator('select[name=country]').select_option('russia')
            assert page.locator('[data-expert-card]:visible').count() == 1
            expect(page.locator('#expert-krivoi')).to_be_visible()
            page.locator('select[name=topic]').select_option('sanctions')
            expect(page.locator('#expert-krivoi')).to_be_visible()
            page.locator('#directory-reset').click()
            page.locator('select[name=country]').select_option('regional')
            assert page.locator('[data-expert-card]:visible').count() == 1
            page.get_by_role('link', name='Профиль эксперта').click()
            expect(page.locator('#focus-regional')).to_be_checked()
            expect(page.locator('#evidence-regional')).to_be_visible()
            page.goto(base + 'templates/expertise-experts.html?topic=interpol#directory')
            assert page.locator('[data-expert-card]:visible').count() == 1
            page.locator('#directory-reset').click()
            page.locator('input[name=name]').fill('Довгаль')
            assert page.locator('[data-expert-card]:visible').count() == 1
            page.get_by_role('link', name='Обсудить вопрос').click()
            assert 'Игорь Довгаль' in page.locator('#request-title').inner_text()
            assert page.locator('#request-expert').input_value() == 'dovgal'
            page.locator('#request-contact').fill('review@example.test')
            page.locator('#request-jurisdiction').fill('Украина')
            page.get_by_role('button', name='Проверить заявку').click()
            expect(page.locator('#form-result')).to_contain_text('Заявка не отправлена')
            assert not [r for r in requests if r.method == 'POST'], 'The preview must not transmit enquiry data'
            page.goto(base + 'templates/product.html')
            expect(page.locator('[data-theme-toggle]')).to_have_attribute('aria-label', 'Switch to dark theme')
            assert not errors, errors
            context.close()

            concept_names = ('expertise-portal', 'expertise-editorial', 'expertise-network', 'expertise-directions')
            for service in ('consultation', 'opinion', 'appearance'):
                context = browser.new_context(viewport={'width': 1440, 'height': 900})
                page = context.new_page()
                page.goto(base + 'templates/expertise-portal.html')
                page.locator('[data-consent-reject]').click()
                page.locator(f'a[href="expertise.html?service={service}#contact"]').first.click()
                expect(page.locator('#request-service')).to_have_value(service)
                context.close()
            concept_shots = ROOT / '.snap' / 'concepts'
            concept_shots.mkdir(parents=True, exist_ok=True)
            for width, height in REGIMES:
                for scheme in ('light', 'dark'):
                    for name in concept_names:
                        context = browser.new_context(viewport={'width': width, 'height': height}, color_scheme=scheme)
                        page = context.new_page()
                        errors = []
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        page.goto(base + f'templates/{name}.html')
                        expect(page.locator('[data-consent-demo]')).to_be_visible()
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (name, width, scheme, 'overflow')
                        page.locator('[data-consent-reject]').click()
                        theme = page.locator('[data-theme-toggle]')
                        theme.click()
                        assert page.locator('html').get_attribute('data-scheme') == ('dark' if scheme == 'light' else 'light')
                        theme.click()
                        if name != 'expertise-directions':
                            nav = page.locator('.desktop-nav') if width > 800 else page.locator('.mobile-nav nav')
                            if width <= 800:
                                page.locator('.mobile-nav > summary').click()
                            nav.locator('.nav-dropdown > summary').first.click()
                            expect(nav.get_by_role('link', name='Правовые заключения', exact=True)).to_be_visible()
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (name, width, 'menu overflow')
                            nav.get_by_role('link', name='Правовые заключения', exact=True).click()
                            expect(page.locator('#service-opinion')).to_be_in_viewport()
                            page.keyboard.press('Escape')
                            article = page.locator('.article-topic .disclosure').first
                            article.locator('summary').click()
                            expect(article.locator('div').first).to_be_visible()
                            page.get_by_role('link', name='Стать экспертом', exact=False).click()
                            expect(page.locator('#join')).to_be_in_viewport()
                            page.evaluate('window.scrollTo(0, 700)')
                            top = page.locator('.css-top').bounding_box()['y']
                            assert abs(top) < 1 if height > 480 else top < 0, (name, width, height, 'sticky')
                        page.evaluate('window.scrollTo(0, 0)')
                        page.screenshot(path=str(concept_shots / f'{name}_{width}x{height}_{scheme}.png'), full_page=True)
                        assert not errors, errors
                        context.close()

            for name in concept_names:
                context = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
                page = context.new_page()
                page.goto(base + f'templates/{name}.html')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (name, 'no JS overflow')
                if name != 'expertise-directions':
                    page.locator('.mobile-nav > summary').click()
                    page.locator('.mobile-nav .nav-dropdown > summary').first.click()
                    page.locator('.mobile-nav nav').get_by_role('link', name='Правовые заключения', exact=True).click()
                    expect(page.locator('#service-opinion')).to_be_in_viewport()
                    article = page.locator('.article-topic .disclosure').first
                    article.locator('summary').click()
                    expect(article.locator('div').first).to_be_visible()
                context.close()

            context = browser.new_context(java_script_enabled=False, viewport={'width': 1440, 'height': 900})
            page = context.new_page()
            page.goto(base + 'templates/expertise.html')
            page.locator('label[for=focus-regional]').click()
            expect(page.locator('#evidence-regional')).to_be_visible()
            assert page.locator('a[href^="mailto:"]').count() == 1
            assert page.locator('a[href$=".pdf"]').count() == 0
            assert not list((ROOT / 'assets/expertise').glob('*.pdf'))
            page.locator('.desktop-nav .nav-dropdown > summary').first.click()
            expect(page.locator('.desktop-nav').get_by_role('link', name='Правовые заключения', exact=True)).to_be_visible()
            page.goto(base + 'templates/expertise-experts.html')
            assert page.locator('[data-expert-card]:visible').count() == 6
            context.close()
            browser.close()
    finally:
        server.shutdown()
    print('Six viewport regimes, both themes, three design directions, menus, filtering, enquiries and no-JS journeys passed')


if __name__ == '__main__':
    main()
