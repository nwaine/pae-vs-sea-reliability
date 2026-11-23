const HEADERS = {
  "User-Agent": "pae-vs-sea-reliability (portfolio project by Nick Waine)",
};

async function fetchJson(url) {
  const res = await fetch(url, {
    headers: HEADERS,
    signal: AbortSignal.timeout(8000),
  });
  if (!res.ok) throw new Error(`${res.status} for ${url}`);
  return res.json();
}

function formatWind(m) {
  if (!m.wspd) return "Calm";
  const dir = m.wdir === "VRB" ? "VRB" : `${String(m.wdir ?? 0).padStart(3, "0")}°`;
  const gust = m.wgst ? `G${m.wgst}` : "";
  return `${dir} @ ${m.wspd}${gust} kt`;
}

function summarizeTraffic(data) {
  const ac = data?.ac ?? [];
  const airborne = ac.filter((a) => typeof a.alt_baro === "number");
  const sample = airborne
    .filter((a) => a.flight && a.flight.trim())
    .sort((a, b) => a.alt_baro - b.alt_baro)
    .slice(0, 5)
    .map((a) => ({
      callsign: a.flight.trim(),
      type: a.t || "—",
      alt: a.alt_baro,
    }));
  return { total: ac.length, airborne: airborne.length, sample };
}

function summarizeFaa(events, code) {
  const e = (events ?? []).find((item) => item.airportId === code);
  if (!e) return "No FAA delays reported";
  if (e.airportClosure) return "Airport closure";
  if (e.groundStop) return "Ground Stop active";
  if (e.groundDelay) return "Ground Delay Program active";
  if (e.arrivalDelay) return "Arrival delays active";
  if (e.departureDelay) return "Departure delays active";
  return "No FAA delays reported";
}

export default async () => {
  const [metarRes, faaRes, paeRes, seaRes] = await Promise.allSettled([
    fetchJson("https://aviationweather.gov/api/data/metar?ids=KPAE,KSEA,KSFO&format=json"),
    fetchJson("https://nasstatus.faa.gov/api/airport-events"),
    fetchJson("https://api.adsb.lol/v2/lat/47.9063/lon/-122.2815/dist/15"),
    fetchJson("https://api.adsb.lol/v2/lat/47.4502/lon/-122.3088/dist/15"),
  ]);

  const weather = {};
  if (metarRes.status === "fulfilled") {
    for (const m of metarRes.value) {
      const code = m.icaoId.slice(1);
      weather[code] = {
        fltCat: m.fltCat || "—",
        tempF: typeof m.temp === "number" ? Math.round((m.temp * 9) / 5 + 32) : null,
        wind: formatWind(m),
        visib: m.visib ? `${m.visib} SM` : "—",
        rawOb: m.rawOb || "",
      };
    }
  }

  const faaEvents = faaRes.status === "fulfilled" ? faaRes.value : [];
  const faa = {
    PAE: summarizeFaa(faaEvents, "PAE"),
    SEA: summarizeFaa(faaEvents, "SEA"),
    SFO: summarizeFaa(faaEvents, "SFO"),
  };

  const traffic = {
    PAE: paeRes.status === "fulfilled" ? summarizeTraffic(paeRes.value) : null,
    SEA: seaRes.status === "fulfilled" ? summarizeTraffic(seaRes.value) : null,
  };

  return new Response(
    JSON.stringify({ updatedAt: new Date().toISOString(), weather, faa, traffic }),
    {
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=60",
      },
    }
  );
};