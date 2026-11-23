from pathlib import Path
import pandas as pd
import zipfile

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
HUBS = {"PAE", "SEA"}
DESTS = {"LAS", "LAX", "SNA", "PHX", "PDX", "SAN", "SFO", "PSP"}

COLUMNS = [
    "FlightDate", "DayOfWeek", "Marketing_Airline_Network", "Operating_Airline ",
    "Flight_Number_Marketing_Airline", "Origin", "Dest",
    "CRSDepTime", "DepDelay", "DepDel15", "DepTimeBlk",
    "CRSArrTime", "ArrDelay", "ArrDel15",
    "Cancelled", "CancellationCode", "Diverted",
    "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay",
]


def load_month(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        csv_name = [n for n in z.namelist() if n.endswith(".csv")][0]
        with z.open(csv_name) as f:
            df = pd.read_csv(f, usecols=COLUMNS, low_memory=False)
    before = len(df)
    outbound = df["Origin"].isin(HUBS) & df["Dest"].isin(DESTS)
    inbound = df["Dest"].isin(HUBS) & df["Origin"].isin(DESTS)
    df = df[outbound | inbound]
    print(f"{zip_path.name}: {before:,} rows -> {len(df):,}")
    return df

def clean_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = [load_month(p) for p in sorted(RAW_DIR.glob("*.zip"))]
    df = pd.concat(frames, ignore_index=True)

    df["FlightDate"] = pd.to_datetime(df["FlightDate"])
    is_outbound = df["Origin"].isin(HUBS)
    df["Direction"] = is_outbound.map({True: "outbound", False: "inbound"})
    df["Hub"] = df["Origin"].where(is_outbound, df["Dest"])
    df["Partner"] = df["Dest"].where(is_outbound, df["Origin"])

    out_path = OUT_DIR / "pae_sea_flights.parquet"
    df.to_parquet(out_path, index=False)
    size_mb = out_path.stat().st_size / 1_000_000
    print(f"\nSaved {len(df):,} rows to {out_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    clean_all()