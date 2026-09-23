import requests
from bs4 import BeautifulSoup
import time
import json
from pathlib import Path
import argparse

from ai_extractor import rule_based_extract, llm_extract

BASE = "https://remoteok.com"


def fetch_search(keyword):
    url = f"{BASE}/remote-{keyword}-jobs"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JobScout/1.0)"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.text


def parse_listings(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    rows = soup.find_all('tr', class_='job')
    if not rows:
        # fallback: look for links to job pages
        links = soup.select('a[itemprop=url]')
        for a in links:
            jobs.append({'url': BASE + a.get('href')})
        return jobs

    for r in rows:
        a = r.find('a', href=True)
        href = a['href'] if a else None
        title_tag = r.find('h2')
        company_tag = r.find('h3')
        tags = [t.get_text(strip=True) for t in r.select('.tags a')]
        jobs.append({
            'url': BASE + href if href and href.startswith('/') else href,
            'title': title_tag.get_text(strip=True) if title_tag else None,
            'company': company_tag.get_text(strip=True) if company_tag else None,
            'tags': tags,
        })
    return jobs


def fetch_job_detail(url):
    if not url:
        return None
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JobScout/1.0)"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    desc = soup.find('div', {'class': 'description'}) or soup.find('div', {'id': 'description'})
    if desc:
        return desc.get_text(separator=' ', strip=True)
    # fallback full text
    return soup.get_text(separator=' ', strip=True)[:5000]


def run(keyword='java', limit=3):
    print(f"Searching RemoteOK for '{keyword}' (limit {limit})")
    html = fetch_search(keyword)
    listings = parse_listings(html)
    print(f"Found {len(listings)} listings (parsing up to {limit})")

    out = []
    for i, job in enumerate(listings[:limit]):
        url = job.get('url')
        print(f"[{i+1}] Fetching {url}")
        try:
            jd = fetch_job_detail(url)
        except Exception as e:
            print("Failed to fetch detail:", e)
            jd = None

        # Compose text for extractor
        combined = ''
        if job.get('title'):
            combined += f"Title: {job.get('title')}\n"
        if job.get('company'):
            combined += f"Company: {job.get('company')}\n"
        if job.get('tags'):
            combined += f"Skills: {', '.join(job.get('tags'))}\n"
        if jd:
            combined += '\n' + jd

        # Try LLM extraction first (internal function handles key presence)
        parsed = llm_extract(combined)
        if not parsed:
            parsed = rule_based_extract(combined)

        parsed_record = {
            'source': 'remoteok',
            'url': url,
            'raw_title': job.get('title'),
            'raw_company': job.get('company'),
            'extracted': parsed
        }
        out.append(parsed_record)
        time.sleep(1)

    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    out_file = data_dir / f'remoteok_{keyword}_extracted.json'
    out_file.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', '-k', default='java')
    parser.add_argument('--limit', '-n', default=3, type=int)
    args = parser.parse_args()
    run(keyword=args.keyword, limit=args.limit)
