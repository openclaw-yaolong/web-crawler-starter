# web-crawler-starter

A minimal Python crawler starter project.

## Features
- Fetch web pages with `requests`
- Parse links with `BeautifulSoup`
- robots.txt compliance check (`/robots.txt`)
- Simple retry / failed URL capture
- Respectful crawling delay
- Save crawl results to JSON + CSV

## Quick Start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m crawler.main --start-url https://example.com --max-pages 20 --retries 2
```

## Output
Results are written to:
- `output/crawl_result.json`
- `output/crawl_result.csv`
