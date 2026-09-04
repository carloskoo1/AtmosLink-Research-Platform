/* =========================================================
   ATMOSLINK SCIENTIFIC TEMPORAL COMPARISON
   Local observation vs ERA5-Land vs NASA POWER
   Native SVG
   ========================================================= */

(() => {
  "use strict";

  const SVG_NS =
    "http://www.w3.org/2000/svg";

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

    const number = Number(value);

    return Number.isFinite(number)
      ? number
      : null;
  }

  function svgElement(
    name,
    attributes = {}
  ) {
    const element =
      document.createElementNS(
        SVG_NS,
        name
      );

    Object.entries(
      attributes
    ).forEach(
      ([key, value]) => {
        element.setAttribute(
          key,
          value
        );
      }
    );

    return element;
  }

  function formatNumber(
    value,
    digits = 2
  ) {
    const number =
      finiteNumber(value);

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

  function formatDate(value) {
    if (!value) {
      return "—";
    }

    const date =
      new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return String(value);
    }

    return new Intl.DateTimeFormat(
      "es-PE",
      {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }
    ).format(date);
  }

  function createTemporalModule() {
    if (
      byId(
        "validationTemporalModule"
      )
    ) {
      return;
    }

    const scatter =
      byId(
        "validationScatterModule"
      );

    if (!scatter) {
      return;
    }

    const module =
      document.createElement(
        "div"
      );

    module.id =
      "validationTemporalModule";

    module.className =
      "atl-temporal-module";

    module.innerHTML = `
      <div class="atl-section__head">
        <div>
          <span class="atl-eyebrow">
            EVOLUCIÓN TEMPORAL COMPARADA
          </span>

          <h3 id="validationTemporalTitle">
            Serie horaria Local–ERA5–NASA
          </h3>

          <p class="atl-section__description">
            Comparación temporal de observaciones locales
            y productos meteorológicos emparejados por hora.
          </p>
        </div>

        <span id="validationTemporalStatus"
              class="atl-chip">
          Cargando…
        </span>
      </div>

      <div class="atl-temporal-legend">
        <span>
          <i class="atl-temporal-key atl-temporal-key--local"></i>
          Observación local
        </span>

        <span>
          <i class="atl-temporal-key atl-temporal-key--era5"></i>
          ERA5-Land
        </span>

        <span>
          <i class="atl-temporal-key atl-temporal-key--nasa"></i>
          NASA POWER
        </span>
      </div>

      <div id="validationTemporalChart"
           class="atl-temporal-chart">
      </div>

      <div id="validationTemporalSummary"
           class="atl-temporal-summary">
      </div>
    `;

    scatter.insertAdjacentElement(
      "afterend",
      module
    );
  }

  function splitSegments(
    records,
    field
  ) {
    const segments = [];
    let current = [];

    records.forEach(
      (record, index) => {
        const value =
          finiteNumber(
            record[field]
          );

        if (value === null) {
          if (current.length) {
            segments.push(
              current
            );

            current = [];
          }

          return;
        }

        current.push(
          {
            index,
            value,
          }
        );
      }
    );

    if (current.length) {
      segments.push(
        current
      );
    }

    return segments;
  }

  function renderTemporalChart(
    payload
  ) {
    const container =
      byId(
        "validationTemporalChart"
      );

    if (!container) {
      return;
    }

    container.innerHTML = "";

    const records =
      payload.records || [];

    if (!records.length) {
      container.textContent =
        "No existen registros horarios disponibles.";

      return;
    }

    const validValues =
      records.flatMap(
        record => [
          finiteNumber(
            record.observed
          ),
          finiteNumber(
            record.era5
          ),
          finiteNumber(
            record.nasa
          ),
        ]
      ).filter(
        value =>
          value !== null
      );

    if (!validValues.length) {
      container.textContent =
        "No existen valores temporalmente comparables.";

      return;
    }

    const width = 1240;
    const height = 480;

    const margin = {
      top: 28,
      right: 32,
      bottom: 64,
      left: 78,
    };

    let minimum =
      Math.min(
        ...validValues
      );

    let maximum =
      Math.max(
        ...validValues
      );

    if (minimum === maximum) {
      minimum -= 1;
      maximum += 1;
    }

    const padding =
      (maximum - minimum) *
      0.07;

    minimum -= padding;
    maximum += padding;

    const plotWidth =
      width -
      margin.left -
      margin.right;

    const plotHeight =
      height -
      margin.top -
      margin.bottom;

    const xScale = index =>
      margin.left +
      (
        index /
        Math.max(
          1,
          records.length - 1
        )
      ) *
      plotWidth;

    const yScale = value =>
      margin.top +
      plotHeight -
      (
        (value - minimum) /
        (maximum - minimum)
      ) *
      plotHeight;

    const svg =
      svgElement(
        "svg",
        {
          viewBox:
            `0 0 ${width} ${height}`,
          role: "img",
          "aria-label":
            `Serie temporal de ${payload.label}`,
        }
      );

    for (
      let index = 0;
      index <= 5;
      index += 1
    ) {
      const value =
        minimum +
        (
          (maximum - minimum) *
          index /
          5
        );

      const y =
        yScale(value);

      svg.appendChild(
        svgElement(
          "line",
          {
            x1: margin.left,
            y1: y,
            x2:
              margin.left +
              plotWidth,
            y2: y,
            class:
              "atl-temporal-grid-line",
          }
        )
      );

      const label =
        svgElement(
          "text",
          {
            x:
              margin.left -
              12,
            y: y + 4,
            "text-anchor": "end",
            class:
              "atl-temporal-axis-text",
          }
        );

      label.textContent =
        formatNumber(
          value,
          1
        );

      svg.appendChild(
        label
      );
    }

    const temporalPositions = [
      0,
      Math.floor(
        (records.length - 1) /
        2
      ),
      records.length - 1,
    ];

    temporalPositions.forEach(
      index => {
        const x =
          xScale(index);

        svg.appendChild(
          svgElement(
            "line",
            {
              x1: x,
              y1: margin.top,
              x2: x,
              y2:
                margin.top +
                plotHeight,
              class:
                "atl-temporal-grid-line",
            }
          )
        );

        const label =
          svgElement(
            "text",
            {
              x,
              y:
                margin.top +
                plotHeight +
                28,
              "text-anchor":
                index === 0
                  ? "start"
                  : index ===
                    records.length - 1
                    ? "end"
                    : "middle",
              class:
                "atl-temporal-axis-text",
            }
          );

        label.textContent =
          formatDate(
            records[index]
              ?.timestamp
          );

        svg.appendChild(
          label
        );
      }
    );

    const sources = [
      {
        field: "observed",
        css:
          "atl-temporal-line--local",
      },
      {
        field: "era5",
        css:
          "atl-temporal-line--era5",
      },
      {
        field: "nasa",
        css:
          "atl-temporal-line--nasa",
      },
    ];

    sources.forEach(
      source => {
        const segments =
          splitSegments(
            records,
            source.field
          );

        segments.forEach(
          segment => {
            const points =
              segment.map(
                point =>
                  `${xScale(
                    point.index
                  )},${yScale(
                    point.value
                  )}`
              ).join(" ");

            svg.appendChild(
              svgElement(
                "polyline",
                {
                  points,
                  class:
                    `atl-temporal-line ${source.css}`,
                }
              )
            );
          }
        );
      }
    );

    const yLabel =
      svgElement(
        "text",
        {
          x: 20,
          y:
            margin.top +
            plotHeight / 2,
          transform:
            `rotate(-90 20 ${
              margin.top +
              plotHeight / 2
            })`,
          "text-anchor": "middle",
          class:
            "atl-temporal-axis-label",
        }
      );

    yLabel.textContent =
      `${payload.label} (${payload.unit})`;

    svg.appendChild(
      yLabel
    );

    const xLabel =
      svgElement(
        "text",
        {
          x:
            margin.left +
            plotWidth / 2,
          y: height - 14,
          "text-anchor": "middle",
          class:
            "atl-temporal-axis-label",
        }
      );

    xLabel.textContent =
      "Tiempo";

    svg.appendChild(
      xLabel
    );

    container.appendChild(
      svg
    );
  }

  function renderTemporalSummary(
    payload
  ) {
    const target =
      byId(
        "validationTemporalSummary"
      );

    if (!target) {
      return;
    }

    const records =
      payload.records || [];

    const localCount =
      records.filter(
        record =>
          finiteNumber(
            record.observed
          ) !== null
      ).length;

    const era5Count =
      records.filter(
        record =>
          finiteNumber(
            record.observed
          ) !== null &&
          finiteNumber(
            record.era5
          ) !== null
      ).length;

    const nasaCount =
      records.filter(
        record =>
          finiteNumber(
            record.observed
          ) !== null &&
          finiteNumber(
            record.nasa
          ) !== null
      ).length;

    target.innerHTML = `
      <span>
        <strong>Horas locales</strong>
        ${localCount}
      </span>

      <span>
        <strong>Pares ERA5-Land</strong>
        ${era5Count}
      </span>

      <span>
        <strong>Pares NASA POWER</strong>
        ${nasaCount}
      </span>

      <span>
        <strong>Inicio</strong>
        ${formatDate(
          records[0]?.timestamp
        )}
      </span>

      <span>
        <strong>Fin</strong>
        ${formatDate(
          records[
            records.length - 1
          ]?.timestamp
        )}
      </span>
    `;
  }

  /* ATMOSLINK_STATION_RESPONSE_ISOLATION_V1 */
  let temporalRequestGeneration = 0;
  
  async function loadTemporalValidation() {
    const requestGeneration = ++temporalRequestGeneration;
    createTemporalModule();

    const container =
      byId(
        "validationTemporalModule"
      );

    if (!container) {
      return;
    }

    const stationId =
      byId("stationSelector")
        ?.value ||
      "CU01";

    const variable =
      byId(
        "validationScatterVariable"
      )?.value ||
      "temperature";

    const status =
      byId(
        "validationTemporalStatus"
      );

    try {
      const response = await fetch(
        `/api/scientific/hourly`
        + `?station_id=${encodeURIComponent(stationId)}`
        + `&variable=${encodeURIComponent(variable)}`,
        {
          cache: "no-store",
          headers: {
            Accept: "application/json",
          },
        }
      );

      const payload =
        await response.json();
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
        requestGeneration !== temporalRequestGeneration ||
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
        status.textContent =
          "NO HABILITADA";

        byId(
          "validationTemporalChart"
        ).textContent =
          payload.reason;

        byId(
          "validationTemporalSummary"
        ).innerHTML = "";

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

      byId(
        "validationTemporalTitle"
      ).textContent =
        `${payload.label}: Local vs ERA5-Land vs NASA POWER`;

      status.textContent =
        `${payload.rows} horas`;

      renderTemporalChart(
        payload
      );

      renderTemporalSummary(
        payload
      );

    } catch (error) {
      console.error(
        "Serie temporal científica:",
        error
      );

      status.textContent =
        "ERROR";

      byId(
        "validationTemporalChart"
      ).textContent =
        "No fue posible cargar la comparación temporal.";
    }
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      createTemporalModule();
      loadTemporalValidation();

      byId(
        "validationScatterVariable"
      )?.addEventListener(
        "change",
        loadTemporalValidation
      );

      byId(
        "stationSelector"
      )?.addEventListener(
        "change",
        loadTemporalValidation
      );

      window.setInterval(
        loadTemporalValidation,
        300000
      );
    }
  );
})();
