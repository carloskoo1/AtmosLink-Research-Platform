/* =========================================================
   ATMOSLINK SCIENTIFIC EXPORTS V2.8

   Funciones:
   - Exportar dataset científico consolidado a CSV.
   - Exportar trazabilidad y metadatos a JSON.
   - Exportar resumen científico a TXT.
   - Generar versión imprimible para PDF.
   ========================================================= */

(() => {
  "use strict";

  const VARIABLES = [
    "temperature",
    "humidity",
    "pressure",
    "dewpoint",
    "precipitation",
  ];

  const VARIABLE_LABELS = {
    temperature:
      "Temperatura",

    humidity:
      "Humedad relativa",

    pressure:
      "Presión atmosférica",

    dewpoint:
      "Punto de rocío",

    precipitation:
      "Precipitación horaria",
  };

  const VARIABLE_UNITS = {
    temperature:
      "°C",

    humidity:
      "%",

    pressure:
      "hPa",

    dewpoint:
      "°C",

    precipitation:
      "mm",
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


  function selectedStationLabel() {
    const selector =
      byId("stationSelector");

    const option =
      selector?.options[
        selector.selectedIndex
      ];

    return (
      option?.textContent ||
      selectedStationId()
    )
      .trim();
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


  function pad(value) {
    return String(value)
      .padStart(2, "0");
  }


  function timestampToken() {
    const now =
      new Date();

    return [
      now.getFullYear(),
      pad(
        now.getMonth() + 1
      ),
      pad(
        now.getDate()
      ),
      "_",
      pad(
        now.getHours()
      ),
      pad(
        now.getMinutes()
      ),
      pad(
        now.getSeconds()
      ),
    ].join("");
  }


  function isoLocalDate() {
    const now =
      new Date();

    const offset =
      now.getTimezoneOffset();

    const sign =
      offset <= 0
        ? "+"
        : "-";

    const absolute =
      Math.abs(offset);

    const hours =
      pad(
        Math.floor(
          absolute / 60
        )
      );

    const minutes =
      pad(
        absolute % 60
      );

    return (
      `${now.getFullYear()}-`
      + `${pad(now.getMonth() + 1)}-`
      + `${pad(now.getDate())}T`
      + `${pad(now.getHours())}:`
      + `${pad(now.getMinutes())}:`
      + `${pad(now.getSeconds())}`
      + `${sign}${hours}:${minutes}`
    );
  }


  function safeFilename(value) {
    return String(value)
      .normalize("NFD")
      .replace(
        /[\u0300-\u036f]/g,
        ""
      )
      .replace(
        /[^a-zA-Z0-9_-]+/g,
        "_"
      )
      .replace(
        /^_+|_+$/g,
        ""
      );
  }


  function downloadBlob(
    content,
    mimeType,
    filename
  ) {
    const blob =
      new Blob(
        [content],
        {
          type:
            `${mimeType};charset=utf-8`,
        }
      );

    const url =
      URL.createObjectURL(
        blob
      );

    const anchor =
      document.createElement(
        "a"
      );

    anchor.href =
      url;

    anchor.download =
      filename;

    document.body.appendChild(
      anchor
    );

    anchor.click();

    anchor.remove();

    window.setTimeout(
      () =>
        URL.revokeObjectURL(
          url
        ),
      1000
    );
  }


  function csvEscape(value) {
    if (
      value === null ||
      value === undefined
    ) {
      return "";
    }

    const text =
      String(value);

    if (
      /[",\n\r;]/.test(text)
    ) {
      return (
        "\""
        + text.replace(
          /"/g,
          "\"\""
        )
        + "\""
      );
    }

    return text;
  }


  function numberOrNull(value) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return null;
    }

    const parsed =
      Number(value);

    return Number.isFinite(parsed)
      ? parsed
      : null;
  }


  async function fetchVariable(
    stationId,
    variable
  ) {
    const url =
      `/api/scientific/hourly`
      + `?station_id=${encodeURIComponent(
        stationId
      )}`
      + `&variable=${encodeURIComponent(
        variable
      )}`;

    const response =
      await fetch(
        url,
        {
          cache:
            "no-store",

          headers: {
            Accept:
              "application/json",
          },
        }
      );

    let payload = null;

    try {
      payload =
        await response.json();

    } catch (error) {
      throw new Error(
        `${variable}: respuesta no JSON`
      );
    }

    if (
      payload.status ===
      "excluded"
    ) {
      return {
        variable,
        excluded: true,
        payload,
        records: [],
      };
    }

    if (
      !response.ok ||
      payload.status !== "ok"
    ) {
      throw new Error(
        payload.error ||
        `${variable}: HTTP ${response.status}`
      );
    }

    return {
      variable,
      excluded: false,
      payload,
      records:
        Array.isArray(
          payload.records
        )
          ? payload.records
          : [],
    };
  }


  async function loadScientificDataset() {
    const stationId =
      selectedStationId();

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
      return {
        stationId,
        excluded: true,
        variables: results,
      };
    }

    return {
      stationId,
      excluded: false,
      variables: results,
    };
  }


  function consolidatedRows(dataset) {
    const rowsByTimestamp =
      new Map();

    for (
      const variableData of
      dataset.variables
    ) {
      const key =
        variableData.variable;

      for (
        const record of
        variableData.records
      ) {
        const timestamp =
          String(
            record.timestamp ||
            ""
          );

        if (!timestamp) {
          continue;
        }

        if (
          !rowsByTimestamp.has(
            timestamp
          )
        ) {
          rowsByTimestamp.set(
            timestamp,
            {
              station_id:
                dataset.stationId,

              timestamp,

              temperature_observed:
                null,

              temperature_era5:
                null,

              temperature_nasa:
                null,

              humidity_observed:
                null,

              humidity_era5:
                null,

              humidity_nasa:
                null,

              pressure_observed:
                null,

              pressure_era5:
                null,

              pressure_nasa:
                null,

              dewpoint_observed:
                null,

              dewpoint_era5:
                null,

              dewpoint_nasa:
                null,

              precipitation_observed:
                null,

              precipitation_era5:
                null,

              precipitation_nasa:
                null,
            }
          );
        }

        const row =
          rowsByTimestamp.get(
            timestamp
          );

        row[
          `${key}_observed`
        ] =
          numberOrNull(
            record.observed
          );

        row[
          `${key}_era5`
        ] =
          numberOrNull(
            record.era5
          );

        row[
          `${key}_nasa`
        ] =
          numberOrNull(
            record.nasa
          );
      }
    }

    return Array.from(
      rowsByTimestamp.values()
    ).sort(
      (a, b) =>
        String(a.timestamp)
          .localeCompare(
            String(b.timestamp)
          )
    );
  }


  function csvContent(rows) {
    const headers = [
      "station_id",
      "timestamp",

      "temperature_observed_c",
      "temperature_era5_c",
      "temperature_nasa_c",

      "humidity_observed_pct",
      "humidity_era5_pct",
      "humidity_nasa_pct",

      "pressure_observed_hpa",
      "pressure_era5_hpa",
      "pressure_nasa_hpa",

      "dewpoint_observed_c",
      "dewpoint_era5_c",
      "dewpoint_nasa_c",

      "precipitation_observed_mm",
      "precipitation_era5_mm",
      "precipitation_nasa_mm",
    ];

    const fieldMap = [
      "station_id",
      "timestamp",

      "temperature_observed",
      "temperature_era5",
      "temperature_nasa",

      "humidity_observed",
      "humidity_era5",
      "humidity_nasa",

      "pressure_observed",
      "pressure_era5",
      "pressure_nasa",

      "dewpoint_observed",
      "dewpoint_era5",
      "dewpoint_nasa",

      "precipitation_observed",
      "precipitation_era5",
      "precipitation_nasa",
    ];

    const lines = [
      headers.join(","),
    ];

    for (
      const row of rows
    ) {
      lines.push(
        fieldMap.map(
          field =>
            csvEscape(
              row[field]
            )
        ).join(",")
      );
    }

    return (
      "\uFEFF"
      + lines.join("\n")
    );
  }


  function countComparable(
    records,
    source
  ) {
    return records.filter(
      record =>
        numberOrNull(
          record.observed
        ) !== null &&
        numberOrNull(
          record[source]
        ) !== null
    ).length;
  }


  function buildMetadata(
    dataset,
    rows
  ) {
    const variables = {};

    for (
      const variableData of
      dataset.variables
    ) {
      variables[
        variableData.variable
      ] = {
        label:
          VARIABLE_LABELS[
            variableData.variable
          ],

        unit:
          VARIABLE_UNITS[
            variableData.variable
          ],

        total_records:
          variableData.records.length,

        era5_comparable_pairs:
          countComparable(
            variableData.records,
            "era5"
          ),

        nasa_comparable_pairs:
          countComparable(
            variableData.records,
            "nasa"
          ),
      };
    }

    return {
      platform:
        "AtmosLink Research Platform",

      module:
        "Scientific Validation and Intelligence",

      export_version:
        "2.8",

      generated_at_local:
        isoLocalDate(),

      station: {
        id:
          dataset.stationId,

        selector_label:
          selectedStationLabel(),

        deployment_mode:
          deploymentMode() ||
          "FIELD",
      },

      scientific_scope: {
        temporal_resolution:
          "hourly",

        observation_source:
          "local meteorological station",

        model_sources: [
          "ERA5-Land",
          "NASA POWER",
        ],

        variables: [
          "temperature",
          "relative humidity",
          "atmospheric pressure",
          "dew point",
          "hourly precipitation",
        ],

        wind_note:
          dataset.stationId === "CU01"
            ? "Wind excluded because CU01 does not have a validated physical anemometer."
            : "Wind is handled separately according to station deployment status.",
      },

      dataset_summary: {
        consolidated_rows:
          rows.length,

        first_timestamp:
          rows.length
            ? rows[0].timestamp
            : null,

        last_timestamp:
          rows.length
            ? rows[
                rows.length - 1
              ].timestamp
            : null,

        variables,
      },

      methodological_note:
        "The export contains temporally paired hourly observations. Model products must be interpreted considering spatial resolution, elevation representation, temporal coverage and local instrumentation.",

      data:
        rows,
    };
  }


  function visibleScientificText() {
    const intelligence =
      byId(
        "atmoslinkScientificIntelligence"
      );

    const validation =
      byId(
        "scientificValidationV2"
      );

    const scatter =
      byId(
        "validationScatterModule"
      );

    const sections = [
      intelligence,
      validation,
      scatter,
    ]
      .filter(Boolean)
      .map(
        section =>
          section.innerText
            ?.trim()
      )
      .filter(Boolean);

    return sections.join(
      "\n\n========================================\n\n"
    );
  }


  function buildTextReport(
    dataset,
    rows
  ) {
    const lines = [];

    lines.push(
      "ATMOSLINK SCIENTIFIC REPORT"
    );

    lines.push(
      "========================================"
    );

    lines.push(
      `Estación: ${selectedStationLabel()}`
    );

    lines.push(
      `Station ID: ${dataset.stationId}`
    );

    lines.push(
      `Fecha de generación: ${isoLocalDate()}`
    );

    lines.push(
      `Modo de despliegue: ${deploymentMode() || "FIELD"}`
    );

    lines.push(
      `Filas horarias consolidadas: ${rows.length}`
    );

    if (rows.length) {
      lines.push(
        `Inicio: ${rows[0].timestamp}`
      );

      lines.push(
        `Fin: ${rows[rows.length - 1].timestamp}`
      );
    }

    lines.push("");
    lines.push(
      "COBERTURA POR VARIABLE"
    );

    lines.push(
      "----------------------------------------"
    );

    for (
      const variableData of
      dataset.variables
    ) {
      lines.push(
        `${VARIABLE_LABELS[variableData.variable]}:`
      );

      lines.push(
        `  Registros totales: ${variableData.records.length}`
      );

      lines.push(
        `  Pares ERA5-Land: ${countComparable(
          variableData.records,
          "era5"
        )}`
      );

      lines.push(
        `  Pares NASA POWER: ${countComparable(
          variableData.records,
          "nasa"
        )}`
      );
    }

    lines.push("");
    lines.push(
      "INTERPRETACIÓN MOSTRADA POR LA PLATAFORMA"
    );

    lines.push(
      "----------------------------------------"
    );

    lines.push(
      visibleScientificText() ||
      "No se encontró texto científico visible."
    );

    lines.push("");
    lines.push(
      "NOTA METODOLÓGICA"
    );

    lines.push(
      "----------------------------------------"
    );

    lines.push(
      "Los resultados constituyen análisis automáticos de apoyo y deben ser revisados por el investigador antes de incorporarlos en informes, artículos o decisiones metodológicas."
    );

    return lines.join("\n");
  }


  function setButtonBusy(
    button,
    busy,
    label
  ) {
    if (!button) {
      return;
    }

    if (busy) {
      button.dataset.originalLabel =
        button.textContent;

      button.textContent =
        label;

      button.disabled =
        true;

      button.classList.add(
        "atl-export-button--busy"
      );

    } else {
      button.textContent =
        button.dataset.originalLabel ||
        button.textContent;

      button.disabled =
        false;

      button.classList.remove(
        "atl-export-button--busy"
      );
    }
  }


  function showExportMessage(
    message,
    type = "ok"
  ) {
    const status =
      byId(
        "scientificExportStatus"
      );

    if (!status) {
      return;
    }

    status.textContent =
      message;

    status.dataset.type =
      type;

    window.clearTimeout(
      showExportMessage.timer
    );

    showExportMessage.timer =
      window.setTimeout(
        () => {
          status.textContent = "";
          status.removeAttribute(
            "data-type"
          );
        },
        6000
      );
  }


  async function exportCsv(
    button
  ) {
    setButtonBusy(
      button,
      true,
      "Generando CSV…"
    );

    try {
      const dataset =
        await loadScientificDataset();

      if (dataset.excluded) {
        throw new Error(
          "La validación científica de esta estación está excluida."
        );
      }

      const rows =
        consolidatedRows(
          dataset
        );

      if (!rows.length) {
        throw new Error(
          "No existen registros científicos para exportar."
        );
      }

      const filename =
        safeFilename(
          `AtmosLink_${dataset.stationId}_scientific_hourly_${timestampToken()}.csv`
        );

      downloadBlob(
        csvContent(rows),
        "text/csv",
        filename
      );

      showExportMessage(
        `CSV generado: ${rows.length} filas horarias.`
      );

    } catch (error) {
      console.error(
        "AtmosLink CSV export:",
        error
      );

      showExportMessage(
        error.message ||
        "No fue posible generar el CSV.",
        "error"
      );

    } finally {
      setButtonBusy(
        button,
        false
      );
    }
  }


  async function exportJson(
    button
  ) {
    setButtonBusy(
      button,
      true,
      "Generando JSON…"
    );

    try {
      const dataset =
        await loadScientificDataset();

      if (dataset.excluded) {
        throw new Error(
          "La validación científica de esta estación está excluida."
        );
      }

      const rows =
        consolidatedRows(
          dataset
        );

      const metadata =
        buildMetadata(
          dataset,
          rows
        );

      const filename =
        safeFilename(
          `AtmosLink_${dataset.stationId}_scientific_traceability_${timestampToken()}.json`
        );

      downloadBlob(
        JSON.stringify(
          metadata,
          null,
          2
        ),
        "application/json",
        filename
      );

      showExportMessage(
        "JSON científico y trazabilidad generados."
      );

    } catch (error) {
      console.error(
        "AtmosLink JSON export:",
        error
      );

      showExportMessage(
        error.message ||
        "No fue posible generar el JSON.",
        "error"
      );

    } finally {
      setButtonBusy(
        button,
        false
      );
    }
  }


  async function exportTxt(
    button
  ) {
    setButtonBusy(
      button,
      true,
      "Generando resumen…"
    );

    try {
      const dataset =
        await loadScientificDataset();

      if (dataset.excluded) {
        throw new Error(
          "La validación científica de esta estación está excluida."
        );
      }

      const rows =
        consolidatedRows(
          dataset
        );

      const report =
        buildTextReport(
          dataset,
          rows
        );

      const filename =
        safeFilename(
          `AtmosLink_${dataset.stationId}_scientific_summary_${timestampToken()}.txt`
        );

      downloadBlob(
        report,
        "text/plain",
        filename
      );

      showExportMessage(
        "Resumen científico TXT generado."
      );

    } catch (error) {
      console.error(
        "AtmosLink TXT export:",
        error
      );

      showExportMessage(
        error.message ||
        "No fue posible generar el resumen.",
        "error"
      );

    } finally {
      setButtonBusy(
        button,
        false
      );
    }
  }


  function printScientificReport(
    button
  ) {
    setButtonBusy(
      button,
      true,
      "Preparando PDF…"
    );

    try {
      document.body.classList.add(
        "atl-scientific-print-mode"
      );

      document.documentElement
        .dataset.printStation =
          selectedStationId();

      document.documentElement
        .dataset.printGenerated =
          isoLocalDate();

      window.setTimeout(
        () => {
          window.print();

          window.setTimeout(
            () => {
              document.body.classList.remove(
                "atl-scientific-print-mode"
              );

              setButtonBusy(
                button,
                false
              );
            },
            500
          );
        },
        250
      );

    } catch (error) {
      console.error(
        "AtmosLink print export:",
        error
      );

      document.body.classList.remove(
        "atl-scientific-print-mode"
      );

      setButtonBusy(
        button,
        false
      );

      showExportMessage(
        "No fue posible preparar la impresión.",
        "error"
      );
    }
  }


  function exportPanelHtml() {
    return `
      <section
        id="scientificExportPanel"
        class="atl-scientific-export-panel"
      >

        <div class="atl-scientific-export-panel__header">

          <div>
            <span class="atl-scientific-export-panel__eyebrow">
              SCIENTIFIC DATA EXPORT
            </span>

            <h3>
              Exportación científica
            </h3>

            <p>
              Descarga de datos horarios, metadatos,
              trazabilidad y versión imprimible del análisis.
            </p>
          </div>

          <span class="atl-scientific-export-panel__badge">
            V2.8
          </span>

        </div>

        <div class="atl-scientific-export-panel__buttons">

          <button
            type="button"
            class="atl-export-button"
            data-export-action="csv"
          >
            CSV horario
          </button>

          <button
            type="button"
            class="atl-export-button"
            data-export-action="json"
          >
            JSON científico
          </button>

          <button
            type="button"
            class="atl-export-button"
            data-export-action="txt"
          >
            Resumen TXT
          </button>

          <button
            type="button"
            class="
              atl-export-button
              atl-export-button--primary
            "
            data-export-action="print"
          >
            Guardar como PDF
          </button>

        </div>

        <div
          id="scientificExportStatus"
          class="atl-scientific-export-panel__status"
          aria-live="polite"
        ></div>

        <div class="atl-scientific-export-panel__note">
          El archivo PDF se genera mediante el cuadro de
          impresión del navegador. Selecciona
          “Guardar como PDF”.
        </div>

      </section>
    `;
  }


  function ensureExportPanel() {
    const intelligence =
      byId(
        "atmoslinkScientificIntelligence"
      );

    if (!intelligence) {
      return false;
    }

    if (
      byId(
        "scientificExportPanel"
      )
    ) {
      return true;
    }

    intelligence.insertAdjacentHTML(
      "beforeend",
      exportPanelHtml()
    );

    bindButtons();

    return true;
  }


  function bindButtons() {
    document
      .querySelectorAll(
        "[data-export-action]"
      )
      .forEach(
        button => {
          if (
            button.dataset.bound ===
            "true"
          ) {
            return;
          }

          button.dataset.bound =
            "true";

          button.addEventListener(
            "click",
            () => {
              const action =
                button.dataset
                  .exportAction;

              if (
                action === "csv"
              ) {
                exportCsv(
                  button
                );

              } else if (
                action === "json"
              ) {
                exportJson(
                  button
                );

              } else if (
                action === "txt"
              ) {
                exportTxt(
                  button
                );

              } else if (
                action === "print"
              ) {
                printScientificReport(
                  button
                );
              }
            }
          );
        }
      );
  }


  function refreshPanel() {
    /*
     * Scientific Intelligence se renderiza de forma
     * asíncrona. Se intenta varias veces sin modificar
     * el módulo principal.
     */

    if (
      ensureExportPanel()
    ) {
      return;
    }

    let attempts = 0;

    const timer =
      window.setInterval(
        () => {
          attempts += 1;

          if (
            ensureExportPanel() ||
            attempts >= 20
          ) {
            window.clearInterval(
              timer
            );
          }
        },
        500
      );
  }


  document.addEventListener(
    "DOMContentLoaded",
    () => {
      window.setTimeout(
        refreshPanel,
        1800
      );

      byId("stationSelector")
        ?.addEventListener(
          "change",
          () => {
            window.setTimeout(
              refreshPanel,
              700
            );
          }
        );
    }
  );


  window.addEventListener(
    "atmoslink:station-updated",
    refreshPanel
  );


  window.addEventListener(
    "atmoslink:deployment-mode",
    refreshPanel
  );


  window.AtmosLinkScientificExports = {
    refresh:
      refreshPanel,

    csv:
      exportCsv,

    json:
      exportJson,

    text:
      exportTxt,

    print:
      printScientificReport,
  };
})();
