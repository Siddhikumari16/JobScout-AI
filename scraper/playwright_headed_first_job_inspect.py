from playwright.sync_api import sync_playwright
from pathlib import Path
import time

BASE = 'https://weworkremotely.com'
CATEGORY = BASE + '/categories/remote-full-stack-programming-jobs'

def run():
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = data_dir / 'wework_first_job_headed.png'
    html_path = data_dir / 'wework_first_job_headed.html'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto(CATEGORY, timeout=120000, wait_until='domcontentloaded')
            page.wait_for_selector('a.listing-link--unlocked', timeout=60000)
            anchors = page.query_selector_all('a.listing-link--unlocked')
            if not anchors:
                print('No anchors found on category page')
                return
            first = anchors[0].get_attribute('href')
            if not first:
                print('First anchor has no href')
                return
            if first.startswith('http'):
                job_url = first
            else:
                job_url = BASE + first

            print('Navigating to first job URL:', job_url)
            page.goto(job_url, timeout=120000, wait_until='domcontentloaded')
            # give page a moment to render dynamic content
            time.sleep(2)

            # save screenshot and HTML
            page.screenshot(path=str(screenshot_path), full_page=True)
            html = page.content()
            html_path.write_text(html, encoding='utf-8')

            final_url = page.url
            try:
                title = page.title()
            except Exception:
                title = ''
            try:
                body_text = page.inner_text('body')
            except Exception:
                body_text = page.content()[:2000]

            print('Final page URL:', final_url)
            print('Page title:', title)
            print('Body snippet (first 800 chars):')
            print(body_text.strip()[:800])
            print('Saved screenshot to', screenshot_path)
            print('Saved HTML to', html_path)
        except Exception as e:
            print('Error during inspection:', repr(e))
        finally:
            try:
                browser.close()
            except Exception:
                pass

if __name__ == '__main__':
    run()
