from datetime import datetime, timezone
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

STYLES = """
    :root {
      --pae: __PAE__;
      --sea: __SEA__;
      --bg: #f8fafc;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --border: #e2e8f0;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }
    .wrap { max-width: 1080px; margin: 0 auto; padding: 32px 20px 56px; }
    header { margin-bottom: 22px; }
    h1 { margin: 0 0 6px; font-size: 1.75rem; letter-spacing: -0.02em; }
    .subtitle { margin: 0; color: var(--muted); font-size: 0.98rem; }

    .live-section {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 18px;
      margin: 20px 0 22px;
    }
    .live-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }
    .live-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.86rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #16a34a;
      display: inline-block;
    }
    .live-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      font-size: 0.8rem;
      color: var(--muted);
    }
    .seg {
      display: inline-flex;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 2px;
      gap: 2px;
    }
    .seg-btn {
      border: none;
      background: transparent;
      border-radius: 6px;
      padding: 3px 9px;
      font-size: 0.76rem;
      font-weight: 500;
      color: var(--muted);
      cursor: pointer;
    }
    .seg-btn.active {
      background: var(--card);
      color: var(--text);
      font-weight: 600;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
    }
    .refresh-btn {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 4px 10px;
      font-size: 0.78rem;
      color: var(--text);
      cursor: pointer;
    }
    .refresh-btn:hover { background: #eef2f6; }
    .live-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
    }
    .live-card {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 14px;
    }
    .live-card-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }
    .airport-code { font-weight: 700; font-size: 0.98rem; }
    .airport-name { color: var(--muted); font-weight: 400; font-size: 0.85rem; margin-left: 6px; }
    .cat-pill {
      font-size: 0.72rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 999px;
      letter-spacing: 0.03em;
    }
    .cat-vfr { background: #dcfce7; color: #166534; }
    .cat-mvfr { background: #dbeafe; color: #1d4ed8; }
    .cat-ifr { background: #fee2e2; color: #b91c1c; }
    .cat-lifr { background: #f3e8ff; color: #7e22ce; }
    .cat-unk { background: #e2e8f0; color: #475569; }
    .wx-line { font-size: 0.88rem; margin: 4px 0; }
    .faa-line { font-size: 0.82rem; color: var(--muted); margin: 4px 0; }
    .faa-alert { color: #b45309; font-weight: 600; }
    .traffic-box {
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid var(--border);
      font-size: 0.8rem;
      color: var(--muted);
    }
    .flights-list {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-top: 6px;
    }
    .flight-chip {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.72rem;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 5px;
      padding: 2px 6px;
      color: var(--text);
    }
    .flight-route {
      font-weight: 700;
      color: var(--pae);
    }
    .live-note { font-size: 0.85rem; color: var(--muted); margin: 0; }

    .kpis {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 14px;
      margin: 22px 0;
    }
    .kpi {
      background: var(--card);
      border: 1px solid var(--border);
      border-top: 4px solid var(--border);
      border-radius: 10px;
      padding: 16px 18px;
    }
    .kpi.pae { border-top-color: var(--pae); }
    .kpi.sea { border-top-color: var(--sea); }
    .kpi-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }
    .kpi-value { font-size: 1.85rem; font-weight: 700; margin: 4px 0; }
    .kpi-note { font-size: 0.82rem; color: var(--muted); }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px 20px 14px;
      margin-bottom: 20px;
    }
    .caption { margin: 8px 4px 0; font-size: 0.85rem; color: var(--muted); }
    footer {
      margin-top: 28px;
      padding-top: 18px;
      border-top: 1px solid var(--border);
      font-size: 0.84rem;
      color: var(--muted);
    }
    footer p { margin: 6px 0; }
"""

