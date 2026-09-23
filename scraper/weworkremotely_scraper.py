import requests
from bs4 import BeautifulSoup
import time
import json
from pathlib import Path
import argparse

from ai_extractor import rule_based_extract, llm_extract

BASE = "https://weworkremotely.com"


def fetch_listings(category='remote-jobs'):
    url = f"{BASE}/categories/{category}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JobScout/1.0)"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.text


def parse_listings(html):
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    sections = soup.select('section.jobs > article')
    for sec in sections:
        link = sec.find('a', href=True)
        if not link:
            continue
        href = link['href']
        title_tag = sec.select_one('span.title')
        company_tag = sec.select_one('span.company')
        tags = [t.get_text(strip=True) for t in sec.select('span.region, span.tag')]
        jobs.append({
            'url': BASE + href,
            'title': title_tag.get_text(strip=True) if title_tag else None,
            'company': company_tag.get_text(strip=True) if company_tag else None,
            'tags': tags,
        })
    return jobs


def extract_jobs_from_category(category_url, per_category_limit=10):
    """Given a category page URL, fetch it and return a list of job dicts found on it."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; JobScout/1.0)"}
        resp = requests.get(category_url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        jobs = []
        # job articles are inside section.jobs or article.listing
        articles = soup.select('section.jobs article') or soup.select('article')
        import re
        for a in articles:
            link = a.find('a', href=True)
            if not link:
                continue
            href = link['href']
            # skip category links
            if '/categories/' in href:
                continue
            # some links are full paths already
            url = href if href.startswith('http') else BASE + href
            # filter only likely job post links using common patterns
            if not re.search(r'/(remote-|jobs/|positions|listings|job/)', href):
                continue
            title_tag = a.select_one('span.title') or a.select_one('h2')
            company_tag = a.select_one('span.company') or a.select_one('h3')
            tags = [t.get_text(strip=True) for t in a.select('span.region, span.tag')]
            jobs.append({
                'url': url,
                'title': title_tag.get_text(strip=True) if title_tag else None,
                'company': company_tag.get_text(strip=True) if company_tag else None,
                'tags': tags,
            })
            if len(jobs) >= per_category_limit:
                break
        return jobs
    except Exception as e:
        print('Failed to expand category:', category_url, e)
        return []


def fetch_job_detail(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JobScout/1.0)"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    desc = soup.select_one('div.listing-container')
    if desc:
        return desc.get_text(separator=' ', strip=True)
    return soup.get_text(separator=' ', strip=True)[:5000]


def run(limit=3):
    print("Fetching WeWorkRemotely listings")
    html = fetch_listings()
    listings = parse_listings(html)
    print(f"Found {len(listings)} initial listings (categories); expanding to job links and parsing up to {limit} total jobs")
    out = []
    # Expand each category into job links until we reach limit
    for cat in listings:
        cat_url = cat.get('url')
        if not cat_url:
            continue
        jobs_in_cat = extract_jobs_from_category(cat_url, per_category_limit=10)
        for job in jobs_in_cat:
            if len(out) >= limit:
                break
            print(f"Fetching job: {job.get('title')} @ {job.get('company')} -> {job.get('url')}")
            jd = None
            try:
                jd = fetch_job_detail(job['url'])
            except Exception as e:
                print('detail fetch failed:', e)

            combined = ''
            if job.get('title'):
                combined += f"Title: {job.get('title')}\n"
            if job.get('company'):
                combined += f"Company: {job.get('company')}\n"
            if job.get('tags'):
                combined += f"Skills: {', '.join(job.get('tags'))}\n"
            if jd:
                combined += '\n' + jd

            parsed = llm_extract(combined)
            if not parsed:
                parsed = rule_based_extract(combined)

            out.append({'url': job['url'], 'raw_title': job.get('title'), 'raw_company': job.get('company'), 'extracted': parsed})
            time.sleep(1)
        if len(out) >= limit:
            break

    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    out_file = data_dir / 'weworkremotely_extracted.json'
    out_file.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', '-n', default=3, type=int)
    args = parser.parse_args()
    run(limit=args.limit)
