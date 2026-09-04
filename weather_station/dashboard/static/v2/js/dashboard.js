/* ==========================================================
   ATMOSLINK UI V2
   Executive Dashboard controller
   ========================================================== */

import { loadOverview } from "./overview.js";

const REFRESH_INTERVAL_MS = 10000;

function byId(id) {
  return document.getElementById(id);
}

function setText(id, value, fallback = "—") {
  const element = byId(id);

  if (!element) {
    return;
  }

  element.textContent =
    value === null ||
    value === undefined ||
    value === ""
      ? fallback
      : String(value);
}

function formatNumber(
  value,
  {
    digits = 1,
    fallback = "—"
  } = {}
) {
  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    return fallback;
  }

  return new Intl.NumberFormat("es-PE", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  }).format(parsed);
}

function formatDateTime(value) {
  if (!value || value === "—") {
    return "—";
  }

  const normalized = String(value).includes("T")
    ? String(value)
    : String(value).replace(" ", "T");

  const date = new Date(normalized);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat("es-PE", {
    dateStyle: "short",
    timeStyle: "medium"
  }).format(date);
}

function normalizeState(value) {
  return String(value ?? "UNKNOWN")
    .trim()
    .toUpperCase();
}

function stateVariant(value) {
  const state = normalizeState(value);

  if (
    [
      "HEALTHY",
      "OK",
      "FRESH",
      "CURRENT",
      "ACTIVE",
      "ONLINE",
      "AVAILABLE",
      "NO_RAIN"
    ].includes(state)
  ) {
    return "success";
  }

  if (
    [
      "WAITING",
      "STALE",
      "DEGRADED",
      "DELAYED",
      "OBSERVING",
      "WARNING"
    ].includes(state)
  ) {
    return "warning";
  }

  if (
    [
      "CRITICAL",
      "ERROR",
      "FAILED",
      "OFFLINE",
      "UNHEALTHY"
    ].includes(state)
  ) {
    return "danger";
  }

  if (
    [
      "NOT_INSTALLED",
      "DISABLED",
      "NOT_ENABLED"
    ].includes(state)
  ) {
    return "disabled";
  }

  return "info";
}

function setStatus(id, value) {
  const element = byId(id);

  if (!element) {
    return;
  }

  const state = normalizeState(value);
  element.textContent = state;
  element.className =
    `atl-status atl-status--${stateVariant(state)}`;
}

function renderStatusCards(overview) {
  setStatus("platformStatus", overview.health.status);

  setText(
    "platformStatusDetail",
    overview.health.latestError
      ? String(overview.health.latestError)
      : `Base de datos: ${overview.health.databaseStatus}`
  );

  setStatus(
    "observationStatus",
    overview.health.operationalState
  );

  setText(
    "observationStatusDetail",
    overview.health.observationAgeLabel
  );

  const scientificAvailable =
    overview.quality.era5 === "OK" &&
    overview.quality.nasaPower === "OK";

  setStatus(
    "scientificStatus",
    scientificAvailable
      ? "AVAILABLE"
      : "DEGRADED"
  );

  setText(
    "scientificStatusDetail",
    `ERA5 ${overview.quality.era5} · NASA ${overview.quality.nasaPower}`
  );

  setStatus(
    "radioStatus",
    overview.quality.radioLink
  );

  setText(
    "radioStatusDetail",
    overview.sources.radio.note
  );
}

function renderMetrics(overview) {
  setText(
    "metricTemperature",
    formatNumber(overview.weather.temperatureC)
  );

  setText(
    "metricHumidity",
    formatNumber(overview.weather.humidityPct)
  );

  setText(
    "metricPressure",
    formatNumber(overview.weather.pressureHpa)
  );

  setText(
    "metricDewPoint",
    formatNumber(overview.weather.dewPointC)
  );

  setText(
    "metricRainHour",
    formatNumber(
      overview.weather.rainHourMm,
      { digits: 2 }
    )
  );

  setText(
    "metricRainTotal",
    formatNumber(
      overview.weather.rainTotalMm,
      { digits: 2 }
    )
  );

  setText(
    "metricRainState",
    overview.weather.rainState
  );
}

function renderSources(overview) {
  const sourceMap = [
    ["sourceLocal", overview.sources.local],
    ["sourceEra5", overview.sources.era5],
    ["sourceNasa", overview.sources.nasa],
    ["sourceRadio", overview.sources.radio]
  ];

  sourceMap.forEach(([prefix, source]) => {
    setText(
      `${prefix}Time`,
      formatDateTime(source.timestamp)
    );

    setText(
      `${prefix}Age`,
      source.age ?? source.note ?? "—"
    );

    setStatus(
      `${prefix}Status`,
      source.status
    );
  });
}

