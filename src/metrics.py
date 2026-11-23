from pathlib import Path
import pandas as pd

DATA_PATH = Path("data/processed/pae_sea_flights.parquet")
CAUSES = [
    "CarrierDelay",
    "WeatherDelay",
    "NASDelay",
    "SecurityDelay",
    "LateAircraftDelay",
]


def load_data():
    df = pd.read_parquet(DATA_PATH)
    df.columns = df.columns.str.strip()
    return df


def summarize(df, group_cols):
    return (
        df.groupby(group_cols)
        .agg(
            flights=("FlightDate", "size"),
            on_time_pct=("ArrDel15", lambda s: (1 - s.mean()) * 100),
            cancel_pct=("Cancelled", lambda s: s.mean() * 100),
            avg_arr_delay=("ArrDelay", "mean"),
            median_arr_delay=("ArrDelay", "median"),
        )
        .round(2)
    )


def delay_causes(df, group_cols):
    completed = df[(df["Cancelled"] == 0) & (df["Diverted"] == 0)].copy()
    completed[CAUSES] = completed[CAUSES].fillna(0)
    return completed.groupby(group_cols)[CAUSES].mean().round(2)


if __name__ == "__main__":
    df = load_data()

    print("=== Delay Causes Overall (avg min per flight) ===")
    print(delay_causes(df, ["Hub"]))

    sfo = df[df["Partner"] == "SFO"]
    print("\n=== SFO Reliability: Hub x Direction ===")
    print(summarize(sfo, ["Hub", "Direction"]))

    print("\n=== SFO Delay Causes: Hub x Direction ===")
    print(delay_causes(sfo, ["Hub", "Direction"]))

    print("\n=== SFO Reliability: Hub x Operating Airline ===")
    print(summarize(sfo, ["Hub", "Operating_Airline"]))

    print("\n=== Sample Possible Duplicates ===")
    dupe_cols = ["FlightDate", "Origin", "Dest", "CRSDepTime", "Operating_Airline"]
    dupes = df[df.duplicated(subset=dupe_cols, keep=False)].sort_values(dupe_cols)
    show = [
        "FlightDate",
        "Origin",
        "Dest",
        "CRSDepTime",
        "Marketing_Airline_Network",
        "Operating_Airline",
        "Flight_Number_Marketing_Airline",
        "Cancelled",
    ]
    print(dupes[show].head(10).to_string(index=False))

    print("\n=== Frontier (F9) at PAE ===")
    f9 = df[(df["Hub"] == "PAE") & (df["Operating_Airline"] == "F9")]
    print(f9["Partner"].value_counts())
    print(f"Dates: {f9['FlightDate'].min().date()} to {f9['FlightDate'].max().date()}")