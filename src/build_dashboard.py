from pathlib import Path
from charts import (
    PAE_COLOR,
    SEA_COLOR,
    monthly_trend_chart,
    route_on_time_chart,
    sfo_delay_causes_chart,
)
from metrics import load_data, summarize

DASHBOARD_DIR = Path("dashboard")


def chart_div(fig, include_js=False):
    fig.update_layout(
        margin=dict(t=60, r=20, b=40, l=70),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn" if include_js else False,
        config={"responsive": True, "displayModeBar": False},
    )


def build():
    df = load_data()
    DASHBOARD_DIR.mkdir(exist_ok=True)

    overall = summarize(df, ["Hub"])
    pae = overall.loc["PAE"]
    sea = overall.loc["SEA"]

    pae_no_sfo = summarize(
        df[(df["Hub"] == "PAE") & (df["Partner"] != "SFO")], ["Hub"]
    ).loc["PAE"]

    qx_pct = (
        ((df["Hub"] == "PAE") & (df["Operating_Airline"] == "QX")).sum()
        / (df["Hub"] == "PAE").sum()
        * 100
    )

    date_start = df["FlightDate"].min().strftime("%b %Y")
    date_end = df["FlightDate"].max().strftime("%b %Y")

    c1 = chart_div(route_on_time_chart(df), include_js=True)
    c2 = chart_div(sfo_delay_causes_chart(df))
    c3 = chart_div(monthly_trend_chart(df))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Paine Field (PAE) vs. Sea-Tac (SEA) Flight Reliability</title>
  <style>
    :root {{
      --pae: {PAE_COLOR};
      --sea: {SEA_COLOR};
      --bg: #f8fafc;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --border: #e2e8f0;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    .wrap {{ max-width: 1080px; margin: 0 auto; padding: 32px 20px 56px; }}
    header {{ margin-bottom: 24px; }}
    h1 {{ margin: 0 0 6px; font-size: 1.75rem; letter-spacing: -0.02em; }}
    .subtitle {{ margin: 0; color: var(--muted); font-size: 0.98rem; }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 14px;
      margin: 24px 0;
    }}
    .kpi {{
      background: var(--card);
      border: 1px solid var(--border);
      border-top: 4px solid var(--border);
      border-radius: 10px;
      padding: 16px 18px;
    }}
    .kpi.pae {{ border-top-color: var(--pae); }}
    .kpi.sea {{ border-top-color: var(--sea); }}
    .kpi-label {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }}
    .kpi-value {{ font-size: 1.85rem; font-weight: 700; margin: 4px 0; }}
    .kpi-note {{ font-size: 0.82rem; color: var(--muted); }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px 20px 14px;
      margin-bottom: 20px;
    }}
    .caption {{ margin: 8px 4px 0; font-size: 0.85rem; color: var(--muted); }}
    footer {{
      margin-top: 28px;
      padding-top: 18px;
      border-top: 1px solid var(--border);
      font-size: 0.84rem;
      color: var(--muted);
    }}
    footer p {{ margin: 6px 0; }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Paine Field (PAE) vs. Sea-Tac (SEA) Reliability</h1>
      <p class="subtitle">
        Comparing on-time arrivals, cancellations, and delay causes across the 8 shared West Coast destinations
        ({date_start} – {date_end} · {len(df):,} scheduled flights).
      </p>
    </header>

    <section class="kpis">
      <div class="kpi pae">
        <div class="kpi-label">PAE On-Time (All 8 Routes)</div>
        <div class="kpi-value">{pae['on_time_pct']:.1f}%</div>
        <div class="kpi-note">{int(pae['flights']):,} flights · {pae['cancel_pct']:.2f}% cancelled</div>
      </div>
      <div class="kpi pae">
        <div class="kpi-label">PAE On-Time (Excl. SFO)</div>
        <div class="kpi-value">{pae_no_sfo['on_time_pct']:.1f}%</div>
        <div class="kpi-note">{int(pae_no_sfo['flights']):,} flights · {pae_no_sfo['cancel_pct']:.2f}% cancelled</div>
      </div>
      <div class="kpi sea">
        <div class="kpi-label">SEA On-Time (Same 8 Routes)</div>
        <div class="kpi-value">{sea['on_time_pct']:.1f}%</div>
        <div class="kpi-note">{int(sea['flights']):,} flights · {sea['cancel_pct']:.2f}% cancelled</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Horizon Air (QX) Share at PAE</div>
        <div class="kpi-value">{qx_pct:.1f}%</div>
        <div class="kpi-note">Why BTS Marketing Carrier data is required</div>
      </div>
    </section>

    <section class="card">
      {c1}
      <p class="caption">
        PAE beats SEA on 4 of 8 routes (PHX, PDX, LAX, LAS), but SFO makes up nearly 1 in 5 PAE flights and drags PAE's headline rate below SEA.
      </p>
    </section>

    <section class="card">
      {c2}
      <p class="caption">
        BTS splits delays into causes only for flights arriving 15+ minutes late (on-time and early flights count as 0).
        Each slice shows average 15+ minute delay minutes per completed flight from that cause. Outbound PAE → SFO airspace holds
        turn directly into inbound SFO → PAE late-arriving-aircraft delays when the same Horizon jet turns around.
      </p>
    </section>

    <section class="card">
      {c3}
      <p class="caption">
        Excluding SFO, Paine Field beat Sea-Tac in 11 of 12 months. During SFO's spring and summer marine-layer season (Apr–Aug),
        that single route pulls Paine Field's overall on-time rate down by up to ~13 percentage points.
      </p>
    </section>

    <footer>
      <p><strong>Data source:</strong> U.S. DOT Bureau of Transportation Statistics (BTS) Marketing Carrier On-Time Performance, {date_start} – {date_end} (data lags ~2 months).</p>
      <p><strong>Definitions:</strong> A flight is on time if it arrives less than 15 minutes late. Destinations reflect active PAE commercial routes (LAS, LAX, PDX, PHX, PSP seasonal, SAN, SFO, SNA).</p>
    </footer>
  </div>
</body>
</html>
"""

    out_path = DASHBOARD_DIR / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Built {out_path} ({out_path.stat().st_size / 1000:.1f} KB)")


if __name__ == "__main__":
    build()