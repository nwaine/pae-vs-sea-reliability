import time                 #lets you pause between downloads
from pathlib import Path    # handles folders and file paths
import requests             # downloads files from the web

BASE_URL = "https://transtats.bts.gov/PREZIP/"
FILE_PATTERN = "On_Time_Marketing_Carrier_On_Time_Performance_Beginning_January_2018_{year}_{month}.zip"
RAW_DIR = Path("data/raw")
HEADERS = {"User-Agent": "pae-vs-sea-reliability (portfolio project by Nick Waine)" }

def bts_url(year, month):
    filename = FILE_PATTERN.format(year=year, month=month)
    return BASE_URL + filename

def download_month(year, month):
    RAW_DIR.mkdir(parents=True, exist_ok=True)       # make the folder if it's missing
    url = bts_url(year, month)
    dest = RAW_DIR / url.split("/")[-1]              # save it under the file's own name

    if dest.exists():                                # don't re-download
        print(f"Skipping {dest.name}, already have it")
        return

    print(f"Downloading {dest.name}...")
    with requests.get(url, headers=HEADERS, stream=True, timeout=120) as r:
        r.raise_for_status()                         # stop if the server says error
        with open(dest, "wb") as f:                  # "wb" = write bytes
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)                       # save 1 MB at a time
    print(f"Saved {dest.name}")

def last_n_months(end_year, end_month, n=12):
    months = []
    y, m = end_year, end_month
    for _ in range(n):
        months.append((y, m))
        m -= 1
        if m == 0:                 # wrap from January back to December
            m = 12
            y -= 1
    return list(reversed(months))  # oldest first

if __name__ == "__main__":
    for year, month in last_n_months(2026, 9):
        try:
            download_month(year, month)
        except Exception as e:
            print(f"Failed {year}-{month}: {e}")   # log it and keep going
        time.sleep(2)                              # be polite to BTS