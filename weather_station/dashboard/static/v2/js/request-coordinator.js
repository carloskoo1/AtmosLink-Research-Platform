/*
 * ATMOSLINK_REQUEST_COORDINATOR_V1
 *
 * Comparte solicitudes GET idénticas que se producen simultáneamente.
 * No cambia estaciones, endpoints ni datos científicos.
 */
(function () {
  "use strict";

  if (window.__atmoslinkRequestCoordinatorInstalled) {
    return;
  }

  window.__atmoslinkRequestCoordinatorInstalled = true;

  const originalFetch = window.fetch.bind(window);
  const inflight = new Map();
  const cache = new Map();

  function ttlFor(pathname) {
    if (pathname.includes("/api/station/history")) {
      return 30000;
    }

    if (pathname.includes("/api/scientific/hourly")) {
      return 30000;
    }

    if (pathname.includes("/api/windrose")) {
      return 15000;
    }

    if (pathname.includes("/api/station/latest")) {
      return 8000;
    }

    return 5000;
  }

  window.fetch = async function (input, init) {
    const options = init || {};
    const method = String(options.method || "GET").toUpperCase();

    let url;

    try {
      url = new URL(
        typeof input === "string" ? input : input.url,
        window.location.href
      );
    } catch (_error) {
      return originalFetch(input, options);
    }

    if (
      method !== "GET" ||
      url.origin !== window.location.origin ||
      !url.pathname.startsWith("/api/") ||
      options.signal
    ) {
      return originalFetch(input, options);
    }

    const key = url.href;
    const now = Date.now();
    const saved = cache.get(key);

    if (saved && saved.expires > now) {
      return saved.response.clone();
    }

    if (inflight.has(key)) {
      const shared = await inflight.get(key);
      return shared.clone();
    }

    const request = originalFetch(input, options)
      .then(response => {
        if (response.ok) {
          cache.set(key, {
            response: response.clone(),
            expires: Date.now() + ttlFor(url.pathname)
          });
        }

        return response;
      })
      .finally(() => {
        inflight.delete(key);
      });

    inflight.set(key, request);

    const response = await request;
    return response.clone();
  };

  document.addEventListener(
    "change",
    event => {
      if (event.target?.id === "stationSelector") {
        cache.clear();
      }
    },
    true
  );

  window.AtmosLinkRequestCoordinator = {
    clear: () => cache.clear()
  };
})();
