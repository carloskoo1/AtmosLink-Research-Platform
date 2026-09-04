/* ==========================================================
   ATMOSLINK UI V2
   Overview data adapter
   ========================================================== */

const ENDPOINTS = Object.freeze({
  latest: "/api/latest",
  health: "/api/health",
  coreStatus: "/api/core/status",
  stations: "/api/stations/latest"
});

async function fetchJson(url) {
  const response = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`${url} respondió HTTP ${response.status}`);
  }

  return response.json();
}

function text(value, fallback = "—") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

function number(value, fallback = null) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function upper(value, fallback = "UNKNOWN") {
  return text(value, fallback).trim().toUpperCase();
}

function normalizeQuality(latest) {
  const quality = latest?.scientific_quality ?? {};

  return {
    bme280: upper(quality.bme280),
    rainGauge: upper(quality.rain_gauge),
    anemometer: upper(
      quality.anemometer,
      latest?.wind_state ?? "UNKNOWN"
    ),
    era5: upper(quality.era5),
    nasaPower: upper(quality.nasa_power),
    radioLink: upper(quality.radio_link)
  };
}

function normalizeAlerts(coreStatus) {
  const source = coreStatus?.alerts?.alerts;

  if (!Array.isArray(source)) {
    return [];
  }

  return source.map((alert, index) => ({
    id: text(alert?.id, `alert-${index}`),
    title: text(alert?.title, "Alerta"),
    message: text(
      alert?.message,
      "Sin descripción disponible"
    ),
    severity: text(
      alert?.severity,
      "info"
    ).toLowerCase()
  }));
}

function normalizeStations(stations) {
  if (!Array.isArray(stations)) {
    return [];
  }

  return stations.map((station, index) => ({
    id: text(
      station?.station_id ?? station?.id,
      `station-${index}`
    ),
    name: text(
      station?.station_name ?? station?.name,
      "Estación sin nombre"
    ),
    timestamp: text(
      station?.timestamp_local ??
      station?.weather_timestamp_local ??
      station?.latest_observation
    ),
    status: upper(
      station?.observation_state ??
      station?.operational_state ??
      station?.status
    ),
    temperature: number(
      station?.temp_avg_C ??
      station?.local_temp_avg_c
    ),
    humidity: number(
      station?.hum_avg_pct ??
      station?.local_hum_avg_pct
    )
  }));
}

function normalizeOverview({
  latest,
  health,
  coreStatus,
  stations
}) {
  return {
    meta: {
      platform: text(
        health?.platform,
        "AtmosLink Research Platform"
      ),
      version: text(health?.version),
      checkedAt: text(health?.checked_at_local)
    },

    station: {
      id: text(
        health?.station_id ??
        latest?.station_id
      ),
      name: text(
        health?.station_name ??
        latest?.station_name
      ),
      role: text(latest?.radio_role)
    },

    health: {
      status: upper(health?.status),
      operationalState: upper(
        health?.operational_state
      ),
      observationAgeSeconds: number(
        health?.observation_age_seconds ??
        latest?.observation_age_seconds
      ),
      observationAgeLabel: text(
        latest?.observation_age_label
      ),
      latestObservation: text(
        health?.latest_observation ??
        latest?.timestamp_local
      ),
      databaseStatus: upper(
        health?.database?.status
      ),
      latestError: health?.latest_error ?? null
    },

    weather: {
      temperatureC: number(
        latest?.local_temp_avg_c ??
        latest?.temp_avg_C
      ),
      humidityPct: number(
        latest?.local_hum_avg_pct ??
        latest?.hum_avg_pct
      ),
      pressureHpa: number(
        latest?.local_press_hpa ??
        latest?.pres_avg_hPa
      ),
      dewPointC: number(
        latest?.local_dew_point_c ??
        latest?.dew_point_C
      ),
      rainHourMm: number(
        latest?.local_rain_1h_mm ??
        latest?.rain_1h_mm
      ),
      rainTotalMm: number(
        latest?.local_rain_total_mm ??
        latest?.rain_total_mm
      ),
      rainState: upper(latest?.rain_state),
      timestamp: text(
        latest?.weather_timestamp_local ??
        latest?.timestamp_local
      )
    },

    sources: {
      local: {
        status: upper(latest?.observation_state),
        timestamp: text(
          latest?.weather_timestamp_local ??
          latest?.timestamp_local
        ),
        age: text(latest?.observation_age_label)
      },

      era5: {
        status: upper(
          latest?.scientific_quality?.era5
        ),
        timestamp: text(
          latest?.era5_timestamp_local
        ),
        age: text(latest?.era5_age_label)
      },

      nasa: {
        status: upper(
          latest?.scientific_quality?.nasa_power
        ),
        timestamp: text(
          latest?.nasa_timestamp_local
        ),
        age: text(latest?.nasa_age_label)
      },

      radio: {
        status: upper(
          latest?.scientific_quality?.radio_link
        ),
        timestamp: text(
          latest?.radio_timestamp_local
        ),
        note: text(
          latest?.radio_note,
          "Sin información"
        )
      }
    },

    quality: normalizeQuality(latest),
    alerts: normalizeAlerts(coreStatus),
    alertCount: number(
      coreStatus?.alerts?.alert_count,
      0
    ),
    stations: normalizeStations(stations)
  };
}

export async function loadOverview() {
  const results = await Promise.allSettled([
    fetchJson(ENDPOINTS.latest),
    fetchJson(ENDPOINTS.health),
    fetchJson(ENDPOINTS.coreStatus),
    fetchJson(ENDPOINTS.stations)
  ]);

  const names = [
    "latest",
    "health",
    "coreStatus",
    "stations"
  ];

  const payload = {};
  const errors = [];

  results.forEach((result, index) => {
    const name = names[index];

    if (result.status === "fulfilled") {
      payload[name] = result.value;
      return;
    }

    payload[name] = name === "stations" ? [] : {};

    errors.push({
      source: name,
      message:
        result.reason?.message ??
        "Error de consulta"
    });
  });

  const overview = normalizeOverview(payload);
  overview.fetchErrors = errors;
  overview.partial = errors.length > 0;

  return overview;
}
