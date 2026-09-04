/*
 * ATMOSLINK_STRICT_STATION_REQUEST_ISOLATION_V2
 *
 * Garantiza que tarjetas y gráficas consulten la misma estación.
 * Cancela solicitudes de la estación anterior durante un cambio.
 */
(function () {
  "use strict";

  const nativeFetch = window.fetch.bind(window);
  const activeControllers = new Set();

  let selectedStation = null;
  let stationGeneration = 0;

  function normalizeStation(value) {
    const station = String(value || "")
      .trim()
      .toUpperCase();

    return station === "CU01" || station === "SJ01"
      ? station
      : null;
  }

  function findStationSelector() {
    const selectors = Array.from(
      document.querySelectorAll("select")
    );

    return selectors.find(function (select) {
      const values = Array.from(select.options || [])
        .map(function (option) {
          return normalizeStation(option.value);
        })
        .filter(Boolean);

      return (
        values.includes("CU01") &&
        values.includes("SJ01")
      );
    }) || null;
  }

  function stationFromPage() {
    const selector = findStationSelector();

    if (selector) {
      const directValue = normalizeStation(selector.value);

      if (directValue) {
        return directValue;
      }

      const option = selector.options[
        selector.selectedIndex
      ];

      const optionText = String(
        option && option.textContent || ""
      ).toUpperCase();

      if (optionText.includes("CU01")) return "CU01";
      if (optionText.includes("SJ01")) return "SJ01";
    }

    const pageText = String(
      document.body && document.body.textContent || ""
    );

    const headerMatch = pageText.match(
      /\b(CU01|SJ01)\s*[·\-:]\s*Cerro/i
    );

    return headerMatch
      ? normalizeStation(headerMatch[1])
      : null;
  }

  function currentStation() {
    return (
      stationFromPage() ||
      selectedStation
    );
  }

  function cancelPreviousStationRequests() {
    activeControllers.forEach(function (controller) {
      try {
        controller.abort();
      } catch (error) {
        console.debug(
          "No fue posible cancelar una consulta anterior.",
          error
        );
      }
    });

    activeControllers.clear();
  }

  function setSelectedStation(station) {
    const normalized = normalizeStation(station);

    if (!normalized) return;

    if (
      selectedStation &&
      selectedStation !== normalized
    ) {
      stationGeneration += 1;
      cancelPreviousStationRequests();
    }

    selectedStation = normalized;
    document.documentElement.dataset.atmosStation =
      normalized;
  }

  function isGeneralLatest(pathname) {
    return (
      pathname === "/api/latest" ||
      pathname.endsWith("/api/latest")
    );
  }

  function isGeneralHistory(pathname) {
    return (
      pathname === "/api/history" ||
      pathname.endsWith("/api/history")
    );
  }

  function buildStationURL(originalURL, station, kind) {
    const target = new URL(
      kind === "latest"
        ? "/api/station/latest"
        : "/api/station/history",
      window.location.origin
    );

    target.searchParams.set(
      "station_id",
      station
    );

    if (kind === "history") {
      const originalLimit =
        originalURL.searchParams.get("limit");

      target.searchParams.set(
        "limit",
        originalLimit || "1440"
      );
    }

    return target;
  }

  async function compatibleHistoryResponse(response) {
    const payload = await response.clone().json();

    const records = Array.isArray(payload)
      ? payload
      : (
          Array.isArray(payload.records)
            ? payload.records
            : []
        );

    const headers = new Headers(response.headers);
    headers.set(
      "Content-Type",
      "application/json; charset=utf-8"
    );
    headers.set(
      "X-AtmosLink-Station-Isolated",
      "1"
    );

    return new Response(
      JSON.stringify(records),
      {
        status: response.status,
        statusText: response.statusText,
        headers: headers
      }
    );
  }

  window.fetch = async function (input, init) {
    let originalURL;

    try {
      const rawURL =
        input instanceof Request
          ? input.url
          : String(input);

      originalURL = new URL(
        rawURL,
        window.location.origin
      );
    } catch (error) {
      return nativeFetch(input, init);
    }

    const latestRequest =
      isGeneralLatest(originalURL.pathname);

    const historyRequest =
      isGeneralHistory(originalURL.pathname);

    if (!latestRequest && !historyRequest) {
      return nativeFetch(input, init);
    }

    const station = currentStation();

    if (!station) {
      return nativeFetch(input, init);
    }

    setSelectedStation(station);

    const requestGeneration = stationGeneration;
    const controller = new AbortController();

    activeControllers.add(controller);

    const options = Object.assign(
      {},
      init || {},
      {
        signal: controller.signal,
        cache: "no-store"
      }
    );

    const targetURL = buildStationURL(
      originalURL,
      station,
      latestRequest ? "latest" : "history"
    );

    try {
      const response = await nativeFetch(
        targetURL.toString(),
        options
      );

      if (
        requestGeneration !== stationGeneration ||
        station !== currentStation()
      ) {
        throw new DOMException(
          "Respuesta de estación anterior descartada.",
          "AbortError"
        );
      }

      if (historyRequest && response.ok) {
        return await compatibleHistoryResponse(
          response
        );
      }

      return response;
    } finally {
      activeControllers.delete(controller);
    }
  };

  function stationFromSelectorEvent(event) {
    const selector = event.target;

    if (
      !selector ||
      selector.tagName !== "SELECT"
    ) {
      return;
    }

    const direct = normalizeStation(selector.value);

    if (direct) {
      setSelectedStation(direct);
      return;
    }

    const option = selector.options[
      selector.selectedIndex
    ];

    const text = String(
      option && option.textContent || ""
    ).toUpperCase();

    if (text.includes("CU01")) {
      setSelectedStation("CU01");
    } else if (text.includes("SJ01")) {
      setSelectedStation("SJ01");
    }
  }

  document.addEventListener(
    "change",
    stationFromSelectorEvent,
    true
  );

  function initializeStationIsolation() {
    const station = stationFromPage();

    if (station) {
      setSelectedStation(station);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      initializeStationIsolation,
      { once: true }
    );
  } else {
    initializeStationIsolation();
  }
})();
