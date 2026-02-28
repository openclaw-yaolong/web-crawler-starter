import argparse
import json
import os
import time
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def same_domain(a: str, b: str) -> bool:
    return urlparse(a).netloc == urlparse(b).netloc


def extract_links(base_url: str, html: str):
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        abs_url = urljoin(base_url, href)
        if abs_url.startswith("http://") or abs_url.startswith("https://"):
            links.append(abs_url)
    return links


def crawl(start_url: str, max_pages: int = 20, delay: float = 0.5):
    ua = os.getenv("USER_AGENT", "web-crawler-starter/1.0")
    headers = {"User-Agent": ua}

    visited = set()
    q = deque([start_url])
    pages = []

    while q and len(visited) < max_pages:
        url = q.popleft()
        if url in visited:
            continue

        try:
            r = requests.get(url, headers=headers, timeout=12)
            status = r.status_code
            content_type = r.headers.get("content-type", "")
            text = r.text if "text/html" in content_type else ""
        except Exception as e:
            pages.append({"url": url, "error": str(e)})
            visited.add(url)
            continue

        visited.add(url)
        page = {
            "url": url,
            "status": status,
            "title": "",
            "links_found": 0,
        }

        if text:
            soup = BeautifulSoup(text, "lxml")
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            links = extract_links(url, text)
            links = [u for u in links if same_domain(start_url, u)]
            page["title"] = title
            page["links_found"] = len(links)
            for nxt in links:
                if nxt not in visited:
                    q.append(nxt)

        pages.append(page)
        time.sleep(delay)

    return {
        "start_url": start_url,
        "crawled_pages": len(visited),
        "pages": pages,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-url", required=True)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    result = crawl(args.start_url, args.max_pages, args.delay)

    os.makedirs("output", exist_ok=True)
    out = "output/crawl_result.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Done. Crawled {result['crawled_pages']} pages.")
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
