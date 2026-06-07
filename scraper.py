import csv
import os
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


INDEX_URL = "https://www.mot.gov.cn/fuwu/yujingtishi/cjshuiweichaowei/index.html"
CSV_PATH = "daliy_update_waterlevel.csv"

TEXT_WATER_LEVEL = "\u957f\u6c5f\u6c34\u4f4d"
TEXT_TIDE_LEVEL = "\u957f\u6c5f\u6f6e\u4f4d"
COL_OBSERVED_TIME = "\u89c2\u6d4b\u65f6\u95f4"
COL_STATION = "\u7ad9\u70b9"
COL_LEVEL = "\u6c34\u4f4d"
COL_CHANGE = "\u6da8\u843d"
OUTPUT_COLUMNS = [COL_OBSERVED_TIME, COL_STATION, COL_LEVEL, COL_CHANGE]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.mot.gov.cn/",
}


def normalize_text(value):
    return re.sub(r"\s+", " ", str(value)).strip()


def fetch_html(session, url):
    response = session.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def parse_observed_time(title):
    pattern = (
        r"(\d{4})\u5e74(\d{1,2})\u6708(\d{1,2})\u65e5"
        r"(?:(\d{1,2})\u65f6)?\u957f\u6c5f\u6c34\u4f4d"
    )
    match = re.search(pattern, title)
    if not match:
        return None

    year, month, day, hour = match.groups()
    hour = hour or "8"
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d} {int(hour):02d}:00:00"


def find_water_level_links(index_html):
    soup = BeautifulSoup(index_html, "lxml")
    links = []
    seen = set()

    for anchor in soup.select("a[href]"):
        title = normalize_text(anchor.get_text())
        href = anchor.get("href", "")

        if TEXT_WATER_LEVEL not in title or TEXT_TIDE_LEVEL in title:
            continue

        observed_time = parse_observed_time(title)
        if not observed_time:
            print(f"Skip title with unknown time: {title}")
            continue

        detail_url = urljoin(INDEX_URL, href)
        if detail_url in seen:
            continue

        seen.add(detail_url)
        links.append(
            {
                "title": title,
                "url": detail_url,
                "observed_time": observed_time,
            }
        )

    return links


def parse_detail_rows(detail_html, observed_time):
    soup = BeautifulSoup(detail_html, "lxml")
    table = soup.select_one("#article-content table") or soup.find("table")
    if table is None:
        raise ValueError("No table found in detail page")

    rows = []
    for tr in table.find_all("tr"):
        cells = [normalize_text(cell.get_text()) for cell in tr.find_all(["td", "th"])]
        if len(cells) < 3:
            continue

        if COL_STATION in cells[0] and COL_LEVEL in cells[1] and COL_CHANGE in cells[2]:
            continue

        rows.append(
            {
                COL_OBSERVED_TIME: observed_time,
                COL_STATION: cells[0],
                COL_LEVEL: cells[1],
                COL_CHANGE: cells[2],
            }
        )

    return rows


def append_rows(rows):
    file_exists = os.path.exists(CSV_PATH)
    file_has_content = file_exists and os.path.getsize(CSV_PATH) > 0

    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_COLUMNS)
        if not file_has_content:
            writer.writeheader()
        writer.writerows(rows)


def scrape_data():
    session = requests.Session()
    print(f"Fetching index page: {INDEX_URL}")
    index_html = fetch_html(session, INDEX_URL)
    links = find_water_level_links(index_html)
    print(f"Found water-level detail links: {len(links)}")

    all_rows = []
    for item in links:
        print(f"Fetching detail: {item['title']} -> {item['url']}")
        try:
            detail_html = fetch_html(session, item["url"])
            rows = parse_detail_rows(detail_html, item["observed_time"])
            all_rows.extend(rows)
            print(f"  Parsed rows: {len(rows)}")
            time.sleep(1)
        except Exception as exc:
            print(f"  Detail page failed: {exc}")

    if not all_rows:
        print("No valid rows were scraped; CSV was not changed.")
        return

    append_rows(all_rows)
    print(f"Appended rows: {len(all_rows)}")


if __name__ == "__main__":
    scrape_data()
