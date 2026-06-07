# Yangtze Daily Water Level Scraper

This repository uses GitHub Actions to scrape Yangtze River water-level data from the Ministry of Transport website every day and append the result to a CSV file in the repository.

## Data Source

- Entry page: <https://www.mot.gov.cn/fuwu/yujingtishi/cjshuiweichaowei/index.html>
- Included: articles whose title contains `长江水位`
- Excluded: articles whose title contains `长江潮位`

## Output File

Data is appended to:

```text
daliy_update_waterlevel.csv
```

CSV columns:

```text
观测时间,站点,水位,涨落
```

The script appends newly scraped rows to the end of the CSV file. It does not deduplicate and does not overwrite existing records.

## Schedule

The workflow runs once per day at:

```text
12:00 Beijing time
```

GitHub Actions cron uses UTC, so the workflow is configured as:

```text
0 4 * * *
```

You can also run it manually from the GitHub Actions tab with `workflow_dispatch`.

## Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── scrape.yml
├── daliy_update_waterlevel.csv
├── requirements.txt
├── scraper.py
└── README.md
```

## Local Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the scraper:

```bash
python scraper.py
```

## GitHub Deployment

1. Create a new GitHub repository.
2. Copy all files from this project into the new repository.
3. Commit and push the files.
4. Open the repository on GitHub.
5. Go to `Actions`.
6. Enable workflows if GitHub asks.
7. Run `scrape-and-update` manually once to test.

After each successful run, GitHub Actions will commit and push changes to `daliy_update_waterlevel.csv` if the file changed.

## Notes

- The source code is ASCII-safe to avoid encoding problems in GitHub Actions logs.
- The CSV itself is written with UTF-8 BOM so Chinese column names and station names open cleanly in Excel.
- If the source website changes its HTML structure, `scraper.py` may need to be updated.
