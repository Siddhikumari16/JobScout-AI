import requests
from bs4 import BeautifulSoup


def fetch(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print("Request failed:", e)
        return None


if __name__ == "__main__":
    url = "https://example.com"
    html = fetch(url)
    if not html:
        print("Failed to fetch page")
    else:
        soup = BeautifulSoup(html, "html.parser")
        print("Status: fetched")
        title = soup.title.string.strip() if soup.title else "(no title)"
        print("Page title:", title)
