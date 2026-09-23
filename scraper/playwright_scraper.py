from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import json

from ai_extractor import rule_based_extract, llm_extract

BASE = 'https://weworkremotely.com'


def run(limit=3):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(user_agent='JobScout/1.0')
        try:
            # increase timeout and use domcontentloaded for faster navigation completion
            page.goto(BASE + '/categories/remote-full-stack-programming-jobs', timeout=60000, wait_until='domcontentloaded')
            # wait for the primary job-post anchors to appear
            page.wait_for_selector('a.listing-link--unlocked', timeout=60000)
            # save debug screenshot and HTML for inspection
            data_dir = Path(__file__).parent.parent / 'data'
            data_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = data_dir / 'wework_category_debug.png'
            page.screenshot(path=str(screenshot_path), full_page=True)
            print('Saved category screenshot to', screenshot_path)
            try:
                # gather anchors using the primary selector
                anchors = page.query_selector_all('a.listing-link--unlocked')
                hrefs = []
                for a in anchors:
                    h = a.get_attribute('href')
                    if not h:
                        continue
                    # keep only /remote-jobs/ links
                    if h.startswith('/remote-jobs/'):
                        # convert to absolute
                        if h.startswith('http'):
                            hrefs.append(h)
                        else:
                            hrefs.append(BASE + h)

                # dedupe while preserving order
                seen = set()
                unique = []
                for u in hrefs:
                    if u not in seen:
                        seen.add(u)
                        unique.append(u)

                print('Found', len(unique), 'unique job URLs')
                for u in unique[:5]:
                    print(u)
                # For now, fetch only the first job URL for inspection
                if len(unique) == 0:
                    print('No job URLs to inspect')
                else:
                    first_url = unique[0]
                    print('\nInspecting first job page:', first_url)
                    try:
                        # navigate to job page and wait for DOM
                        page.goto(first_url, timeout=60000, wait_until='domcontentloaded')
                    except Exception as e:
                        print('Navigation to job page failed:', repr(e))
                    else:
                        # helper to try multiple selectors and return first match
                        def first_text_for_selectors(sel_list):
                            for s in sel_list:
                                try:
                                    el = page.query_selector(s)
                                    if el:
                                        txt = el.inner_text().strip()
                                        if txt:
                                            return s, txt
                                except Exception:
                                    continue
                            return None, None

                        title_selectors = [
                            'h1.listing-header__title',
                            'h1',
                            'div.new-listing__header__title__text',
                            'h1.listing-title',
                            'div.listing-header__title__text',
                            'span.new-listing__header__title__text',
                        ]
                        company_selectors = [
                            'p.new-listing__company-name',
                            'div.listing-header__company',
                            'a.company',
                            'span.company',
                        ]
                        location_selectors = [
                            'p.new-listing__company-headquarters',
                            'span.listing-location',
                            'div.listing-header__location',
                        ]
                        desc_selectors = [
                            'div.listing-container',
                            'div.listing-body',
                            'div.listing-container--description',
                            'section.listing-container',
                        ]

                        sel, title = first_text_for_selectors(title_selectors)
                        print('Title selector:', sel)
                        print('Title:', (title or '').strip()[:400])

                        sel_c, company = first_text_for_selectors(company_selectors)
                        print('Company selector:', sel_c)
                        print('Company:', (company or '').strip()[:200])

                        sel_l, location = first_text_for_selectors(location_selectors)
                        print('Location selector:', sel_l)
                        print('Location:', (location or '').strip()[:200])

                        sel_d, desc = first_text_for_selectors(desc_selectors)
                        print('Description selector:', sel_d)
                        print('Description (first 800 chars):')
                        if desc:
                            print(desc.strip()[:800])
                        else:
                            # fallback: try to grab main content HTML
                            try:
                                body = page.content()
                                print('Page content length:', len(body))
                            except Exception as e:
                                print('Failed to read page content:', repr(e))
            except Exception as e:
                print('Error inspecting jobs section:', repr(e))
        except Exception as e:
            print('Navigation or selector wait failed:', repr(e))
            browser.close()
            return
        # select job links
        links = page.query_selector_all('section.jobs article a')
        jobs = []
        for a in links:
            href = a.get_attribute('href')
            title_el = a.query_selector('span.title')
            company_el = a.query_selector('span.company')
            title = title_el.inner_text().strip() if title_el else None
            company = company_el.inner_text().strip() if company_el else None
            url = href if href.startswith('http') else BASE + href
            jobs.append({'url': url, 'title': title, 'company': company})
            if len(jobs) >= limit:
                break

        out = []
        for job in jobs:
            print('Fetching', job['url'])
            try:
                page.goto(job['url'], timeout=60000, wait_until='domcontentloaded')
                # wait for the detail container to appear
                page.wait_for_selector('div.listing-container', timeout=60000)
                desc = page.query_selector('div.listing-container')
                jd = desc.inner_text().strip() if desc else page.content()[:5000]
            except Exception as e:
                print('Failed to load job page or find selector:', repr(e))
                jd = page.content()[:5000]

            combined = ''
            if job.get('title'):
                combined += f"Title: {job.get('title')}\n"
            if job.get('company'):
                combined += f"Company: {job.get('company')}\n"
            combined += '\n' + jd

            parsed = llm_extract(combined)
            if not parsed:
                parsed = rule_based_extract(combined)

            out.append({'url': job['url'], 'raw_title': job.get('title'), 'raw_company': job.get('company'), 'extracted': parsed})
            time.sleep(1)

        data_dir = Path(__file__).parent.parent / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        out_file = data_dir / 'playwright_wework_extracted.json'
        out_file.write_text(json.dumps(out, indent=2))
        print('Wrote', out_file)
        try:
            browser.close()
        except Exception:
            pass


if __name__ == '__main__':
    run(limit=3)
