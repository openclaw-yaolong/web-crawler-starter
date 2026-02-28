import argparse
import csv
import json
import os
import time
from collections import deque
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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


def build_session(retries: int = 2) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET"],
        backoff_factor=0.5,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def build_robots_parser(start_url: str, user_agent: str):
    parsed = urlparse(start_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp, robots_url
    except Exception:
        return None, robots_url


def crawl(start_url: str, max_pages: int = 20, delay: float = 0.5, retries: int = 2):
    ua = os.getenv("USER_AGENT", "web-crawler-starter/1.0")
    headers = {"User-Agent": ua}

    session = build_session(retries=retries)
    rp, robots_url = build_robots_parser(start_url, ua)

    visited = set()
    q = deque([start_url])
    pages = []
    failed = []

    while q and len(visited) < max_pages:
        url = q.popleft()
        if url in visited:
            continue

        # robots.txt compliance check
        if rp is not None and not rp.can_fetch(ua, url):
            visited.add(url)
            pages.append({
                "url": url,
                "status": None,
                "title": "",
                "links_found": 0,
                "blocked_by_robots": True,
            })
            continue

        try:
            r = session.get(url, headers=headers, timeout=12)
            status = r.status_code
            content_type = r.headers.get("content-type", "")
            text = r.text if "text/html" in content_type else ""
        except Exception as e:
            pages.append({"url": url, "error": str(e), "blocked_by_robots": False})
            failed.append(url)
            visited.add(url)
            continue

        visited.add(url)
        page = {
            "url": url,
            "status": status,
            "title": "",
            "links_found": 0,
            "blocked_by_robots": False,
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
        "robots_url": robots_url,
        "robots_enabled": rp is not None,
        "crawled_pages": len(visited),
        "failed_count": len(failed),
        "failed_urls": failed,
        "pages": pages,
    }


def write_csv(pages, out_csv: str):
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["url", "status", "title", "links_found", "blocked_by_robots", "error"],
        )
        writer.writeheader()
        for p in pages:
            writer.writerow({
                "url": p.get("url", ""),
                "status": p.get("status", ""),
                "title": p.get("title", ""),
                "links_found": p.get("links_found", 0),
                "blocked_by_robots": p.get("blocked_by_robots", False),
                "error": p.get("error", ""),
            })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-url", required=True)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    result = crawl(args.start_url, args.max_pages, args.delay, args.retries)

    os.makedirs("output", exist_ok=True)
    out_json = "output/crawl_result.json"
    out_csv = "output/crawl_result.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    write_csv(result["pages"], out_csv)

    print(f"Done. Crawled {result['crawled_pages']} pages.")
    print(f"Failed URLs: {result['failed_count']}")
    print(f"Saved JSON: {out_json}")
    print(f"Saved CSV:  {out_csv}")


if __name__ == "__main__":
    main()
