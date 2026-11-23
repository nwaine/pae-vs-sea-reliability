const HEADERS = {
  "User-Agent": "pae-vs-sea-reliability (portfolio project by Nick Waine)",
};

const COMMERCIAL_CATS = new Set(["A3", "A4", "A5"]);

async function fetchJson(url, timeoutMs = 8000) {
  const res = await fetch(url, {
    headers: HEADERS,
    signal: AbortSignal.timeout(timeoutMs),
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

function isCommercial(a) {
  const flight = (a.flight || "").trim();
  return /^[A-Z]{3}\d/.test(flight) && COMMERCIAL_CATS.has(a.category);
}

function buildBucket(list) {
  const airborne = list.filter((a) => typeof a.alt_baro === "number");
  const sample = airborne
    .filter((a) => a.flight && a.flight.trim())
    .sort((a, b) => a.alt_baro - b.alt_baro)
    .slice(0, 5)
    .map((a) => ({
      callsign: a.flight.trim(),
      type: a.t || "—",
      alt: a.alt_baro,
      commercial: isCommercial(a),
    }));
  return { total: list.length, airborne: airborne.length, sample };
}

function summarizeTraffic(data) {
  const ac = data?.ac ?? [];
  return {
    all: buildBucket(ac),
    commercial: buildBucket(ac.filter(isCommercial)),
  };
}

function nearPugetSound(ap) {
  if (!ap || typeof ap.latitude !== "number" || typeof ap.longitude !== "number") return false;
  return Math.abs(ap.latitude - 47.65) < 1.5 && Math.abs(ap.longitude - -122.3) < 2.0;
}

async function lookupRoutes(traffic) {
  const callsigns = new Set();
  for (const hub of Object.values(traffic)) {
    if (!hub) continue;
    for (const bucket of [hub.all, hub.commercial]) {
      for (const plane of bucket?.sample ?? []) {
        if (plane.commercial) callsigns.add(plane.callsign);
      }
    }
  }

  const routes = {};
  await Promise.allSettled(
    [...callsigns].map(async (cs) => {
      try {
        const data = await fetchJson(`https://api.adsbdb.com/v0/callsign/${encodeURIComponent(cs)}`, 2500);
        const fr = data?.response?.flightroute;
        if (!fr?.origin?.iata_code || !fr?.destination?.iata_code) return;
        if (!nearPugetSound(fr.origin) && !nearPugetSound(fr.destination)) return;
        routes[cs] = `${fr.origin.iata_code}→${fr.destination.iata_code}`;
      } catch {
        // Skip unknown or slow route lookups cleanly
      }
    })
  );

  for (const hub of Object.values(traffic)) {
    if (!hub) continue;
    for (const bucket of [hub.all, hub.commercial]) {
      for (const plane of bucket?.sample ?? []) {
        if (routes[plane.callsign]) plane.route = routes[plane.callsign];
        delete plane.commercial;
      }
    }
  }
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

  await lookupRoutes(traffic);

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