LIVE_SCRIPT = """
<script>
  const AIRPORTS = [
    { code: "PAE", name: "Paine Field" },
    { code: "SEA", name: "Sea-Tac" },
    { code: "SFO", name: "San Francisco" },
  ];

  let trafficFilter = "all";
  let lastLiveData = null;

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function catClass(cat) {
    const map = { VFR: "cat-vfr", MVFR: "cat-mvfr", IFR: "cat-ifr", LIFR: "cat-lifr" };
    return map[cat] || "cat-unk";
  }

  function renderTraffic(code, traffic) {
    if (code === "SFO") {
      return '<div class="traffic-box">Tracked here because SFO airspace holds drive PAE delays.</div>';
    }
    if (!traffic) return "";
    const bucket = traffic[trafficFilter] || traffic;
    const label = trafficFilter === "commercial" ? "commercial airborne" : "airborne";

    if (bucket.airborne === 0) {
      const emptyMsg = trafficFilter === "commercial"
        ? `No commercial flights airborne (${bucket.total} total within 15 nm)`
        : `No aircraft airborne (${bucket.total} within 15 nm)`;
      return `<div class="traffic-box"><div>${emptyMsg}</div></div>`;
    }

    const chips = (bucket.sample || [])
      .map((a) => {
        const route = a.route ? ` · <span class="flight-route">${esc(a.route)}</span>` : "";
        return `<span class="flight-chip">${esc(a.callsign)}${route} · ${esc(a.type)} · ${Number(a.alt).toLocaleString()} ft</span>`;
      })
      .join("");
    return `
      <div class="traffic-box">
        <div><strong>${bucket.airborne}</strong> ${label} (${bucket.total} within 15 nm)</div>
        ${chips ? `<div class="flights-list">${chips}</div>` : ""}
      </div>
    `;
  }

  function renderLive(data) {
    const grid = document.getElementById("live-grid");
    grid.innerHTML = AIRPORTS.map(({ code, name }) => {
      const wx = data.weather?.[code];
      const faa = data.faa?.[code] || "No FAA delays reported";
      const faaCls = faa === "No FAA delays reported" ? "faa-line" : "faa-line faa-alert";
      const cat = wx?.fltCat || "—";
      const temp = wx?.tempF != null ? `${wx.tempF}°F` : "—";
      const wxText = wx
        ? `${temp} · Wind ${esc(wx.wind)} · Vis ${esc(wx.visib)}`
        : "Weather unavailable";

      return `
        <div class="live-card">
          <div class="live-card-top">
            <div><span class="airport-code">${code}</span><span class="airport-name">${name}</span></div>
            <span class="cat-pill ${catClass(cat)}">${esc(cat)}</span>
          </div>
          <div class="wx-line" title="${esc(wx?.rawOb || "")}">${wxText}</div>
          <div class="${faaCls}">FAA: ${esc(faa)}</div>
          ${renderTraffic(code, data.traffic?.[code])}
        </div>
      `;
    }).join("");
  }

  async function loadLive() {
    const grid = document.getElementById("live-grid");
    const updated = document.getElementById("live-updated");

    if (window.location.protocol === "file:") {
      grid.innerHTML = '<p class="live-note">Live NOAA weather, FAA delay status, and nearby aircraft activate automatically once deployed on Netlify.</p>';
      updated.textContent = "Local preview";
      return;
    }

    updated.textContent = "Refreshing...";
    try {
      const res = await fetch("/.netlify/functions/live");
      if (!res.ok) throw new Error("Feed error " + res.status);
      lastLiveData = await res.json();
      renderLive(lastLiveData);

      const t = new Date(lastLiveData.updatedAt);
      updated.textContent = "Updated " + t.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    } catch (err) {
      grid.innerHTML = '<p class="live-note">Live conditions temporarily unavailable. Historical reliability charts below are unaffected.</p>';
      updated.textContent = "Offline";
    }
  }

  document.querySelectorAll(".seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      trafficFilter = btn.dataset.filter;
      document.querySelectorAll(".seg-btn").forEach((b) => {
        const active = b === btn;
        b.classList.toggle("active", active);
        b.setAttribute("aria-pressed", String(active));
      });
      if (lastLiveData) renderLive(lastLiveData);
    });
  });

  document.getElementById("live-refresh").addEventListener("click", loadLive);
  loadLive();
</script>
"""


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

    routes = summarize(df, ["Partner", "Hub"]).unstack("Hub")["on_time_pct"]
    pae_wins = (
        routes[routes["PAE"] > routes["SEA"]]
        .sort_values("PAE", ascending=False)
        .index.tolist()
    )
    sfo_share = (
        ((df["Hub"] == "PAE") & (df["Partner"] == "SFO")).sum()
        / (df["Hub"] == "PAE").sum()
        * 100
    )

    monthly = df.copy()
    monthly["Month"] = monthly["FlightDate"].dt.to_period("M").astype(str)
    m_pae_no_sfo = summarize(
        monthly[(monthly["Hub"] == "PAE") & (monthly["Partner"] != "SFO")], ["Month"]
    )["on_time_pct"]
    m_pae_all = summarize(monthly[monthly["Hub"] == "PAE"], ["Month"])["on_time_pct"]
    m_sea = summarize(monthly[monthly["Hub"] == "SEA"], ["Month"])["on_time_pct"]
    months_won = int((m_pae_no_sfo > m_sea).sum())
    total_months = len(m_pae_no_sfo)
    max_sfo_drag = (m_pae_no_sfo - m_pae_all).max()

    date_start = df["FlightDate"].min().strftime("%b %Y")
    date_end = df["FlightDate"].max().strftime("%b %Y")
    built_date = datetime.now(timezone.utc).strftime("%b %d, %Y")

    c1 = chart_div(route_on_time_chart(df), include_js=True)
    c2 = chart_div(sfo_delay_causes_chart(df))
    c3 = chart_div(monthly_trend_chart(df))

    css = STYLES.replace("__PAE__", PAE_COLOR).replace("__SEA__", SEA_COLOR)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Paine Field (PAE) vs. Sea-Tac (SEA) Flight Reliability</title>
  <style>{css}</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Paine Field (PAE) vs. Sea-Tac (SEA) Reliability</h1>
      <p class="subtitle">
        Comparing on-time arrivals, cancellations, and delay causes across the {len(routes)} shared West Coast destinations
        ({date_start} – {date_end} · {len(df):,} scheduled flights).
      </p>
    </header>

    <section class="live-section">
      <div class="live-header">
        <div class="live-title"><span class="dot"></span>Live Airport Conditions</div>
        <div class="live-meta">
          <div class="seg" role="radiogroup" aria-label="Aircraft filter">
            <button class="seg-btn active" type="button" data-filter="all" aria-pressed="true">All aircraft</button>
            <button class="seg-btn" type="button" data-filter="commercial" aria-pressed="false">Commercial</button>
          </div>
          <span id="live-updated">Loading...</span>
          <button id="live-refresh" class="refresh-btn" type="button">Refresh</button>
        </div>
      </div>
      <div id="live-grid" class="live-grid">
        <p class="live-note">Loading live weather, FAA status, and nearby aircraft...</p>
      </div>
    </section>

    <section class="kpis">
      <div class="kpi pae">
        <div class="kpi-label">PAE On-Time (All {len(routes)} Routes)</div>
        <div class="kpi-value">{pae['on_time_pct']:.1f}%</div>
        <div class="kpi-note">{int(pae['flights']):,} flights · {pae['cancel_pct']:.2f}% cancelled</div>
      </div>
      <div class="kpi pae">
        <div class="kpi-label">PAE On-Time (Excl. SFO)</div>
        <div class="kpi-value">{pae_no_sfo['on_time_pct']:.1f}%</div>
        <div class="kpi-note">{int(pae_no_sfo['flights']):,} flights · {pae_no_sfo['cancel_pct']:.2f}% cancelled</div>
      </div>
      <div class="kpi sea">
        <div class="kpi-label">SEA On-Time (Same {len(routes)} Routes)</div>
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
        PAE beats SEA on {len(pae_wins)} of {len(routes)} routes ({", ".join(pae_wins)}), while SFO makes up {sfo_share:.1f}% of PAE's schedule and drags PAE's headline rate below SEA.
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
        Excluding SFO, Paine Field beat Sea-Tac in {months_won} of {total_months} months. At its peak, the SFO route alone
        pulls Paine Field's monthly on-time rate down by {max_sfo_drag:.1f} percentage points.
      </p>
    </section>

    <footer>
      <p><strong>Historical data:</strong> U.S. DOT Bureau of Transportation Statistics (BTS) Marketing Carrier On-Time Performance, {date_start} – {date_end} (auto-checked weekly; DOT publishes on a ~2-month lag; built {built_date}). A flight is on time if it arrives less than 15 minutes late.</p>
      <p><strong>Live data:</strong> NOAA Aviation Weather (METAR), FAA NAS Status (if PAE is unlisted, no event is reported), nearby aircraft positions via adsb.lol (ODbL), and commercial routes via adsbdb.com.</p>
    </footer>
  </div>
  {LIVE_SCRIPT}
</body>
</html>
"""

    out_path = DASHBOARD_DIR / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Built {out_path} ({out_path.stat().st_size / 1000:.1f} KB)")


if __name__ == "__main__":
    build()