
/* =========================================================
   ATMOSLINK VALIDATION SCIENTIFIC SUMMARY V1
   ERA5-Land vs NASA POWER
   ========================================================= */

(() => {
  "use strict";

  const VARIABLE_ORDER = [
    "temperature",
    "humidity",
    "pressure",
    "dewpoint",
    "precipitation",
  ];

  function byId(id) {
    return document.getElementById(id);
  }

  function finiteNumber(value) {
    const number = Number(value);

    return Number.isFinite(number)
      ? number
      : null;
  }

  function formatNumber(
    value,
    digits = 3
  ) {
    const number = finiteNumber(value);

    if (number === null) {
      return "—";
    }

    return new Intl.NumberFormat(
      "es-PE",
      {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }
    ).format(number);
  }

  function modelLabel(model) {
    return model === "era5"
      ? "ERA5-Land"
      : "NASA POWER";
  }

  async function fetchValidation(
    stationId
  ) {
    const response = await fetch(
      `/api/scientific/validation?station_id=${encodeURIComponent(stationId)}`,
      {
        cache: "no-store",
        headers: {
          Accept: "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(
        `HTTP ${response.status}`
      );
    }

    return response.json();
  }

  function collectComparisons(payload) {
    const results = [];

    for (
      const variableKey
      of VARIABLE_ORDER
    ) {
      const variable =
        payload.variables?.[
          variableKey
        ];

      if (
        !variable ||
        variable.enabled === false
      ) {
        continue;
      }

      const era5 =
        variable.models?.era5
          ?.metrics;

      const nasa =
        variable.models?.nasa
          ?.metrics;

      const era5Rmse =
        finiteNumber(
          era5?.rmse
        );

      const nasaRmse =
        finiteNumber(
          nasa?.rmse
        );

      if (
        era5Rmse === null ||
        nasaRmse === null
      ) {
        continue;
      }

      const winner =
        era5Rmse < nasaRmse
          ? "era5"
          : nasaRmse < era5Rmse
            ? "nasa"
            : "tie";

      results.push({
        variableKey,
        label: variable.label,
        unit: variable.unit,
        era5,
        nasa,
        era5Rmse,
        nasaRmse,
        winner,
      });
    }

    return results;
  }

  function renderExcluded(payload) {
    byId(
      "validationV2BestModel"
    ).textContent =
      "NO DISPONIBLE";

    byId(
      "validationV2ModelWins"
    ).textContent =
      "SJ01 en laboratorio";

    byId(
      "validationV2BestTemperature"
    ).textContent =
      "PREDESPLIEGUE";

    byId(
      "validationV2TemperatureMetric"
    ).textContent =
      "Sin validación espacial";

    byId(
      "validationV2Coverage"
    ).textContent =
      "0 horas";

    byId(
      "validationV2CoverageDetail"
    ).textContent =
      "Sin pares científicamente comparables";

    byId(
      "validationV2Interpretation"
    ).innerHTML = `
      <strong>
        Interpretación automática:
      </strong>
      ${payload.reason || (
        "SJ01 permanece en laboratorio y todavía no puede "
        + "compararse científicamente con ERA5-Land ni NASA "
        + "POWER para las coordenadas del Cerro San José."
      )}
    `;
  }

  function renderReport(payload) {
    const comparisons =
      collectComparisons(payload);

    const wins = {
      era5: 0,
      nasa: 0,
      tie: 0,
    };

    comparisons.forEach(
      result => {
        wins[result.winner] += 1;
      }
    );

    let bestModel = "EMPATE";

    if (wins.era5 > wins.nasa) {
      bestModel = "ERA5-Land";
    }

    if (wins.nasa > wins.era5) {
      bestModel = "NASA POWER";
    }

    byId(
      "validationV2BestModel"
    ).textContent =
      bestModel;

    byId(
      "validationV2ModelWins"
    ).textContent =
      `ERA5: ${wins.era5} · NASA: ${wins.nasa}`
      + (
        wins.tie > 0
          ? ` · Empates: ${wins.tie}`
          : ""
      );

    const temperature =
      comparisons.find(
        result =>
          result.variableKey ===
          "temperature"
      );

    if (temperature) {
      const winner =
        temperature.winner === "era5"
          ? "era5"
          : "nasa";

      const metrics =
        temperature[winner];

      byId(
        "validationV2BestTemperature"
      ).textContent =
        modelLabel(winner);

      byId(
        "validationV2TemperatureMetric"
      ).textContent =
        `RMSE ${formatNumber(
          metrics.rmse,
          3
        )} ${temperature.unit}`
        + ` · BIAS ${formatNumber(
          metrics.bias,
          3
        )} ${temperature.unit}`;
    }

    const era5Counts = [];
    const nasaCounts = [];

    comparisons.forEach(
      result => {
        const era5Count =
          finiteNumber(
            result.era5?.count
          );

        const nasaCount =
          finiteNumber(
            result.nasa?.count
          );

        if (era5Count !== null) {
          era5Counts.push(
            era5Count
          );
        }

        if (nasaCount !== null) {
          nasaCounts.push(
            nasaCount
          );
        }
      }
    );

    const era5Coverage =
      era5Counts.length
        ? Math.min(...era5Counts)
        : 0;

    const nasaCoverage =
      nasaCounts.length
        ? Math.min(...nasaCounts)
        : 0;

    const maximumCoverage =
      Math.max(
        era5Coverage,
        nasaCoverage
      );

    byId(
      "validationV2Coverage"
    ).textContent =
      `${maximumCoverage} horas`;

    byId(
      "validationV2CoverageDetail"
    ).textContent =
      `ERA5: ${era5Coverage} · NASA: ${nasaCoverage}`;

    const temperatureSentence =
      temperature
        ? (
          temperature.winner === "nasa"
            ? (
              `NASA POWER presentó menor RMSE térmico `
              + `(${formatNumber(
                temperature.nasa.rmse,
                3
              )} ${temperature.unit}) que ERA5-Land `
              + `(${formatNumber(
                temperature.era5.rmse,
                3
              )} ${temperature.unit}).`
            )
            : (
              `ERA5-Land presentó menor RMSE térmico `
              + `(${formatNumber(
                temperature.era5.rmse,
                3
              )} ${temperature.unit}) que NASA POWER `
              + `(${formatNumber(
                temperature.nasa.rmse,
                3
              )} ${temperature.unit}).`
            )
        )
        : "";

    const precipitation =
      comparisons.find(
        result =>
          result.variableKey ===
          "precipitation"
      );

    let precipitationSentence = "";

    if (precipitation) {
      const bestCorrelation =
        Math.max(
          finiteNumber(
            precipitation.era5
              ?.pearson_r
          ) ?? -1,
          finiteNumber(
            precipitation.nasa
              ?.pearson_r
          ) ?? -1
        );

      if (bestCorrelation < 0.5) {
        precipitationSentence =
          " La precipitación presenta baja concordancia "
          + "temporal con las observaciones locales, por "
          + "lo que sus métricas deben interpretarse con "
          + "precaución.";
      }
    }

    byId(
      "validationV2Interpretation"
    ).innerHTML = `
      <strong>
        Interpretación automática:
      </strong>
      Durante la campaña analizada,
      ${bestModel} obtuvo el menor RMSE en
      ${Math.max(
        wins.era5,
        wins.nasa
      )} de ${comparisons.length}
      variables comparables.
      ${temperatureSentence}
      ${precipitationSentence}
      Las métricas se actualizan automáticamente
      cada hora.
    `;
  }

  /* ATMOSLINK_STATION_RESPONSE_ISOLATION_V1 */
  let validationSummaryRequestGeneration = 0;
  
  async function loadValidationSummary() {
    const requestGeneration = ++validationSummaryRequestGeneration;
    const stationId =
      byId("stationSelector")
        ?.value ||
      "CU01";

    try {
      const payload =
        await fetchValidation(
          stationId
        );
      const requestedStationId =
        String(stationId || "CU01")
          .trim()
          .toUpperCase();

      const currentStationId =
        String(
          byId("stationSelector")
            ?.value ||
          "CU01"
        )
          .trim()
          .toUpperCase();

      const responseStationId =
        String(
          payload.station_id ||
          requestedStationId
        )
          .trim()
          .toUpperCase();

      if (
        requestGeneration !== validationSummaryRequestGeneration ||
        currentStationId !== requestedStationId ||
        responseStationId !== requestedStationId
      ) {
        console.info(
          "Respuesta científica descartada:",
          {
            requestedStationId,
            currentStationId,
            responseStationId,
          }
        );
        return;
      }


      if (
        payload.status ===
        "excluded"
      ) {
        renderExcluded(payload);
        return;
      }

      if (
        payload.status !== "ok"
      ) {
        throw new Error(
          payload.error ||
          "Reporte no disponible"
        );
      }

      renderReport(payload);

    } catch (error) {
      console.error(
        "AtmosLink Validation Summary:",
        error
      );

      const interpretation =
        byId(
          "validationV2Interpretation"
        );

      if (interpretation) {
        interpretation.innerHTML = `
          <strong>
            Error:
          </strong>
          No fue posible cargar el resumen
          comparativo de validación científica.
        `;
      }
    }
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      loadValidationSummary();

      byId(
        "stationSelector"
      )?.addEventListener(
        "change",
        loadValidationSummary
      );

      window.setInterval(
        loadValidationSummary,
        300000
      );
    }
  );
})();
