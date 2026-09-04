/* =========================================================
   ATMOSLINK DEPLOYMENT MODE
   SCIENTIFIC READINESS LEVEL + CAMPAIGN TIMELINE V2.3
   ========================================================= */

(() => {
  "use strict";

  /*
   * CONFIGURACIÓN CENTRAL DE DESPLIEGUE
   *
   * Cuando SJ01 sea instalada en Cerro San José:
   *
   * 1. Cambiar mode a "FIELD".
   * 2. Marcar las etapas realizadas como complete: true.
   * 3. Registrar sus fechas reales.
   *
   * El porcentaje y el SRL se calculan automáticamente.
   */
  const STATIONS = {
    CU01: {
      mode: "FIELD",
      location: "Cerro Cuñacales",
      stage: "OPERACIÓN DE CAMPO",
      spatialComparison: true,

      steps: [
        {
          key: "laboratory",
          label: "Laboratorio",
          complete: true,
          date: "26/06/2026",
          description:
            "Pruebas instrumentales completadas",
        },
        {
          key: "transport",
          label: "Transporte",
          complete: true,
          date: "26/06/2026",
          description:
            "Traslado al sitio realizado",
        },
        {
          key: "installation",
          label: "Instalación",
          complete: true,
          date: "26/06/2026",
          description:
            "Estación instalada en Cuñacales",
        },
        {
          key: "calibration",
          label: "Estabilización",
          complete: true,
          date: "22/07/2026",
          description:
            "Verificación instrumental ejecutada",
        },
        {
          key: "operation",
          label: "Operación",
          complete: true,
          date: "22/07/2026",
          description:
            "Adquisición continua habilitada",
        },
        {
          key: "validation",
          label: "Validación",
          complete: true,
          date: "04/08/2026",
          description:
            "Validación ERA5-Land y NASA POWER activa",
        },
      ],
    },

    SJ01: {
      mode: "FIELD",
      location: "Cerro San José",
      stage: "OPERACIÓN INICIAL EN CAMPO",
      spatialComparison: false,
      fieldStartLocal: "2026-08-31 18:30:00-05:00",

      steps: [
        {
          key: "laboratory",
          label: "Laboratorio",
          complete: true,
          date: "04/08/2026",
          description:
            "Sensores y adquisición verificados",
        },
        {
          key: "transport",
          label: "Transporte",
          complete: true,
          date: "31/08/2026",
          description:
            "Traslado a Cerro San José completado",
        },
        {
          key: "installation",
          label: "Instalación",
          complete: true,
          date: "31/08/2026",
          description:
            "Estación instalada físicamente en Cerro San José",
        },
        {
          key: "calibration",
          label: "Estabilización",
          complete: false,
          date: "31/08/2026",
          description:
            "Estabilización operativa y acumulación de pares horarios",
        },
        {
          key: "operation",
          label: "Operación",
          complete: false,
          date: null,
          description:
            "Pendiente de continuidad operacional",
        },
        {
          key: "validation",
          label: "Validación",
          complete: false,
          date: null,
          description:
            "Pendiente de cobertura científica suficiente",
        },
      ],
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


  function fallbackStation(stationId) {
    return {
      mode: "UNKNOWN",
      location: "Ubicación no definida",
      stage: "CONTEXTO NO DEFINIDO",
      spatialComparison: false,
      steps: [
        {
          key: "laboratory",
          label: "Laboratorio",
          complete: false,
          date: null,
          description:
            "Sin información",
        },
        {
          key: "transport",
          label: "Transporte",
          complete: false,
          date: null,
          description:
            "Sin información",
        },
        {
          key: "installation",
          label: "Instalación",
          complete: false,
          date: null,
          description:
            "Sin información",
        },
        {
          key: "calibration",
          label: "Estabilización",
          complete: false,
          date: null,
          description:
            "Sin información",
        },
        {
          key: "operation",
          label: "Operación",
          complete: false,
          date: null,
          description:
            "Sin información",
        },
        {
          key: "validation",
          label: "Validación",
          complete: false,
          date: null,
          description:
            "Sin información",
        },
      ],
      stationId,
    };
  }


  function stationConfiguration(
    stationId
  ) {
    return (
      STATIONS[stationId] ||
      fallbackStation(stationId)
    );
  }


  function completedSteps(config) {
    return config.steps.filter(
      step => step.complete
    ).length;
  }


  function totalSteps(config) {
    return config.steps.length;
  }


  function readinessPercentage(
    config
  ) {
    const total =
      totalSteps(config);

    if (!total) {
      return 0;
    }

    return Math.round(
      completedSteps(config) /
      total *
      100
    );
  }


  function scientificReadinessLabel(
    config
  ) {
    return (
      `SRL ${completedSteps(config)}` +
      `/${totalSteps(config)}`
    );
  }


  function mainContainer() {
    return (
      document.querySelector(
        ".atl-main"
      ) ||
      document.querySelector(
        "main"
      ) ||
      document.querySelector(
        ".atl-content"
      )
    );
  }


  function firstDashboardSection() {
    return (
      byId("dashboard") ||
      mainContainer()
        ?.firstElementChild ||
      null
    );
  }


  function ensureReadinessPanel() {
    let panel =
      byId(
        "atmoslinkScientificReadiness"
      );

    if (panel) {
      return panel;
    }

    panel =
      document.createElement(
        "section"
      );

    panel.id =
      "atmoslinkScientificReadiness";

    panel.className =
      "atl-readiness-panel";

    const reference =
      firstDashboardSection();

    if (
      reference &&
      reference.parentNode
    ) {
      reference.parentNode.insertBefore(
        panel,
        reference
      );
    } else {
      mainContainer()?.prepend(
        panel
      );
    }

    return panel;
  }


  function modeExplanation(
    stationId,
    config
  ) {
    if (
      config.mode === "FIELD"
    ) {
      return (
        `${stationId} opera en su ubicación física ` +
        "configurada. La adquisición de campo está " +
        "habilitada y las métricas científicas pueden " +
        "calcularse cuando existan pares horarios válidos."
      );
    }

    if (
      config.mode === "LABORATORY"
    ) {
      return (
        `${stationId} permanece en laboratorio. ` +
        "La adquisición instrumental está habilitada, " +
        "pero la validación espacial, los gradientes del " +
        "corredor y la comparación con ERA5-Land y NASA " +
        "POWER permanecen excluidos hasta su instalación " +
        "en Cerro San José."
      );
    }

    return (
      "El contexto de despliegue no está definido. " +
      "No deben publicarse comparaciones científicas."
    );
  }


  function readinessStepsHtml(
    config
  ) {
    return config.steps.map(
      (step, index) => {
        const stateClass =
          step.complete
            ? "atl-readiness-step--complete"
            : "atl-readiness-step--pending";

        const symbol =
          step.complete
            ? "✓"
            : String(index + 1);

        const date =
          step.date ||
          "Pendiente";

        return `
          <div class="atl-readiness-step ${stateClass}">

            <span class="atl-readiness-step__number">
              ${symbol}
            </span>

            <span class="atl-readiness-step__content">

              <strong class="atl-readiness-step__label">
                ${step.label}
              </strong>

              <small class="atl-readiness-step__date">
                ${date}
              </small>

            </span>

          </div>
        `;
      }
    ).join("");
  }


  function timelineHtml(config) {
    return config.steps.map(
      (step, index) => {
        const stateClass =
          step.complete
            ? "atl-campaign-event--complete"
            : "atl-campaign-event--pending";

        const dateText =
          step.date ||
          "Pendiente";

        return `
          <article class="atl-campaign-event ${stateClass}">

            <div class="atl-campaign-event__marker">
              ${
                step.complete
                  ? "✓"
                  : index + 1
              }
            </div>

            <div class="atl-campaign-event__body">

              <span class="atl-campaign-event__date">
                ${dateText}
              </span>

              <strong class="atl-campaign-event__title">
                ${step.label}
              </strong>

              <p class="atl-campaign-event__description">
                ${step.description}
              </p>

            </div>

          </article>
        `;
      }
    ).join("");
  }


  function renderReadinessPanel() {
    const stationId =
      selectedStationId();

    const config =
      stationConfiguration(
        stationId
      );

    const readiness =
      readinessPercentage(
        config
      );

    const srl =
      scientificReadinessLabel(
        config
      );

    const panel =
      ensureReadinessPanel();

    if (!panel) {
      return;
    }

    const modeClass =
      config.mode === "FIELD"
        ? "atl-readiness-panel--field"
        : config.mode === "LABORATORY"
          ? "atl-readiness-panel--laboratory"
          : "atl-readiness-panel--unknown";

    panel.className =
      `atl-readiness-panel ${modeClass}`;

    panel.dataset.mode =
      config.mode;

    panel.innerHTML = `
      <div class="atl-readiness-panel__header">

        <div class="atl-readiness-heading">

          <span class="atl-readiness-eyebrow">
            SCIENTIFIC READINESS LEVEL
          </span>

          <h2 class="atl-readiness-title">
            ${stationId} · ${config.location}
          </h2>

          <p class="atl-readiness-description">
            ${modeExplanation(
              stationId,
              config
            )}
          </p>

        </div>

        <div class="atl-readiness-score">

          <span class="atl-readiness-score__value">
            ${readiness}%
          </span>

          <span class="atl-readiness-score__srl">
            ${srl}
          </span>

          <span class="atl-readiness-score__label">
            ${config.stage}
          </span>

        </div>

      </div>

      <div class="atl-readiness-progress"
           role="progressbar"
           aria-valuemin="0"
           aria-valuemax="100"
           aria-valuenow="${readiness}">

        <span class="atl-readiness-progress__bar"
              style="width: ${readiness}%">
        </span>

      </div>

      <div class="atl-readiness-steps">
        ${readinessStepsHtml(config)}
      </div>

      <div class="atl-readiness-context">

        <span>
          <strong>Modo</strong>
          ${config.mode}
        </span>

        <span>
          <strong>Comparación espacial</strong>
          ${
            config.spatialComparison
              ? "HABILITADA"
              : "NO HABILITADA"
          }
        </span>

        <span>
          <strong>Validación de modelos</strong>
          ${
            config.mode === "FIELD"
              ? "CONDICIONADA A COBERTURA"
              : "EXCLUIDA"
          }
        </span>

      </div>

      <div class="atl-campaign-timeline">

        <div class="atl-campaign-timeline__header">

          <div>
            <span class="atl-readiness-eyebrow">
              TRAZABILIDAD DE CAMPAÑA
            </span>

            <h3>
              Línea de tiempo científica
            </h3>
          </div>

          <span class="atl-campaign-timeline__status">
            ${srl}
          </span>

        </div>

        <div class="atl-campaign-timeline__events">
          ${timelineHtml(config)}
        </div>

      </div>
    `;

    document.documentElement
      .dataset.stationId =
      stationId;

    document.documentElement
      .dataset.deploymentMode =
      config.mode;

    window.dispatchEvent(
      new CustomEvent(
        "atmoslink:deployment-mode",
        {
          detail: {
            stationId,
            readiness,
            srl,
            ...config,
          },
        }
      )
    );
  }


  function scheduleRender() {
    window.clearTimeout(
      scheduleRender.timer
    );

    scheduleRender.timer =
      window.setTimeout(
        renderReadinessPanel,
        100
      );
  }


  function installObserver() {
    const target =
      mainContainer();

    if (!target) {
      return;
    }

    const observer =
      new MutationObserver(
        scheduleRender
      );

    observer.observe(
      target,
      {
        childList: true,
        subtree: true,
      }
    );
  }


  document.addEventListener(
    "DOMContentLoaded",
    () => {
      renderReadinessPanel();
      installObserver();

      byId("stationSelector")
        ?.addEventListener(
          "change",
          renderReadinessPanel
        );
    }
  );


  window.addEventListener(
    "focus",
    renderReadinessPanel
  );


  window.AtmosLinkDeployment = {
    refresh:
      renderReadinessPanel,

    stationId:
      selectedStationId,

    configuration: () =>
      stationConfiguration(
        selectedStationId()
      ),

    readiness: () => {
      const config =
        stationConfiguration(
          selectedStationId()
        );

      return {
        percentage:
          readinessPercentage(config),

        completed:
          completedSteps(config),

        total:
          totalSteps(config),

        label:
          scientificReadinessLabel(
            config
          ),
      };
    },
  };
})();
