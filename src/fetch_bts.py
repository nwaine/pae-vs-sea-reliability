import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests

BASE_URL = "https://transtats.bts.gov/PREZIP/"
FILE_PATTERN = "On_Time_Marketing_Carrier_On_Time_Performance_Beginning_January_2018_{year}_{month}.zip"
RAW_DIR = Path("data/raw")
PARQUET_PATH = Path("data/processed/pae_sea_flights.parquet")
HEADERS = {"User-Agent": "pae-vs-sea-reliability (portfolio project by Nick Waine)"}


def bts_url(year, month):
    filename = FILE_PATTERN.format(year=year, month=month)
    return BASE_URL + filename


def last_n_months(end_year, end_month, n=12):
    months = []
    y, m = end_year, end_month
    for _ in range(n):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(months))


def find_latest_published_month(max_lookback=6):
    now = datetime.now(timezone.utc)
    y, m = now.year, now.month
    for _ in range(max_lookback):
        url = bts_url(y, m)
        r = requests.head(url, headers=HEADERS, timeout=20, allow_redirects=True)
        content_type = r.headers.get("Content-Type", "").lower()
        if r.status_code == 200 and "zip" in content_type:
            return y, m
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    raise RuntimeError("Could not find a recent published BTS PREZIP file.")


def current_local_month():
    if not PARQUET_PATH.exists():
        return None
    dates = pd.read_parquet(PARQUET_PATH, columns=["FlightDate"])["FlightDate"]
    latest = pd.to_datetime(dates).max()
    return (int(latest.year), int(latest.month))


def download_month(year, month):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = bts_url(year, month)
    dest = RAW_DIR / url.split("/")[-1]

    if dest.exists():
        print(f"Skipping {dest.name}, already have it")
        return

    print(f"Downloading {dest.name}...")
    with requests.get(url, headers=HEADERS, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    print(f"Saved {dest.name}")


def main():
    force = "--force" in sys.argv
    latest_remote = find_latest_published_month()
    latest_local = current_local_month()
    print(f"Latest on BTS: {latest_remote[0]}-{latest_remote[1]:02d} | Local parquet: {latest_local}")

    if not force and latest_local == latest_remote:
        print("Already up to date — nothing to download.")
        return

    months = last_n_months(latest_remote[0], latest_remote[1], n=12)
    expected = {FILE_PATTERN.format(year=y, month=m) for y, m in months}

    if RAW_DIR.exists():
        for old_zip in RAW_DIR.glob("*.zip"):
            if old_zip.name not in expected:
                print(f"Removing older file {old_zip.name}")
                old_zip.unlink()

    for year, month in months:
        download_month(year, month)
        time.sleep(2)


if __name__ == "__main__":
    main()