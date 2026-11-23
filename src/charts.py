from pathlib import Path
import pandas as pd
import plotly.express as px
from metrics import delay_causes, load_data, summarize

OUT_DIR = Path("outputs")
PAE_COLOR = "#0d9488"  # teal
SEA_COLOR = "#ea580c"  # warm orange


def route_on_time_chart(df):
    routes = summarize(df, ["Partner", "Hub"]).reset_index()

    # Sort destinations by PAE on-time rate
    pae_order = (
        routes[routes["Hub"] == "PAE"]
        .sort_values("on_time_pct", ascending=True)["Partner"]
        .tolist()
    )

    fig = px.bar(
        routes,
        x="on_time_pct",
        y="Partner",
        color="Hub",
        barmode="group",
        orientation="h",
        category_orders={"Partner": pae_order, "Hub": ["PAE", "SEA"]},
        color_discrete_map={"PAE": PAE_COLOR, "SEA": SEA_COLOR},
        hover_data=["flights", "cancel_pct", "avg_arr_delay"],
        labels={
            "on_time_pct": "On-Time Arrival Rate (%)",
            "Partner": "Destination",
            "Hub": "Home Airport",
        },
        title="On-Time Arrival Rate by Destination: Paine Field (PAE) vs. Sea-Tac (SEA)",
    )
    fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
    fig.update_layout(
        xaxis_range=[0, 100],
        template="plotly_white",
        legend_title_text="",
        legend=dict(traceorder="reversed"),
        margin=dict(l=70),
    )
    return fig


def sfo_delay_causes_chart(df):
    sfo = df[df["Partner"] == "SFO"]
    causes = delay_causes(sfo, ["Hub", "Direction"]).reset_index()

    leg_labels = {
        ("PAE", "outbound"): "PAE → SFO (outbound)",
        ("PAE", "inbound"): "SFO → PAE (inbound)",
        ("SEA", "outbound"): "SEA → SFO (outbound)",
        ("SEA", "inbound"): "SFO → SEA (inbound)",
    }
    causes["Leg"] = [
        leg_labels[(h, d)] for h, d in zip(causes["Hub"], causes["Direction"])
    ]

    cause_names = {
        "NASDelay": "Airspace / ATC (NAS)",
        "LateAircraftDelay": "Late Arriving Aircraft",
        "CarrierDelay": "Airline / Carrier",
        "WeatherDelay": "Weather",
    }
    melted = causes.melt(
        id_vars="Leg",
        value_vars=list(cause_names.keys()),
        var_name="Cause",
        value_name="Minutes",
    )
    melted["Cause"] = melted["Cause"].map(cause_names)

    fig = px.bar(
        melted,
        x="Leg",
        y="Minutes",
        color="Cause",
        barmode="stack",
        category_orders={
            "Leg": list(leg_labels.values()),
            "Cause": list(cause_names.values()),
        },
        color_discrete_map={
            "Airspace / ATC (NAS)": "#d97706",
            "Late Arriving Aircraft": "#dc2626",
            "Airline / Carrier": "#475569",
            "Weather": "#0284c7",
        },
        labels={
            "Leg": "",
            "Minutes": "Average Delay Minutes per Flight",
            "Cause": "Delay Cause",
        },
        title="Why PAE–SFO Breaks Down: Airspace Holds Outbound, Late Aircraft Inbound",
    )
    fig.update_traces(texttemplate="%{y:.1f}", textposition="inside")
    fig.update_layout(
        template="plotly_white",
        legend_title_text="",
        legend=dict(traceorder="reversed"),
        uniformtext_minsize=10,
        uniformtext_mode="hide",
    )
    return fig


def monthly_trend_chart(df):
    monthly = df.copy()
    monthly["Month"] = monthly["FlightDate"].dt.to_period("M").astype(str)

    all_routes = summarize(monthly, ["Month", "Hub"]).reset_index()
    all_routes["Series"] = all_routes["Hub"].map(
        {"PAE": "PAE (all routes)", "SEA": "SEA (all 8 routes)"}
    )

    pae_no_sfo = summarize(
        monthly[(monthly["Hub"] == "PAE") & (monthly["Partner"] != "SFO")],
        ["Month"],
    ).reset_index()
    pae_no_sfo["Series"] = "PAE (excl. SFO)"

    trend = pd.concat(
        [
            pae_no_sfo[["Month", "Series", "flights", "on_time_pct", "cancel_pct"]],
            all_routes[["Month", "Series", "flights", "on_time_pct", "cancel_pct"]],
        ],
        ignore_index=True,
    ).sort_values("Month")

    fig = px.line(
        trend,
        x="Month",
        y="on_time_pct",
        color="Series",
        line_dash="Series",
        markers=True,
        category_orders={
            "Series": ["PAE (excl. SFO)", "SEA (all 8 routes)", "PAE (all routes)"]
        },
        color_discrete_map={
            "PAE (excl. SFO)": PAE_COLOR,
            "PAE (all routes)": PAE_COLOR,
            "SEA (all 8 routes)": SEA_COLOR,
        },
        line_dash_map={
            "PAE (excl. SFO)": "solid",
            "PAE (all routes)": "dash",
            "SEA (all 8 routes)": "solid",
        },
        hover_data=["flights", "cancel_pct"],
        labels={
            "Month": "",
            "on_time_pct": "On-Time Arrival Rate (%)",
            "Series": "",
        },
        title="Monthly On-Time Rate (Oct 2025 – Sep 2026): The SFO Effect Over Time",
    )
    fig.update_traces(line=dict(width=2.5), marker=dict(size=7))
    fig.update_layout(
        template="plotly_white",
        legend_title_text="",
        hovermode="x unified",
        yaxis=dict(ticksuffix="%"),
    )
    return fig


if __name__ == "__main__":
    df = load_data()
    OUT_DIR.mkdir(exist_ok=True)

    fig1 = route_on_time_chart(df)
    fig1.write_html(OUT_DIR / "route_reliability.html")

    fig2 = sfo_delay_causes_chart(df)
    fig2.write_html(OUT_DIR / "sfo_delay_causes.html")

    fig3 = monthly_trend_chart(df)
    fig3.write_html(OUT_DIR / "monthly_trend.html")
    fig3.show()