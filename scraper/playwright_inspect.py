from playwright.sync_api import sync_playwright
from pathlib import Path

BASE = 'https://weworkremotely.com'
url = BASE + '/categories/remote-full-stack-programming-jobs'

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=120000, wait_until='domcontentloaded')
        # selectors to check
        selectors = ['a.listing-link--unlocked', 'li.new-listing-container a', 'a.listing-link', 'section.jobs article a']
        data_dir = Path(__file__).parent.parent / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        out = {}
        for sel in selectors:
            try:
                els = page.query_selector_all(sel)
                hrefs = [e.get_attribute('href') for e in els]
                out[sel] = {'count': len(els), 'sample': hrefs[:10]}
            except Exception as e:
                out[sel] = {'error': repr(e)}
        # save screenshot
        screenshot_path = data_dir / 'wework_inspect_headless.png'
        page.screenshot(path=str(screenshot_path), full_page=True)
        print('Saved screenshot to', screenshot_path)
        for k,v in out.items():
            print(k, ':', v)
        browser.close()

if __name__ == '__main__':
    inspect()
