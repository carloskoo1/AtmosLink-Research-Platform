/* =========================================================
   ATMOSLINK SCIENTIFIC VALIDATION MATURITY V2.4

   Separa:
   - Deployment readiness: SRL
   - Statistical maturity: pares horarios comparables

   Clasificación:
   EXCLUDED      : estación fuera de campaña científica
   INSUFFICIENT  : menos de 24 pares
   PRELIMINARY   : 24 a 167 pares
   INTERMEDIATE  : 168 a 719 pares
   MATURE        : 720 pares o más
   ========================================================= */

(() => {
  "use strict";

  const VARIABLE =
    "temperature";

  const REFRESH_INTERVAL_MS =
    5 * 60 * 1000;

  function byId(id) {
    return document.getElementById(id);
  }

  function finiteNumber(value) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return null;
    }

    const number =
      Number(value);

    return Number.isFinite(number)
      ? number
      : null;
  }

  function selectedStationId() {
    return String(
      byId("stationSelector")?.value ||
      "CU01"
    )
      .trim()
      .toUpperCase();
  }

  function deploymentMode() {
    return String(
      document.documentElement
        .dataset.deploymentMode ||
      ""
    )
      .trim()
      .toUpperCase();
  }

  function classifyCoverage(pairs) {
    if (pairs < 24) {
      return {
        key: "INSUFFICIENT",
        label: "INSUFICIENTE",
        description:
          "Cobertura aún insuficiente para una interpretación estadística estable.",
        progress:
          Math.min(
            100,
            pairs / 24 * 100
          ),
      };
    }

    if (pairs < 168) {
      return {
        key: "PRELIMINARY",
        label: "PRELIMINAR",
        description:
          "Resultados exploratorios. La cobertura todavía no alcanza una semana completa.",
        progress:
          Math.min(
            100,
            pairs / 168 * 100
          ),
      };
    }

    if (pairs < 720) {
      return {
        key: "INTERMEDIATE",
        label: "INTERMEDIA",
        description:
          "Cobertura suficiente para análisis temporal inicial, pero todavía inferior a 30 días.",
        progress:
          Math.min(
            100,
            pairs / 720 * 100
          ),
      };
    }

    return {
      key: "MATURE",
      label: "MADURA",
      description:
        "Cobertura de al menos 720 pares horarios comparables, equivalente a 30 días.",
      progress: 100,
    };
  }

  function createPanel() {
    let panel =
      byId(
        "scientificValidationMaturity"
      );

    if (panel) {
      return panel;
    }

    const readiness =
      byId(
        "atmoslinkScientificReadiness"
      );

    if (!readiness) {
      return null;
    }

    panel =
      document.createElement(
        "section"
      );

    panel.id =
      "scientificValidationMaturity";

    panel.className =
      "atl-validation-maturity";

    readiness.insertAdjacentElement(
      "afterend",
      panel
    );

    return panel;
  }

  function renderExcluded(
    stationId,
    reason
  ) {
    const panel =
      createPanel();

    if (!panel) {
      return;
    }

    panel.dataset.status =
      "EXCLUDED";

    panel.innerHTML = `
      <div class="atl-validation-maturity__header">

        <div>
          <span class="atl-validation-maturity__eyebrow">
            SCIENTIFIC VALIDATION STATUS
          </span>

          <h2>
            ${stationId} · Validación estadística
          </h2>

          <p>
            ${reason}
          </p>
        </div>

        <div class="atl-validation-maturity__status">
          <strong>EXCLUIDA</strong>
          <span>0 pares comparables</span>
        </div>

      </div>

      <div class="atl-validation-maturity__progress">
        <span style="width: 0%"></span>
      </div>

      <div class="atl-validation-maturity__grid">

        <div>
          <strong>ERA5-Land</strong>
          <span>0 pares</span>
        </div>

        <div>
          <strong>NASA POWER</strong>
          <span>0 pares</span>
        </div>

        <div>
          <strong>Cobertura efectiva</strong>
          <span>0 horas</span>
        </div>

        <div>
          <strong>Criterio</strong>
          <span>Estación no desplegada</span>
        </div>

      </div>
    `;
  }

  function renderAvailable(
    stationId,
    era5Pairs,
    nasaPairs
  ) {
    const panel =
      createPanel();

    if (!panel) {
      return;
    }

    /*
     * Cobertura conservadora:
     * se toma el menor número de pares disponibles.
     */
    const effectivePairs =
      Math.min(
        era5Pairs,
        nasaPairs
      );

    const maturity =
      classifyCoverage(
        effectivePairs
      );

    const approximateDays =
      effectivePairs / 24;

    panel.dataset.status =
      maturity.key;

    panel.innerHTML = `
      <div class="atl-validation-maturity__header">

        <div>
          <span class="atl-validation-maturity__eyebrow">
            SCIENTIFIC VALIDATION STATUS
          </span>

          <h2>
            ${stationId} · Madurez estadística
          </h2>

          <p>
            ${maturity.description}
          </p>
        </div>

        <div class="atl-validation-maturity__status">
          <strong>${maturity.label}</strong>
          <span>
            ${effectivePairs} pares efectivos
          </span>
        </div>

      </div>

      <div class="atl-validation-maturity__progress"
           role="progressbar"
           aria-valuemin="0"
           aria-valuemax="100"
           aria-valuenow="${Math.round(
             maturity.progress
           )}">

        <span style="width: ${
          maturity.progress
        }%"></span>

      </div>

      <div class="atl-validation-maturity__grid">

        <div>
          <strong>ERA5-Land</strong>
          <span>${era5Pairs} pares</span>
        </div>

        <div>
          <strong>NASA POWER</strong>
          <span>${nasaPairs} pares</span>
        </div>

        <div>
          <strong>Cobertura efectiva</strong>
          <span>
            ${effectivePairs} h
            ·
            ${approximateDays.toFixed(1)} días
          </span>
        </div>

        <div>
          <strong>Siguiente nivel</strong>
          <span>
            ${
              maturity.key === "INSUFFICIENT"
                ? `${Math.max(
                    0,
                    24 - effectivePairs
                  )} pares para PRELIMINAR`
                : maturity.key === "PRELIMINARY"
                  ? `${Math.max(
                      0,
                      168 - effectivePairs
                    )} pares para INTERMEDIA`
                  : maturity.key === "INTERMEDIATE"
                    ? `${Math.max(
                        0,
                        720 - effectivePairs
                      )} pares para MADURA`
                    : "Nivel máximo alcanzado"
            }
          </span>
        </div>

      </div>

      <div class="atl-validation-maturity__criteria">

        <span>
          <strong>INSUFICIENTE</strong>
          &lt; 24 h
        </span>

        <span>
          <strong>PRELIMINAR</strong>
          24–167 h
        </span>

        <span>
          <strong>INTERMEDIA</strong>
          168–719 h
        </span>

        <span>
          <strong>MADURA</strong>
          ≥ 720 h
        </span>

      </div>
    `;
  }

  function renderError(
    stationId,
    message
  ) {
    const panel =
      createPanel();

    if (!panel) {
      return;
    }

    panel.dataset.status =
      "ERROR";

    panel.innerHTML = `
      <div class="atl-validation-maturity__header">

        <div>
          <span class="atl-validation-maturity__eyebrow">
            SCIENTIFIC VALIDATION STATUS
          </span>

          <h2>
            ${stationId} · Estado no disponible
          </h2>

          <p>
            No fue posible determinar la cobertura estadística:
            ${message}
          </p>
        </div>

        <div class="atl-validation-maturity__status">
          <strong>ERROR</strong>
          <span>Reintento automático</span>
        </div>

      </div>
    `;
  }

  function countPairs(
    records,
    source
  ) {
    return records.filter(
      record =>
        finiteNumber(
          record.observed
        ) !== null &&
        finiteNumber(
          record[source]
        ) !== null
    ).length;
  }

  async function loadValidationMaturity() {
    const stationId =
      selectedStationId();

    /*
     * El modo LABORATORY siempre excluye la validación,
     * aunque el endpoint conserve registros instrumentales.
     */
    if (
      deploymentMode() ===
      "LABORATORY"
    ) {
      renderExcluded(
        stationId,
        `${stationId} permanece en laboratorio. ` +
        "La madurez estadística se habilitará después " +
        "de su instalación y generación de pares horarios " +
        "comparables en el sitio físico."
      );

      return;
    }

    try {
      const response = await fetch(
        `/api/scientific/hourly`
        + `?station_id=${encodeURIComponent(
          stationId
        )}`
        + `&variable=${encodeURIComponent(
          VARIABLE
        )}`,
        {
          cache: "no-store",
          headers: {
            Accept:
              "application/json",
          },
        }
      );

      const payload =
        await response.json();

      if (
        payload.status ===
        "excluded"
      ) {
        renderExcluded(
          stationId,
          payload.reason ||
          "Validación científica no habilitada."
        );

        return;
      }

      if (
        !response.ok ||
        payload.status !== "ok"
      ) {
        throw new Error(
          payload.error ||
          `HTTP ${response.status}`
        );
      }

      const records =
        Array.isArray(
          payload.records
        )
          ? payload.records
          : [];

      const era5Pairs =
        countPairs(
          records,
          "era5"
        );

      const nasaPairs =
        countPairs(
          records,
          "nasa"
        );

      renderAvailable(
        stationId,
        era5Pairs,
        nasaPairs
      );

    } catch (error) {
      console.error(
        "Scientific validation maturity:",
        error
      );

      renderError(
        stationId,
        error.message ||
        "Error desconocido"
      );
    }
  }

  function scheduleRefresh() {
    window.clearTimeout(
      scheduleRefresh.timer
    );

    scheduleRefresh.timer =
      window.setTimeout(
        loadValidationMaturity,
        120
      );
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      /*
       * El panel SRL es creado por otro módulo.
       * Se concede un breve intervalo para su inserción.
       */
      window.setTimeout(
        loadValidationMaturity,
        250
      );

      byId("stationSelector")
        ?.addEventListener(
          "change",
          scheduleRefresh
        );

      window.setInterval(
        loadValidationMaturity,
        REFRESH_INTERVAL_MS
      );
    }
  );

  window.addEventListener(
    "atmoslink:deployment-mode",
    scheduleRefresh
  );

  window.addEventListener(
    "focus",
    scheduleRefresh
  );

  window.AtmosLinkValidationMaturity = {
    refresh:
      loadValidationMaturity,
  };
})();
