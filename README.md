# web-crawler-starter

A minimal Python crawler starter project.

## Features
- Fetch web pages with `requests`
- Parse links with `BeautifulSoup`
- Respectful crawling delay
- Save crawl results to JSON

## Quick Start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m crawler.main --start-url https://example.com --max-pages 20
```

## Output
Results are written to:
- `output/crawl_result.json`