function renderAlerts(overview) {
  const container = byId("alertList");

  if (!container) {
    return;
  }

  container.replaceChildren();

  if (!overview.alerts.length) {
    const empty = document.createElement("div");
    empty.className = "atl-empty";
    empty.textContent =
      "No existen alertas activas.";
    container.appendChild(empty);
    return;
  }

  overview.alerts.forEach((alert) => {
    const article = document.createElement("article");
    article.className =
      `atl-alert atl-alert--${alert.severity}`;

    const title = document.createElement("div");
    title.className = "atl-alert__title";
    title.textContent = alert.title;

    const message = document.createElement("p");
    message.className = "atl-alert__message";
    message.textContent = alert.message;

    article.append(title, message);
    container.appendChild(article);
  });
}

function renderStations(overview) {
  const tbody = byId("stationTableBody");

  if (!tbody) {
    return;
  }

  tbody.replaceChildren();

  if (!overview.stations.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");

    cell.colSpan = 5;
    cell.textContent =
      "No hay estaciones disponibles.";

    row.appendChild(cell);
    tbody.appendChild(row);
    return;
  }

  overview.stations.forEach((station) => {
    const row = document.createElement("tr");

    const stationCell =
      document.createElement("td");

    stationCell.textContent =
      `${station.id} · ${station.name}`;

    const statusCell =
      document.createElement("td");

    const status = document.createElement("span");

    status.className =
      `atl-status atl-status--${stateVariant(station.status)}`;

    status.textContent =
      normalizeState(station.status);

    statusCell.appendChild(status);

    const temperatureCell =
      document.createElement("td");

    temperatureCell.textContent =
      `${formatNumber(station.temperature)} °C`;

    const humidityCell =
      document.createElement("td");

    humidityCell.textContent =
      `${formatNumber(station.humidity)} %`;

    const timestampCell =
      document.createElement("td");

    timestampCell.textContent =
      formatDateTime(station.timestamp);

    row.append(
      stationCell,
      statusCell,
      temperatureCell,
      humidityCell,
      timestampCell
    );

    tbody.appendChild(row);
  });
}

function renderMeta(overview) {
  setText(
    "heroStation",
    `${overview.station.id} · ${overview.station.name}`
  );

  setText(
    "heroRole",
    overview.station.role
  );

  setText(
    "heroVersion",
    overview.meta.version
  );

  setText(
    "topbarStation",
    `${overview.station.id} · ${overview.station.name}`
  );

  setText(
    "lastObservation",
    formatDateTime(
      overview.health.latestObservation
    )
  );

  setText(
    "dashboardUpdatedAt",
    formatDateTime(
      overview.meta.checkedAt
    )
  );

  setText(
    "alertCount",
    overview.alertCount
  );
}

function renderFetchErrors(overview) {
  const notice = byId("partialDataNotice");

  if (!notice) {
    return;
  }

  if (!overview.partial) {
    notice.hidden = true;
    notice.textContent = "";
    return;
  }

  notice.hidden = false;

  notice.textContent =
    "Carga parcial: " +
    overview.fetchErrors
      .map((error) => error.source)
      .join(", ");
}

function setLoading(isLoading) {
  const root = byId("dashboardRoot");

  if (!root) {
    return;
  }

  root.classList.toggle(
    "atl-loading",
    isLoading
  );
}

async function refreshDashboard() {
  setLoading(true);

  try {
    const overview = await loadOverview();

    renderMeta(overview);
    renderStatusCards(overview);
    renderMetrics(overview);
    renderSources(overview);
    renderAlerts(overview);
    renderStations(overview);
    renderFetchErrors(overview);

    setText(
      "dashboardConnectionState",
      overview.partial
        ? "DATOS PARCIALES"
        : "EN LÍNEA"
    );
  } catch (error) {
    console.error(
      "AtmosLink UI v2 update failed:",
      error
    );

    setText(
      "dashboardConnectionState",
      "ERROR DE CONEXIÓN"
    );

    const notice =
      byId("partialDataNotice");

    if (notice) {
      notice.hidden = false;
      notice.textContent =
        error?.message ??
        "No fue posible actualizar el dashboard.";
    }
  } finally {
    setLoading(false);
  }
}

document.addEventListener(
  "DOMContentLoaded",
  () => {
    refreshDashboard();

    window.setInterval(
      refreshDashboard,
      REFRESH_INTERVAL_MS
    );
  }
);
