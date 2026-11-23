# Paine Field (PAE) vs. Sea-Tac (SEA) Flight Reliability

**Live dashboard:** [pae-vs-sea-reliability.netlify.app](https://pae-vs-sea-reliability.netlify.app)

**Guiding question:** Across the 8 West Coast cities served nonstop by Paine Field (`LAS`, `LAX`, `SNA`, `PHX`, `PDX`, `SAN`, `SFO`, and seasonal `PSP`), are flights from PAE actually more reliable than flights from Sea-Tac (`SEA`) to the same destinations?

## Key Findings (Oct 2025 – Sep 2026)

From **7,801,408** nationwide U.S. flights filtered down to **94,910** scheduled PAE/SEA flights (6,551 at PAE; 88,359 at SEA):

- **The headline hides the real story:** Overall, SEA edges out PAE on on-time arrivals (**78.8%** vs. **77.7%**). Exclude **SFO**, and PAE jumps to **83.4%** on time — beating SEA in **11 of 12 months**.
- **PAE wins half the routes outright:** PAE beats SEA on **PHX** (87.2% vs. 79.8%), **PDX** (86.5% vs. 82.6%), **LAX** (85.9% vs. 83.0%), and **LAS** (85.0% vs. 79.9%), with flights on those routes landing early on average.
- **SFO creates a turnaround domino effect:** SFO accounts for **19.3%** of PAE's schedule, all flown by Horizon Air (`QX`). Outbound `PAE → SFO` is only **48.8%** on time (+30.6 min avg delay), driven by **20.2 min/flight** of airspace/ATC holds (`NASDelay`). When that same regional jet turns around for `SFO → PAE`, the delay converts directly into **20.4 min/flight** of `LateAircraftDelay` (nearly 3× `SFO → SEA`'s 7.5 min) and a **3.8%** cancellation rate (vs. 1.1% at SEA).
- **The small-airport trade-off:** PAE cancels almost twice as often overall (**1.69%** vs. **0.89%**), which hurts more when a route only runs 1–2 flights a day.

## Data Sources & Architecture

- **Historical reliability:** U.S. DOT Bureau of Transportation Statistics ([BTS](https://transtats.bts.gov/PREZIP/)) **Marketing Carrier** On-Time Performance PREZIPs (rolling 12 months; DOT publishes on a ~2-month lag).
- **Live airport strip:** [NOAA Aviation Weather](https://aviationweather.gov/) METARs (`KPAE`, `KSEA`, `KSFO`), [FAA NAS Status](https://nasstatus.faa.gov/) delay events, nearby aircraft positions via [adsb.lol](https://adsb.lol/) (ODbL), and commercial route lookups via [adsbdb.com](https://www.adsbdb.com/), proxied and cached for 60 seconds through a Netlify Function (`netlify/functions/live.mjs`).
- **Auto-refresh pipeline:** A weekly GitHub Action (`.github/workflows/refresh.yml`) checks BTS with a lightweight `HEAD` request. When a new month is published, it downloads the rolling 12-month window, rebuilds `data/processed/pae_sea_flights.parquet` and `dashboard/index.html`, commits to `main`, and Netlify redeploys automatically.

## Data Quality Notes

- **Why Marketing Carrier (not Reporting Carrier):** Horizon Air (`QX`) is not a 2026 DOT Reporting Carrier, yet operates **63.7%** (4,172 of 6,551) of Paine Field's flights. Using the default Reporting Carrier table would have silently dropped nearly two-thirds of PAE's schedule.
- **Raw file quirks:** BTS ZIPs bundle a `readme.html` alongside the CSV (extracted explicitly via `zipfile`), and the CSV header literally includes a trailing space in `'Operating_Airline '` (cleaned with `.str.strip()`).
- **Duplicate check:** 67 same-minute timestamp matches were inspected and confirmed to be SkyWest (`OO`) operating separate regional jets for competing mainline carriers — zero true duplicates.
- **Live route sanity check:** Because airlines reuse flight numbers across legs, `adsbdb.com` lookups are filtered to routes with at least one endpoint in the Puget Sound region so stale cross-country legs aren't displayed.

## Project Structure

```text
├── .github/workflows/refresh.yml   # Weekly BTS freshness check & auto-rebuild
├── dashboard/index.html            # Built static dashboard (published by Netlify)
├── data/processed/                 # Cleaned rolling 12-month parquet (~0.7 MB)
├── netlify/functions/live.mjs      # Serverless proxy for NOAA, FAA, adsb.lol, adsbdb
├── netlify.toml                    # Netlify publish + functions config
├── requirements.txt
└── src/
    ├── fetch_bts.py                # Auto-discovers & downloads latest 12 BTS months
    ├── clean.py                    # Filters 7.8M+ raw rows down to PAE/SEA routes
    ├── metrics.py                  # Reliability and delay-cause aggregations
    ├── charts.py                   # Interactive Plotly charts
    └── build_dashboard.py          # Renders static HTML dashboard + live strip