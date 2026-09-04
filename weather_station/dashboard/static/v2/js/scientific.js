/* =========================================================
   AtmosLink Scientific Observatory
   Observed vs ERA5-Land vs NASA POWER
   ========================================================= */

(() => {
  "use strict";

  const VARIABLES = [
    {
      key: "temperature",
      label: "Temperatura",
      unit: "°C",
    },
    {
      key: "humidity",
      label: "Humedad relativa",
      unit: "%",
    },
    {
      key: "pressure",
      label: "Presión",
      unit: "hPa",
    },
    {
      key: "dewpoint",
      label: "Punto de rocío",
      unit: "°C",
    },
    {
      key: "precipitation",
      label: "Precipitación",
      unit: "mm",
    },
    {
      key: "wind",
      label: "Velocidad del viento",
      unit: "m/s",
    },
  ];

  function byId(id) {
    return document.getElementById(id);
  }

  function valueOrDash(value, digits = 2) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
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

  function formatValue(value, unit) {
    if (
      value === null ||
      value === undefined
    ) {
      return "—";
    }

    return `${valueOrDash(value)} ${unit}`;
  }

  function formatTimestamp(value) {
    if (!value) {
      return "—";
    }

    const date = new Date(
      String(value).replace(" ", "T")
    );

    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    return new Intl.DateTimeFormat(
      "es-PE",
      {
        dateStyle: "short",
        timeStyle: "short",
      }
    ).format(date);
  }

  async function fetchScientific(stationId) {
    const response = await fetch(
      `/api/station/scientific?station_id=${encodeURIComponent(stationId)}`,
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

  function renderLatestAvailable(payload) {
    const latest =
      payload.latest_available ?? {};

    const local =
      latest.local ?? {};

    const era5 =
      latest.era5 ?? {};

    const nasa =
      latest.nasa_power ?? {};

    byId("scientificLocalTimestamp").textContent =
      formatTimestamp(
        local.timestamp_local
      );

    byId("scientificLocalStation").textContent =
      `${payload.station_id} · ${
        local.station_name ?? "Estación"
      }`;

    byId("scientificEra5Timestamp").textContent =
      formatTimestamp(
        era5.timestamp_local
      );

    byId("scientificEra5Age").textContent =
      latest.era5_age_label
        ? `Antigüedad: ${latest.era5_age_label}`
        : "Sin información de antigüedad";

    byId("scientificNasaTimestamp").textContent =
      formatTimestamp(
        nasa.timestamp_local
      );

    byId("scientificNasaAge").textContent =
      latest.nasa_age_label
        ? `Antigüedad: ${latest.nasa_age_label}`
        : "Sin información de antigüedad";
  }

  function renderStrictMatched(payload) {
    const strict =
      payload.strict_matched ?? {};

    const body =
      byId("scientificComparisonBody");

    if (!body) {
      return;
    }

    if (!strict.available) {
      body.innerHTML = `
        <tr>
          <td colspan="8">
            No existe todavía una hora con observación local,
            ERA5-Land y NASA POWER simultáneos.
          </td>
        </tr>
      `;

      return;
    }

    const local =
      strict.local ?? {};

    const era5 =
      strict.era5 ?? {};

    const nasa =
      strict.nasa_power ?? {};

    const era5Comparison =
      strict.era5_comparison ?? {};

    const nasaComparison =
      strict.nasa_comparison ?? {};

    const sourceKeys = {
      temperature: "temperature_c",
      humidity: "humidity_pct",
      pressure: "pressure_hpa",
      dewpoint: "dewpoint_c",
      precipitation: "precipitation_mm",
      wind: "wind_ms",
    };

    body.innerHTML = VARIABLES.map(
      variable => {
        const key =
          sourceKeys[variable.key];

        const era5Metric =
          era5Comparison[
            variable.key
          ] ?? {};

        const nasaMetric =
          nasaComparison[
            variable.key
          ] ?? {};

        return `
          <tr>
            <td>
              <strong>
                ${variable.label}
              </strong>
            </td>

            <td>
              ${formatValue(
                local[key],
                variable.unit
              )}
            </td>

            <td>
              ${formatValue(
                era5[key],
                variable.unit
              )}
            </td>

            <td>
              ${formatValue(
                nasa[key],
                variable.unit
              )}
            </td>

            <td>
              ${formatValue(
                era5Metric.bias_model_minus_observed,
                variable.unit
              )}
            </td>

            <td>
              ${formatValue(
                era5Metric.absolute_error,
                variable.unit
              )}
            </td>

            <td>
              ${formatValue(
                nasaMetric.bias_model_minus_observed,
                variable.unit
              )}
            </td>

            <td>
              ${formatValue(
                nasaMetric.absolute_error,
                variable.unit
              )}
            </td>
          </tr>
        `;
      }
    ).join("");
  }

  function renderWarning(payload) {
    const warning =
      byId("scientificWarning");

    if (!warning) {
      return;
    }

    if (
      payload.comparison_mode ===
      "STRICT_MATCHED"
    ) {
      warning.hidden = false;
      warning.innerHTML = `
        <strong>
          Comparación temporalmente válida.
        </strong>
        Los valores observado, ERA5-Land y NASA POWER
        corresponden a la misma hora de análisis.
      `;

      return;
    }

    const latest =
      payload.latest_available ?? {};

    warning.hidden = false;
    warning.innerHTML = `
      <strong>
        Comparación estricta todavía no disponible.
      </strong>
      ${
        latest.warning ??
        "Las fuentes disponibles pertenecen a horas diferentes."
      }
    `;
  }

  function renderMode(payload) {
    const mode =
      byId("scientificMode");

    if (!mode) {
      return;
    }

    mode.textContent =
      payload.comparison_mode ??
      "UNKNOWN";
  }

  async function loadScientificObservatory() {
    /*
     * El observatorio comparativo original puede no estar
     * presente en la plantilla profesional actual.
     *
     * En ese caso se omite este módulo sin afectar la sección
     * de Validación Científica V2.
     */
    const observatoryRoot =
      byId("scientificObservatory");

    if (!observatoryRoot) {
      return;
    }

    const selector =
      byId("stationSelector");

    const stationId =
      selector?.value ||
      localStorage.getItem(
        "atmoslink_selected_station"
      ) ||
      "CU01";

    try {
      const payload =
        await fetchScientific(
          stationId
        );

      renderMode(payload);
      renderLatestAvailable(payload);
      renderStrictMatched(payload);
      renderWarning(payload);

    } catch (error) {
      console.error(
        "Scientific Observatory:",
        error
      );

      const mode =
        byId("scientificMode");

      if (mode) {
        mode.textContent =
          "ERROR";
      }

      const body =
        byId(
          "scientificComparisonBody"
        );

      if (body) {
        body.innerHTML = `
          <tr>
            <td colspan="8">
              No fue posible cargar la comparación científica.
            </td>
          </tr>
        `;
      }
    }
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      loadScientificObservatory();

      const selector =
        byId("stationSelector");

      selector?.addEventListener(
        "change",
        loadScientificObservatory
      );

      window.setInterval(
        loadScientificObservatory,
        60000
      );
    }
  );
})();

/* Navegación explícita al Observatorio Científico */
document.addEventListener("DOMContentLoaded", () => {
  const link = document.querySelector(
    'a[href="#scientificObservatory"]'
  );

  link?.addEventListener("click", event => {
    event.preventDefault();

    const section = document.getElementById(
      "scientificObservatory"
    );

    if (!section) {
      console.error(
        "No existe la sección scientificObservatory"
      );
      return;
    }

    history.replaceState(
      null,
      "",
      "#scientificObservatory"
    );

    section.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  });
});

/* Navegación explícita hacia Validación científica */
document.addEventListener(
  "DOMContentLoaded",
  () => {
    const link =
      document.querySelector(
        'a[href="#scientificObservatory"]'
      );

    link?.addEventListener(
      "click",
      event => {
        event.preventDefault();

        const section =
          document.getElementById(
            "scientificObservatory"
          );

        if (!section) {
          console.error(
            "No existe scientificObservatory"
          );
          return;
        }

        history.replaceState(
          null,
          "",
          "#scientificObservatory"
        );

        section.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    );
  }
);


/* =========================================================
   ATMOSLINK SCIENTIFIC VALIDATION V2 FRONTEND
   ========================================================= */

(() => {
  "use strict";

  const VALIDATION_VARIABLE_ORDER = [
    "temperature",
    "humidity",
    "pressure",
    "dewpoint",
    "precipitation",
    "wind",
  ];

  function validationById(id) {
    return document.getElementById(id);
  }

  function validationFormat(
    value,
    digits = 3
  ) {
      if (value == null || value === "") return "—";
    const number = Number(value);

    if (!Number.isFinite(number)) {
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

  function validationDate(value) {
    if (!value) {
      return "—";
    }

    const date = new Date(
      String(value).replace(" ", "T")
    );

    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    return new Intl.DateTimeFormat(
      "es-PE",
      {
        dateStyle: "short",
        timeStyle: "short",
      }
    ).format(date);
  }

  async function validationFetch(
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

  function validationRenderExcluded(
    payload
  ) {
    validationById(
      "validationV2Status"
    ).textContent =
      "EXCLUIDA";

    validationById(
      "validationV2Station"
    ).textContent =
      payload.station_id || "SJ01";

    validationById(
      "validationV2Scope"
    ).textContent =
      payload.validation_scope ||
      "LABORATORY";

    validationById(
      "validationV2Resolution"
    ).textContent =
      "No aplica";

    validationById(
      "validationV2Rows"
    ).textContent =
      "Sin métricas publicables";

    validationById(
      "validationV2Period"
    ).textContent =
      "Predespliegue";

    const warning =
      validationById(
        "validationV2Warning"
      );

    warning.hidden = false;
    warning.innerHTML = `
      <strong>
        Validación científica no habilitada.
      </strong>
      ${payload.reason || ""}
    `;

    validationById(
      "validationV2Body"
    ).innerHTML = `
      <tr>
        <td colspan="10">
          SJ01 permanece en laboratorio.
          Sus datos no se comparan todavía con
          ERA5-Land ni NASA POWER para Cerro San José.
        </td>
      </tr>
    `;
  }

  function validationRenderReport(
    payload
  ) {
    validationById(
      "validationV2Status"
    ).textContent =
      "FIELD VALIDATION";

    validationById(
      "validationV2Station"
    ).textContent =
      payload.station_id || "CU01";

    validationById(
      "validationV2Scope"
    ).textContent =
      payload.validation_scope ||
      "FIELD_VALIDATION";

    validationById(
      "validationV2Resolution"
    ).textContent =
      payload.methodology
        ?.temporal_resolution
        ?.toUpperCase() ||
      "HOURLY";

    validationById(
      "validationV2Rows"
    ).textContent =
      `${payload.hourly_rows || 0} horas analizadas`;

    validationById(
      "validationV2Period"
    ).textContent =
      `${validationDate(
        payload.campaign_start_local
      )} → ${validationDate(
        payload.campaign_end_hour
      )}`;

    const warning =
      validationById(
        "validationV2Warning"
      );

    warning.hidden = false;
    warning.innerHTML = `
      <strong>
        Validación preliminar de campaña.
      </strong>
      Los resultados corresponden únicamente al periodo
      de campo homogéneo de CU01 y a pares horarios
      temporalmente coincidentes.
    `;

    const rows = [];

    for (
      const variableKey
      of VALIDATION_VARIABLE_ORDER
    ) {
      const variable =
        payload.variables?.[
          variableKey
        ];

      if (!variable) {
        continue;
      }

      if (!variable.enabled) {
        rows.push(`
          <tr>
            <td>
              <strong>
                ${variable.label}
              </strong>
            </td>

            <td colspan="9">
              EXCLUIDA ·
              ${
                variable.exclusion_reason ||
                "Sin justificación registrada."
              }
            </td>
          </tr>
        `);

        continue;
      }

      for (
        const modelName
        of ["era5", "nasa"]
      ) {
        const model =
          variable.models?.[
            modelName
          ];

        if (!model) {
          continue;
        }

        const metrics =
          model.metrics || {};

        rows.push(`
          <tr>
            <td>
              <strong>
                ${variable.label}
              </strong>
              <small>
                ${variable.unit}
              </small>
            </td>

            <td>
              ${
                  modelName === "era5"
                    ? "ERA5-Land"
                    : variableKey === "pressure"
                      ? "NASA POWER · CORREGIDA"
                      : "NASA POWER"
              }
            </td>

            <td>
                ${Number(metrics.count) === 0 ? "0 · SIN PARES" : Number(metrics.count) < 10 ? String(metrics.count) + " · MUESTRA INSUFICIENTE" : Number(metrics.count) < 30 ? String(metrics.count) + " · PRELIMINAR" : (metrics.count ?? "—")}
            </td>

            <td>
              ${validationFormat(
                metrics.bias
              )}
            </td>

            <td>
              ${validationFormat(
                metrics.mae
              )}
            </td>

            <td>
              ${validationFormat(
                metrics.rmse
              )}
            </td>

            <td>
              ${validationFormat(
                metrics.pearson_r
              )}
            </td>

            <td>
              ${validationFormat(
                metrics.r_squared
              )}
            </td>

            <td>
              ${validationFormat(
                metrics.nse
              )}
            </td>

            <td>
              ${validationFormat(
                metrics.willmott_d
              )}
            </td>
          </tr>
        `);
      }
    }

    validationById(
      "validationV2Body"
    ).innerHTML =
      rows.join("");
  }

  /* ATMOSLINK_STATION_RESPONSE_ISOLATION_V1 */
  let validationV2RequestGeneration = 0;
  
  async function loadScientificValidationV2() {
    const requestGeneration = ++validationV2RequestGeneration;
    const selector =
      validationById(
        "stationSelector"
      );

    const stationId =
      selector?.value ||
      "CU01";

    try {
      const payload =
        await validationFetch(
          stationId
        );
      const requestedStationId =
        String(stationId || "CU01")
          .trim()
          .toUpperCase();

      const currentStationId =
        String(
          validationById("stationSelector")
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
        requestGeneration !== validationV2RequestGeneration ||
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
        validationRenderExcluded(
          payload
        );
        return;
      }

      validationRenderReport(
        payload
      );

    } catch (error) {
      console.error(
        "Scientific Validation V2:",
        error
      );

      validationById(
        "validationV2Status"
      ).textContent =
        "ERROR";

      validationById(
        "validationV2Body"
      ).innerHTML = `
        <tr>
          <td colspan="10">
            No fue posible cargar las métricas científicas.
          </td>
        </tr>
      `;
    }
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      loadScientificValidationV2();

      validationById(
        "stationSelector"
      )?.addEventListener(
        "change",
        loadScientificValidationV2
      );

      window.setInterval(
        loadScientificValidationV2,
        300000
      );
    }
  );
})();
