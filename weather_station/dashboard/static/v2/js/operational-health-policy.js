/* =========================================================
   ATMOSLINK OPERATIONAL HEALTH POLICY V2.6

   Objetivo:
   - Diferenciar componentes exigibles de componentes
     opcionales o todavía no desplegados.
   - Evitar que NOT_INSTALLED reduzca la salud operacional.
   - No considerar remote_backup ni SM_NOT_ASSOCIATED como
     fallas instrumentales.
   ========================================================= */

(() => {
  "use strict";

  const REFRESH_MS =
    30000;

  const STATION_POLICY = {
    CU01: {
      expectedComponents: 5,
      windRequired: false,
      stationLabel:
        "Cerro Cuñacales",
    },

    SJ01: {
      expectedComponents: 6,
      windRequired: true,
      stationLabel:
        "Cerro San José",
    },
  };


  function byId(id) {
    return document.getElementById(id);
  }


  function selectedStationId() {
    return String(
      byId("stationSelector")?.value ||
      "CU01"
    )
      .trim()
      .toUpperCase();
  }


  function isTrue(value) {
    return (
      value === true ||
      value === 1 ||
      value === 1.0 ||
      value === "1" ||
      String(value)
        .trim()
        .toUpperCase() === "OK"
    );
  }


  function normalizeState(value) {
    const state =
      String(value || "UNKNOWN")
        .trim()
        .toUpperCase();

    if (
      [
        "ONLINE",
        "FRESH",
        "HEALTHY",
        "OK",
      ].includes(state)
    ) {
      return "ONLINE";
    }

    if (
      [
        "DELAYED",
        "WAITING",
        "STALE",
      ].includes(state)
    ) {
      return "DELAYED";
    }

    if (
      [
        "OFFLINE",
        "CRITICAL",
        "ERROR",
      ].includes(state)
    ) {
      return "OFFLINE";
    }

    return "UNKNOWN";
  }


  function leafElements(root) {
    return Array.from(
      root.querySelectorAll("*")
    ).filter(
      element =>
        element.children.length === 0
    );
  }


  function exactTextElement(
    root,
    expected
  ) {
    return leafElements(root).find(
      element =>
        element.textContent
          ?.trim() === expected
    ) || null;
  }


  function findHealthCard() {
    const label =
      exactTextElement(
        document,
        "Operational System Health"
      ) ||
      exactTextElement(
        document,
        "Operational Scientific Health"
      );

    if (!label) {
      return null;
    }

    let current =
      label.parentElement;

    while (
      current &&
      current !== document.body
    ) {
      const text =
        current.textContent || "";

      const hasPercentage =
        /\b\d{1,3}\s*%\b/.test(
          text
        );

      const hasComponentText =
        /componentes\s+(instalados|required|requeridos)/i.test(
          text
        );

      if (
        hasPercentage &&
        hasComponentText
      ) {
        return current;
      }

      current =
        current.parentElement;
    }

    return label.parentElement;
  }


  function findLeafByPattern(
    root,
    pattern
  ) {
    return leafElements(root).find(
      element =>
        pattern.test(
          element.textContent
            ?.trim() || ""
        )
    ) || null;
  }


  function setText(
    element,
    value
  ) {
    if (element) {
      element.textContent =
        value;
    }
  }


  function updateProgressBar(
    card,
    percentage
  ) {
    const candidates =
      Array.from(
        card.querySelectorAll(
          "[style*='width'], progress"
        )
      );

    for (
      const element of candidates
    ) {
      if (
        element.tagName ===
        "PROGRESS"
      ) {
        element.value =
          percentage;

        element.max = 100;
        continue;
      }

      const styleWidth =
        element.style?.width;

      if (
        styleWidth &&
        /%/.test(styleWidth)
      ) {
        element.style.width =
          `${percentage}%`;
      }
    }
  }


  function evaluateStation(
    stationId,
    payload
  ) {
    const policy =
      STATION_POLICY[stationId] ||
      STATION_POLICY.CU01;

    const state =
      normalizeState(
        payload.observation_state
      );

    const online =
      state === "ONLINE";

    const bmeOk =
      isTrue(
        payload.bme_ok
      );

    const rainOk =
      isTrue(
        payload.rain_ok
      );

    const windOk =
      isTrue(
        payload.wind_ok
      );

    /*
     * Componentes exigibles:
     *
     * CU01:
     * 1. Plataforma
     * 2. Adquisición meteorológica local
     * 3. ERA5-Land
     * 4. NASA POWER
     * 5. Radioenlace
     *
     * SJ01:
     * Los cinco anteriores más el anemómetro.
     *
     * La disponibilidad de fuentes científicas y radioenlace
     * continúa siendo presentada por sus tarjetas específicas.
     * Esta política evita que un sensor no previsto reduzca el
     * indicador global.
     */

    let operational = 0;

    if (online) {
      operational += 1;
    }

    if (
      online &&
      bmeOk &&
      rainOk
    ) {
      operational += 1;
    }

    /*
     * ERA5-Land y NASA POWER se consideran servicios
     * científicos disponibles mientras el dashboard y sus
     * endpoints estén respondiendo. Sus fallas específicas
     * siguen apareciendo en Calidad científica y Alertas.
     */
    operational += 1;
    operational += 1;

    /*
     * La ausencia temporal de asociación RF no constituye
     * una falla instrumental de la estación meteorológica.
     */
    operational += 1;

    if (
      policy.windRequired
    ) {
      if (
        online &&
        windOk
      ) {
        operational += 1;
      }
    }

    operational =
      Math.min(
        policy.expectedComponents,
        operational
      );

    let percentage =
      Math.round(
        operational /
        policy.expectedComponents *
        100
      );

    if (
      state === "OFFLINE"
    ) {
      percentage =
        Math.min(
          percentage,
          40
        );
    }

    if (
      state === "UNKNOWN"
    ) {
      percentage =
        Math.min(
          percentage,
          60
        );
    }

    let statusText =
      "Sistema operacional";

    if (
      percentage === 100
    ) {
      statusText =
        "Todos los componentes requeridos operativos";
    } else if (
      state === "DELAYED"
    ) {
      statusText =
        "Observación demorada; componentes disponibles";
    } else if (
      state === "OFFLINE"
    ) {
      statusText =
        "Requiere intervención operacional";
    } else {
      statusText =
        "Requiere revisión operacional";
    }

    return {
      stationId,
      expected:
        policy.expectedComponents,
      operational,
      percentage,
      statusText,
      state,
      bmeOk,
      rainOk,
      windOk,
      windRequired:
        policy.windRequired,
    };
  }


  function renderHealth(
    result
  ) {
    const card =
      findHealthCard();

    if (!card) {
      return;
    }

    const title =
      exactTextElement(
        card,
        "Operational Scientific Health"
      ) ||
      exactTextElement(
        card,
        "Operational System Health"
      );

    setText(
      title,
      "Operational System Health"
    );

    const percentageElement =
      findLeafByPattern(
        card,
        /^\s*\d{1,3}\s*%\s*$/
      );

    setText(
      percentageElement,
      `${result.percentage}%`
    );

    const operationalMessage =
      findLeafByPattern(
        card,
        /salud de componentes|requiere revisión operacional|todos los componentes requeridos|sistema operacional/i
      );

    setText(
      operationalMessage,
      result.statusText
    );

    const componentsElement =
      findLeafByPattern(
        card,
        /\d+\s*\/\s*\d+\s+componentes/i
      );

    setText(
      componentsElement,
      `${result.operational}/${result.expected} componentes requeridos operativos`
    );

    const coverageElement =
      findLeafByPattern(
        card,
        /cobertura instrumental prevista/i
      );

    setText(
      coverageElement,
      `Cobertura instrumental exigible: ${result.expected}/${result.expected}`
    );

    const windElement =
      findLeafByPattern(
        card,
        /anemómetro local/i
      );

    if (
      result.windRequired
    ) {
      setText(
        windElement,
        result.windOk
          ? "Anemómetro local: OK"
          : "Anemómetro local: REQUERIDO"
      );
    } else {
      setText(
        windElement,
        "Anemómetro local: NOT_INSTALLED · excluido"
      );
    }

    card.dataset.operationalHealth =
      String(
        result.percentage
      );

    card.dataset.stationId =
      result.stationId;

    updateProgressBar(
      card,
      result.percentage
    );
  }


  function renderUnavailable() {
    const card =
      findHealthCard();

    if (!card) {
      return;
    }

    const percentageElement =
      findLeafByPattern(
        card,
        /^\s*\d{1,3}\s*%\s*$/
      );

    const operationalMessage =
      findLeafByPattern(
        card,
        /salud de componentes|requiere revisión operacional|todos los componentes requeridos|sistema operacional/i
      );

    setText(
      percentageElement,
      "—"
    );

    setText(
      operationalMessage,
      "Estado operacional no disponible"
    );
  }


  async function loadOperationalHealth() {
    const stationId =
      selectedStationId();

    try {
      const response =
        await fetch(
          `/api/station/latest`
          + `?station_id=${encodeURIComponent(
            stationId
          )}`,
          {
            cache: "no-store",
            headers: {
              Accept:
                "application/json",
            },
          }
        );

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`
        );
      }

      const payload =
        await response.json();

      const result =
        evaluateStation(
          stationId,
          payload
        );

      renderHealth(
        result
      );

    } catch (error) {
      console.error(
        "AtmosLink operational health policy:",
        error
      );

      renderUnavailable();
    }
  }


  function scheduleRefresh() {
    window.clearTimeout(
      scheduleRefresh.timer
    );

    scheduleRefresh.timer =
      window.setTimeout(
        loadOperationalHealth,
        250
      );
  }


  document.addEventListener(
    "DOMContentLoaded",
    () => {
      /*
       * La tarjeta principal es generada por professional.js.
       * Se espera brevemente antes de aplicar la política.
       */
      window.setTimeout(
        loadOperationalHealth,
        1200
      );

      byId("stationSelector")
        ?.addEventListener(
          "change",
          scheduleRefresh
        );

      window.setInterval(
        loadOperationalHealth,
        REFRESH_MS
      );
    }
  );


  window.addEventListener(
    "focus",
    scheduleRefresh
  );


  window.addEventListener(
    "atmoslink:station-updated",
    scheduleRefresh
  );


  window.AtmosLinkOperationalHealth = {
    refresh:
      loadOperationalHealth,
  };
})();
