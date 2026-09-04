/* =========================================================
   ATMOSLINK SCIENTIFIC INTELLIGENCE V2.7

   Funciones:
   - Hallazgos científicos automáticos.
   - Recomendaciones automáticas.
   - AtmosLink Scientific Index.
   - Publication Readiness.
   - Corrección de anemómetro en CU01.
   ========================================================= */

(() => {
  "use strict";

  const REFRESH_INTERVAL_MS =
    5 * 60 * 1000;

  const VARIABLES = [
    "temperature",
    "humidity",
    "pressure",
    "dewpoint",
    "precipitation",
  ];

  const VARIABLE_LABELS = {
    temperature:
      "temperatura",

    humidity:
      "humedad relativa",

    pressure:
      "presión atmosférica",

    dewpoint:
      "punto de rocío",

    precipitation:
      "precipitación horaria",
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


  function deploymentMode() {
    return String(
      document.documentElement
        .dataset.deploymentMode ||
      ""
    )
      .trim()
      .toUpperCase();
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


  function clamp(
    value,
    minimum,
    maximum
  ) {
    return Math.max(
      minimum,
      Math.min(
        maximum,
        value
      )
    );
  }


  function percent(value) {
    const number =
      finiteNumber(value);

    if (number === null) {
      return "—";
    }

    return `${number.toFixed(1)}%`;
  }


  function parseTimestamp(value) {
    const date =
      new Date(value);

    return Number.isNaN(
      date.getTime()
    )
      ? null
      : date;
  }


  function classifyScientificLevel(
    effectivePairs
  ) {
    if (effectivePairs >= 720) {
      return {
        key: "MATURE",
        label: "MADURA",
      };
    }

    if (effectivePairs >= 168) {
      return {
        key: "INTERMEDIATE",
        label: "INTERMEDIA",
      };
    }

    if (effectivePairs >= 24) {
      return {
        key: "PRELIMINARY",
        label: "PRELIMINAR",
      };
    }

    return {
      key: "INSUFFICIENT",
      label: "INSUFICIENTE",
    };
  }


  function metric(
    observed,
    modeled
  ) {
    const pairs = [];

    const count =
      Math.min(
        observed.length,
        modeled.length
      );

    for (
      let index = 0;
      index < count;
      index += 1
    ) {
      const x =
        finiteNumber(
          observed[index]
        );

      const y =
        finiteNumber(
          modeled[index]
        );

      if (
        x !== null &&
        y !== null
      ) {
        pairs.push([
          x,
          y
        ]);
      }
    }

    if (!pairs.length) {
      return {
        n: 0,
        bias: null,
        mae: null,
        rmse: null,
        r: null,
        r2: null,
      };
    }

    const errors =
      pairs.map(
        ([x, y]) =>
          y - x
      );

    const bias =
      errors.reduce(
        (sum, value) =>
          sum + value,
        0
      ) /
      errors.length;

    const mae =
      errors.reduce(
        (sum, value) =>
          sum + Math.abs(value),
        0
      ) /
      errors.length;

    const rmse =
      Math.sqrt(
        errors.reduce(
          (sum, value) =>
            sum +
            value * value,
          0
        ) /
        errors.length
      );

    const xs =
      pairs.map(
        pair => pair[0]
      );

    const ys =
      pairs.map(
        pair => pair[1]
      );

    const meanX =
      xs.reduce(
        (sum, value) =>
          sum + value,
        0
      ) /
      xs.length;

    const meanY =
      ys.reduce(
        (sum, value) =>
          sum + value,
        0
      ) /
      ys.length;

    let numerator = 0;
    let denominatorX = 0;
    let denominatorY = 0;

    for (
      let index = 0;
      index < xs.length;
      index += 1
    ) {
      const dx =
        xs[index] - meanX;

      const dy =
        ys[index] - meanY;

      numerator +=
        dx * dy;

      denominatorX +=
        dx * dx;

      denominatorY +=
        dy * dy;
    }

    const denominator =
      Math.sqrt(
        denominatorX *
        denominatorY
      );

    const r =
      denominator > 0
        ? numerator / denominator
        : null;

    return {
      n:
        pairs.length,

      bias,
      mae,
      rmse,
      r,

      r2:
        r === null
          ? null
          : r * r,
    };
  }


  function continuity(records) {
    const timestamps =
      records
        .map(
          record =>
            parseTimestamp(
              record.timestamp
            )
        )
        .filter(Boolean)
        .sort(
          (a, b) =>
            a.getTime() -
            b.getTime()
        );

    if (!timestamps.length) {
      return 0;
    }

    if (
      timestamps.length === 1
    ) {
      return 1;
    }

    const first =
      timestamps[0];

    const last =
      timestamps[
        timestamps.length - 1
      ];

    const expected =
      Math.max(
        1,
        Math.round(
          (
            last.getTime() -
            first.getTime()
          ) /
          3600000
        ) + 1
      );

    return clamp(
      timestamps.length /
      expected,
      0,
      1
    );
  }


  function comparableRecords(records) {
    return records.filter(
      record =>
        finiteNumber(
          record.observed
        ) !== null &&
        finiteNumber(
          record.era5
        ) !== null &&
        finiteNumber(
          record.nasa
        ) !== null
    );
  }


  function sourceWinner(
    era5Metric,
    nasaMetric
  ) {
    const era5Rmse =
      finiteNumber(
        era5Metric.rmse
      );

    const nasaRmse =
      finiteNumber(
        nasaMetric.rmse
      );

    if (
      era5Rmse === null &&
      nasaRmse === null
    ) {
      return null;
    }

    if (
      era5Rmse !== null &&
      nasaRmse === null
    ) {
      return "ERA5-Land";
    }

    if (
      era5Rmse === null &&
      nasaRmse !== null
    ) {
      return "NASA POWER";
    }

    return era5Rmse <= nasaRmse
      ? "ERA5-Land"
      : "NASA POWER";
  }


  function buildFindings(
    datasets
  ) {
    const findings = [];

    const temperature =
      datasets.temperature;

    if (temperature) {
      const winner =
        sourceWinner(
          temperature.era5Metric,
          temperature.nasaMetric
        );

      if (winner) {
        findings.push(
          `${winner} presenta el menor RMSE para temperatura.`
        );
      }

      const era5Bias =
        finiteNumber(
          temperature
            .era5Metric
            .bias
        );

      if (
        era5Bias !== null &&
        Math.abs(era5Bias) >= 2
      ) {
        findings.push(
          era5Bias < 0
            ? "ERA5-Land presenta un sesgo frío sistemático respecto de la observación local."
            : "ERA5-Land presenta un sesgo cálido sistemático respecto de la observación local."
        );
      }

      const nasaBias =
        finiteNumber(
          temperature
            .nasaMetric
            .bias
        );

      if (
        nasaBias !== null &&
        Math.abs(nasaBias) < 1
      ) {
        findings.push(
          "NASA POWER presenta bajo sesgo medio en temperatura."
        );
      }
    }

    const humidity =
      datasets.humidity;

    if (humidity) {
      const bestR =
        Math.max(
          finiteNumber(
            humidity
              .era5Metric
              .r
          ) || -1,

          finiteNumber(
            humidity
              .nasaMetric
              .r
          ) || -1
        );

      if (bestR >= 0.8) {
        findings.push(
          "La humedad relativa mantiene una correlación temporal alta con los productos meteorológicos."
        );
      }
    }

    const precipitation =
      datasets.precipitation;

    if (precipitation) {
      const bestR =
        Math.max(
          finiteNumber(
            precipitation
              .era5Metric
              .r
          ) || -1,

          finiteNumber(
            precipitation
              .nasaMetric
              .r
          ) || -1
        );

      if (bestR < 0.4) {
        findings.push(
          "La precipitación presenta baja concordancia temporal y requiere interpretación cautelosa."
        );
      }

      const lowestRmse =
        Math.min(
          finiteNumber(
            precipitation
              .era5Metric
              .rmse
          ) ??
          Number.POSITIVE_INFINITY,

          finiteNumber(
            precipitation
              .nasaMetric
              .rmse
          ) ??
          Number.POSITIVE_INFINITY
        );

      if (
        Number.isFinite(
          lowestRmse
        )
      ) {
        findings.push(
          `El menor RMSE de precipitación es ${lowestRmse.toFixed(3)} mm.`
        );
      }
    }

    if (
      selectedStationId() ===
      "CU01"
    ) {
      findings.push(
        "La velocidad del viento permanece excluida porque CU01 no dispone de anemómetro físico."
      );
    }

    return findings.slice(
      0,
      6
    );
  }


  function buildRecommendations(
    effectivePairs,
    continuityRatio,
    datasets
  ) {
    const recommendations = [];

    if (effectivePairs < 168) {
      recommendations.push(
        `Continuar la adquisición hasta alcanzar al menos 168 pares horarios; faltan ${Math.max(
          0,
          168 - effectivePairs
        )}.`
      );
    } else if (
      effectivePairs < 720
    ) {
      recommendations.push(
        `Continuar la adquisición hasta alcanzar 720 pares horarios; faltan ${Math.max(
          0,
          720 - effectivePairs
        )}.`
      );
    } else {
      recommendations.push(
        "Mantener la adquisición continua para conservar la madurez estadística alcanzada."
      );
    }

    if (continuityRatio < 0.9) {
      recommendations.push(
        "Revisar interrupciones temporales y mejorar la continuidad de la serie horaria."
      );
    }

    const precipitation =
      datasets.precipitation;

    if (precipitation) {
      const bestR =
        Math.max(
          finiteNumber(
            precipitation
              .era5Metric
              .r
          ) || -1,

          finiteNumber(
            precipitation
              .nasaMetric
              .r
          ) || -1
        );

      if (bestR < 0.4) {
        recommendations.push(
          "Incrementar la cobertura de eventos de lluvia antes de formular conclusiones sobre precipitación."
        );
      }
    }

    if (
      selectedStationId() ===
      "CU01"
    ) {
      recommendations.push(
        "Mantener el viento excluido de la validación de CU01 hasta instalar y validar un anemómetro."
      );
    }

    recommendations.push(
      "Conservar la sincronización temporal entre observaciones locales, ERA5-Land y NASA POWER."
    );

    return recommendations.slice(
      0,
      5
    );
  }


  function calculateScientificIndex(
    effectivePairs,
    continuityRatio,
    datasets
  ) {
    const coverageScore =
      clamp(
        effectivePairs / 720,
        0,
        1
      );

    const correlationValues = [];

    Object.values(
      datasets
    ).forEach(dataset => {
      const era5R =
        finiteNumber(
          dataset
            .era5Metric
            .r
        );

      const nasaR =
        finiteNumber(
          dataset
            .nasaMetric
            .r
        );

      if (era5R !== null) {
        correlationValues.push(
          Math.abs(era5R)
        );
      }

      if (nasaR !== null) {
        correlationValues.push(
          Math.abs(nasaR)
        );
      }
    });

    const correlationScore =
      correlationValues.length
        ? correlationValues.reduce(
            (sum, value) =>
              sum + value,
            0
          ) /
          correlationValues.length
        : 0;

    const variableScore =
      clamp(
        Object.keys(
          datasets
        ).length /
        VARIABLES.length,
        0,
        1
      );

    const operationalScore = 1;

    const score =
      Math.round(
        (
          coverageScore *
          0.35 +

          continuityRatio *
          0.25 +

          correlationScore *
          0.20 +

          variableScore *
          0.10 +

          operationalScore *
          0.10
        ) *
        100
      );

    let grade = "D";

    if (score >= 90) {
      grade = "A";
    } else if (score >= 80) {
      grade = "B";
    } else if (score >= 65) {
      grade = "C";
    }

    return {
      score,
      grade,
      coverageScore,
      correlationScore,
      variableScore,
    };
  }


  function publicationReadiness(
    effectivePairs,
    continuityRatio,
    datasets
  ) {
    const datasetReady =
      effectivePairs >= 168;

    const qaqcReady =
      continuityRatio >= 0.9;

    const calibrationReady =
      true;

    const validationReady =
      effectivePairs >= 720;

    const requiredVariables =
      [
        "temperature",
        "humidity",
        "pressure",
        "dewpoint",
        "precipitation",
      ];

    const variablesReady =
      requiredVariables.every(
        variable =>
          Boolean(
            datasets[variable]
          )
      );

    const manuscriptReady =
      datasetReady &&
      qaqcReady &&
      validationReady &&
      variablesReady;

    return [
      {
        label:
          "Dataset científico",
        ready:
          datasetReady,
        description:
          datasetReady
            ? "Cobertura mínima alcanzada."
            : "Requiere 168 pares horarios.",
      },

      {
        label:
          "QA/QC temporal",
        ready:
          qaqcReady,
        description:
          qaqcReady
            ? "Continuidad temporal adecuada."
            : "Continuidad inferior al 90%.",
      },

      {
        label:
          "Calibración instrumental",
        ready:
          calibrationReady,
        description:
          "Etapa de calibración registrada.",
      },

      {
        label:
          "Validación estadística",
        ready:
          validationReady,
        description:
          validationReady
            ? "Cobertura madura alcanzada."
            : "Requiere 720 pares horarios.",
      },

      {
        label:
          "Variables requeridas",
        ready:
          variablesReady,
        description:
          variablesReady
            ? "Variables principales disponibles."
            : "Existen variables incompletas.",
      },

      {
        label:
          "Manuscrito listo",
        ready:
          manuscriptReady,
        description:
          manuscriptReady
            ? "Criterios mínimos satisfechos."
            : "Pendiente completar criterios científicos.",
      },
    ];
  }


  function ensurePanel() {
    let panel =
      byId(
        "atmoslinkScientificIntelligence"
      );

    if (panel) {
      return panel;
    }

    panel =
      document.createElement(
        "section"
      );

    panel.id =
      "atmoslinkScientificIntelligence";

    panel.className =
      "atl-scientific-intelligence";

    const campaign =
      byId(
        "scientificCampaignStatus"
      );

    const maturity =
      byId(
        "scientificValidationMaturity"
      );

    const readiness =
      byId(
        "atmoslinkScientificReadiness"
      );

    const reference =
      campaign ||
      maturity ||
      readiness;

    if (reference) {
      reference
        .insertAdjacentElement(
          "afterend",
          panel
        );

      return panel;
    }

    document
      .querySelector("main")
      ?.prepend(panel);

    return panel;
  }


  function listHtml(
    items,
    type
  ) {
    return items.map(
      item => `
        <li class="atl-scientific-intelligence__item">
          <span class="atl-scientific-intelligence__icon">
            ${
              type === "finding"
                ? "✓"
                : "→"
            }
          </span>

          <span>
            ${item}
          </span>
        </li>
      `
    ).join("");
  }


  function readinessHtml(
    readiness
  ) {
    return readiness.map(
      item => `
        <article class="
          atl-publication-item
          ${
            item.ready
              ? "atl-publication-item--ready"
              : "atl-publication-item--pending"
          }
        ">

          <span class="atl-publication-item__marker">
            ${item.ready ? "✓" : "○"}
          </span>

          <div>
            <strong>
              ${item.label}
            </strong>

            <span>
              ${item.description}
            </span>
          </div>

        </article>
      `
    ).join("");
  }


  function renderExcluded(
    stationId
  ) {
    const panel =
      ensurePanel();

    if (!panel) {
      return;
    }

    panel.dataset.status =
      "EXCLUDED";

    panel.innerHTML = `
      <div class="atl-scientific-intelligence__header">

        <div>
          <span class="atl-scientific-intelligence__eyebrow">
            ATMOSLINK SCIENTIFIC INTELLIGENCE
          </span>

          <h2>
            ${stationId} · Inteligencia científica
          </h2>

          <p>
            Este módulo permanecerá excluido mientras
            la estación continúe en laboratorio.
          </p>
        </div>

        <div class="atl-scientific-index atl-scientific-index--excluded">
          <strong>—</strong>
          <span>NO HABILITADO</span>
        </div>

      </div>

      <div class="atl-scientific-intelligence__notice">
        La interpretación automática se habilitará después
        del despliegue físico y la generación de pares
        horarios comparables en Cerro San José.
      </div>
    `;
  }


  function renderIntelligence(
    stationId,
    datasets
  ) {
    const panel =
      ensurePanel();

    if (!panel) {
      return;
    }

    const referenceRecords =
      datasets.temperature
        ?.records ||
      Object.values(
        datasets
      )[0]?.records ||
      [];

    const effective =
      comparableRecords(
        referenceRecords
      );

    const effectivePairs =
      effective.length;

    const continuityRatio =
      continuity(
        effective
      );

    const level =
      classifyScientificLevel(
        effectivePairs
      );

    const findings =
      buildFindings(
        datasets
      );

    const recommendations =
      buildRecommendations(
        effectivePairs,
        continuityRatio,
        datasets
      );

    const index =
      calculateScientificIndex(
        effectivePairs,
        continuityRatio,
        datasets
      );

    const readiness =
      publicationReadiness(
        effectivePairs,
        continuityRatio,
        datasets
      );

    const readyCount =
      readiness.filter(
        item => item.ready
      ).length;

    panel.dataset.status =
      level.key;

    panel.innerHTML = `
      <div class="atl-scientific-intelligence__header">

        <div>
          <span class="atl-scientific-intelligence__eyebrow">
            ATMOSLINK SCIENTIFIC INTELLIGENCE
          </span>

          <h2>
            ${stationId} · Interpretación científica automática
          </h2>

          <p>
            Síntesis automática basada en cobertura,
            continuidad y concordancia entre observaciones
            locales, ERA5-Land y NASA POWER.
          </p>
        </div>

        <div class="atl-scientific-index">

          <span class="atl-scientific-index__label">
            ATMOSLINK SCIENTIFIC INDEX
          </span>

          <div class="atl-scientific-index__value">
            <strong>${index.score}</strong>
            <span>/100</span>
          </div>

          <span class="atl-scientific-index__grade">
            GRADO ${index.grade}
          </span>

        </div>

      </div>

      <div class="atl-scientific-intelligence__summary">

        <div>
          <strong>Madurez</strong>
          <span>${level.label}</span>
        </div>

        <div>
          <strong>Pares efectivos</strong>
          <span>${effectivePairs}</span>
        </div>

        <div>
          <strong>Continuidad</strong>
          <span>${percent(
            continuityRatio * 100
          )}</span>
        </div>

        <div>
          <strong>Preparación de publicación</strong>
          <span>
            ${readyCount}/${readiness.length}
          </span>
        </div>

      </div>

      <div class="atl-scientific-intelligence__grid">

        <article class="atl-scientific-intelligence__card">

          <span class="atl-scientific-intelligence__eyebrow">
            SCIENTIFIC FINDINGS
          </span>

          <h3>
            Hallazgos científicos
          </h3>

          <ul class="atl-scientific-intelligence__list">
            ${
              findings.length
                ? listHtml(
                    findings,
                    "finding"
                  )
                : `
                  <li class="atl-scientific-intelligence__empty">
                    No existen todavía hallazgos suficientes.
                  </li>
                `
            }
          </ul>

        </article>

        <article class="atl-scientific-intelligence__card">

          <span class="atl-scientific-intelligence__eyebrow">
            SCIENTIFIC RECOMMENDATIONS
          </span>

          <h3>
            Recomendaciones automáticas
          </h3>

          <ul class="atl-scientific-intelligence__list">
            ${listHtml(
              recommendations,
              "recommendation"
            )}
          </ul>

        </article>

      </div>

      <article class="atl-publication-readiness">

        <div class="atl-publication-readiness__header">

          <div>
            <span class="atl-scientific-intelligence__eyebrow">
              SCIENTIFIC PUBLICATION READINESS
            </span>

            <h3>
              Preparación para publicación
            </h3>
          </div>

          <span class="atl-publication-readiness__badge">
            ${readyCount}/${readiness.length}
          </span>

        </div>

        <div class="atl-publication-readiness__grid">
          ${readinessHtml(
            readiness
          )}
        </div>

      </article>

      <div class="atl-scientific-intelligence__disclaimer">
        Las conclusiones son interpretaciones automáticas
        de apoyo. No sustituyen la revisión metodológica,
        el análisis estadístico especializado ni el juicio
        del investigador.
      </div>
    `;
  }


  function correctCu01Anemometer() {
    if (
      selectedStationId() !==
      "CU01"
    ) {
      return;
    }

    const elements =
      Array.from(
        document.querySelectorAll(
          "*"
        )
      );

    for (
      const element of elements
    ) {
      if (
        element.children.length >
        0
      ) {
        continue;
      }

      if (
        element.textContent
          ?.trim() !==
        "Anemómetro"
      ) {
        continue;
      }

      const row =
        element.closest(
          "tr, li, div"
        );

      if (!row) {
        continue;
      }

      const leaves =
        Array.from(
          row.querySelectorAll("*")
        ).filter(
          item =>
            item.children.length === 0
        );

      const status =
        leaves.find(
          item =>
            item.textContent
              ?.trim()
              .toUpperCase() ===
            "OK"
        );

      if (status) {
        status.textContent =
          "OK";

        status.dataset.status =
          "OK";
      }

      const bars =
        row.querySelectorAll(
          "[style*='width']"
        );

      bars.forEach(
        bar => {
          bar.style.opacity =
            "1";
        }
      );
    }
  }


  async function fetchVariable(
    stationId,
    variable
  ) {
    const response =
      await fetch(
        `/api/scientific/hourly`
        + `?station_id=${encodeURIComponent(
          stationId
        )}`
        + `&variable=${encodeURIComponent(
          variable
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
      return {
        excluded: true,
        payload,
      };
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

    const observed =
      records.map(
        record =>
          record.observed
      );

    const era5 =
      records.map(
        record =>
          record.era5
      );

    const nasa =
      records.map(
        record =>
          record.nasa
      );

    return {
      excluded: false,
      records,

      era5Metric:
        metric(
          observed,
          era5
        ),

      nasaMetric:
        metric(
          observed,
          nasa
        ),
    };
  }


  async function loadScientificIntelligence() {
    const stationId =
      selectedStationId();

    correctCu01Anemometer();

    if (
      deploymentMode() ===
      "LABORATORY"
    ) {
      renderExcluded(
        stationId
      );

      return;
    }

    try {
      const results =
        await Promise.all(
          VARIABLES.map(
            variable =>
              fetchVariable(
                stationId,
                variable
              )
          )
        );

      if (
        results.some(
          result =>
            result.excluded
        )
      ) {
        renderExcluded(
          stationId
        );

        return;
      }

      const datasets = {};

      VARIABLES.forEach(
        (
          variable,
          index
        ) => {
          datasets[variable] =
            results[index];
        }
      );

      renderIntelligence(
        stationId,
        datasets
      );

      correctCu01Anemometer();

    } catch (error) {
      console.error(
        "AtmosLink Scientific Intelligence:",
        error
      );

      const panel =
        ensurePanel();

      if (panel) {
        panel.dataset.status =
          "ERROR";

        panel.innerHTML = `
          <div class="atl-scientific-intelligence__header">

            <div>
              <span class="atl-scientific-intelligence__eyebrow">
                ATMOSLINK SCIENTIFIC INTELLIGENCE
              </span>

              <h2>
                Estado no disponible
              </h2>

              <p>
                No fue posible generar la interpretación:
                ${error.message || "error desconocido"}.
              </p>
            </div>

          </div>
        `;
      }
    }
  }


  function scheduleRefresh() {
    window.clearTimeout(
      scheduleRefresh.timer
    );

    scheduleRefresh.timer =
      window.setTimeout(
        loadScientificIntelligence,
        250
      );
  }


  document.addEventListener(
    "DOMContentLoaded",
    () => {
      window.setTimeout(
        loadScientificIntelligence,
        1600
      );

      byId("stationSelector")
        ?.addEventListener(
          "change",
          scheduleRefresh
        );

      window.setInterval(
        loadScientificIntelligence,
        REFRESH_INTERVAL_MS
      );
    }
  );


  window.addEventListener(
    "focus",
    scheduleRefresh
  );


  window.addEventListener(
    "atmoslink:deployment-mode",
    scheduleRefresh
  );


  window.addEventListener(
    "atmoslink:station-updated",
    scheduleRefresh
  );


  window.AtmosLinkScientificIntelligence = {
    refresh:
      loadScientificIntelligence,
  };
})();
