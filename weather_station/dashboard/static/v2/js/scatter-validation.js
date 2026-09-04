/* =========================================================
   ATMOSLINK SCIENTIFIC SCATTER VALIDATION
   Native SVG
   ========================================================= */

(() => {
  "use strict";

  const SVG_NS =
    "http://www.w3.org/2000/svg";

  function byId(id) {
    return document.getElementById(id);
  }

  function number(value) {
    /*
     * Evita convertir valores ausentes en cero.
     *
     * En JavaScript:
     *   Number(null) === 0
     *   Number("") === 0
     *
     * Esas conversiones generaban puntos artificiales sobre
     * y = 0 y distorsionaban BIAS, MAE, RMSE, r y R².
     */
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return null;
    }

    const parsed = Number(value);

    return Number.isFinite(parsed)
      ? parsed
      : null;
  }

  function format(
    value,
    digits = 3
  ) {
    const parsed = number(value);

    if (parsed === null) {
      return "—";
    }

    return new Intl.NumberFormat(
      "es-PE",
      {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }
    ).format(parsed);
  }

  function calculateMetrics(
    records,
    source
  ) {
    const pairs = records
      .map(record => ({
        observed: number(record.observed),
        modeled: number(record[source]),
      }))
      .filter(
        pair =>
          pair.observed !== null &&
          pair.modeled !== null
      );

    const count = pairs.length;

    if (!count) {
      return {
        count: 0,
        pairs: [],
      };
    }

    const errors = pairs.map(
      pair =>
        pair.modeled -
        pair.observed
    );

    const bias =
      errors.reduce(
        (sum, value) =>
          sum + value,
        0
      ) / count;

    const mae =
      errors.reduce(
        (sum, value) =>
          sum + Math.abs(value),
        0
      ) / count;

    const rmse = Math.sqrt(
      errors.reduce(
        (sum, value) =>
          sum + value ** 2,
        0
      ) / count
    );

    const observedMean =
      pairs.reduce(
        (sum, pair) =>
          sum + pair.observed,
        0
      ) / count;

    const modeledMean =
      pairs.reduce(
        (sum, pair) =>
          sum + pair.modeled,
        0
      ) / count;

    let covariance = 0;
    let observedVariance = 0;
    let modeledVariance = 0;

    pairs.forEach(pair => {
      const observedDelta =
        pair.observed -
        observedMean;

      const modeledDelta =
        pair.modeled -
        modeledMean;

      covariance +=
        observedDelta *
        modeledDelta;

      observedVariance +=
        observedDelta ** 2;

      modeledVariance +=
        modeledDelta ** 2;
    });

    const denominator = Math.sqrt(
      observedVariance *
      modeledVariance
    );

    const pearson =
      denominator > 0
        ? covariance / denominator
        : null;

    return {
      count,
      pairs,
      bias,
      mae,
      rmse,
      pearson,
      rSquared:
        pearson === null
          ? null
          : pearson ** 2,
      regression:
        calculateLinearRegression(
          pairs
        ),
    };
  }

  function calculateLinearRegression(
    pairs
  ) {
    const count = pairs.length;

    if (count < 3) {
      return null;
    }

    const meanX =
      pairs.reduce(
        (sum, pair) =>
          sum + pair.observed,
        0
      ) / count;

    const meanY =
      pairs.reduce(
        (sum, pair) =>
          sum + pair.modeled,
        0
      ) / count;

    let sxx = 0;
    let sxy = 0;

    pairs.forEach(pair => {
      const dx =
        pair.observed - meanX;

      const dy =
        pair.modeled - meanY;

      sxx += dx ** 2;
      sxy += dx * dy;
    });

    if (sxx <= 0) {
      return null;
    }

    const slope =
      sxy / sxx;

    const intercept =
      meanY -
      slope * meanX;

    let residualSumSquares = 0;

    pairs.forEach(pair => {
      const predicted =
        intercept +
        slope * pair.observed;

      residualSumSquares +=
        (
          pair.modeled -
          predicted
        ) ** 2;
    });

    const residualStdError =
      count > 2
        ? Math.sqrt(
            residualSumSquares /
            (count - 2)
          )
        : null;

    return {
      slope,
      intercept,
      meanX,
      sxx,
      count,
      residualStdError,
    };
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

  function renderScatter(
    containerId,
    metrics,
    label,
    unit,
    sourceKey
  ) {
    const container =
      byId(containerId);

    if (!container) {
      return;
    }

    container.innerHTML = "";

    if (!metrics.count) {
      container.textContent =
        "No existen pares válidos.";

      return;
    }

    const width = 620;
    const height = 420;
    const margin = {
      top: 24,
      right: 24,
      bottom: 62,
      left: 72,
    };

    const values =
      metrics.pairs.flatMap(
        pair => [
          pair.observed,
          pair.modeled,
        ]
      );

    let minimum =
      Math.min(...values);

    let maximum =
      Math.max(...values);

    if (minimum === maximum) {
      minimum -= 1;
      maximum += 1;
    }

    const padding =
      (maximum - minimum) *
      0.06;

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

    const scaleX = value =>
      margin.left +
      (
        (value - minimum) /
        (maximum - minimum)
      ) *
      plotWidth;

    const scaleY = value =>
      margin.top +
      plotHeight -
      (
        (value - minimum) /
        (maximum - minimum)
      ) *
      plotHeight;

    const svg = svgElement(
      "svg",
      {
        viewBox:
          `0 0 ${width} ${height}`,
        role: "img",
        "aria-label":
          `Dispersión ${label}`,
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

      const x = scaleX(value);
      const y = scaleY(value);

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
              "atl-scatter-grid-line",
          }
        )
      );

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
              "atl-scatter-grid-line",
          }
        )
      );

      const xText =
        svgElement(
          "text",
          {
            x,
            y:
              margin.top +
              plotHeight +
              24,
            "text-anchor": "middle",
            class:
              "atl-scatter-axis-text",
          }
        );

      xText.textContent =
        format(value, 1);

      svg.appendChild(xText);

      const yText =
        svgElement(
          "text",
          {
            x:
              margin.left -
              12,
            y: y + 4,
            "text-anchor": "end",
            class:
              "atl-scatter-axis-text",
          }
        );

      yText.textContent =
        format(value, 1);

      svg.appendChild(yText);
    }

    svg.appendChild(
      svgElement(
        "line",
        {
          x1: scaleX(minimum),
          y1: scaleY(minimum),
          x2: scaleX(maximum),
          y2: scaleY(maximum),
          class:
            "atl-scatter-reference-line",
        }
      )
    );

    const regression =
      metrics.regression;

    if (
      regression &&
      Number.isFinite(
        regression.residualStdError
      )
    ) {
      const sampleCount = 80;
      const upperPoints = [];
      const lowerPoints = [];

      for (
        let index = 0;
        index <= sampleCount;
        index += 1
      ) {
        const x =
          minimum +
          (
            (maximum - minimum) *
            index /
            sampleCount
          );

        const predicted =
          regression.intercept +
          regression.slope * x;

        const standardErrorMean =
          regression.residualStdError *
          Math.sqrt(
            1 / regression.count +
            (
              (x - regression.meanX) ** 2 /
              regression.sxx
            )
          );

        const confidence95 =
          1.96 *
          standardErrorMean;

        const upper =
          Math.min(
            maximum,
            predicted +
            confidence95
          );

        const lower =
          Math.max(
            minimum,
            predicted -
            confidence95
          );

        upperPoints.push(
          `${scaleX(x)},${scaleY(upper)}`
        );

        lowerPoints.push(
          `${scaleX(x)},${scaleY(lower)}`
        );
      }

      const confidencePolygon =
        svgElement(
          "polygon",
          {
            points:
              upperPoints
                .concat(
                  lowerPoints.reverse()
                )
                .join(" "),
            class:
              `atl-scatter-confidence-band ` +
              `atl-scatter-confidence-band--${sourceKey}`,
          }
        );

      svg.appendChild(
        confidencePolygon
      );

      const regressionY1 =
        regression.intercept +
        regression.slope * minimum;

      const regressionY2 =
        regression.intercept +
        regression.slope * maximum;

      svg.appendChild(
        svgElement(
          "line",
          {
            x1: scaleX(minimum),
            y1: scaleY(regressionY1),
            x2: scaleX(maximum),
            y2: scaleY(regressionY2),
            class:
              `atl-scatter-regression-line ` +
              `atl-scatter-regression-line--${sourceKey}`,
          }
        )
      );

      const equationBackground =
        svgElement(
          "rect",
          {
            x: margin.left + 12,
            y: margin.top + 12,
            width: 190,
            height: 54,
            rx: 7,
            class:
              "atl-scatter-equation-background",
          }
        );

      svg.appendChild(
        equationBackground
      );

      const equationText =
        svgElement(
          "text",
          {
            x: margin.left + 22,
            y: margin.top + 34,
            class:
              "atl-scatter-equation-text",
          }
        );

      const sign =
        regression.intercept >= 0
          ? "+"
          : "−";

      equationText.textContent =
        `y = ${format(
          regression.slope,
          3
        )}x ${sign} ${format(
          Math.abs(
            regression.intercept
          ),
          3
        )}`;

      svg.appendChild(
        equationText
      );

      const rSquaredText =
        svgElement(
          "text",
          {
            x: margin.left + 22,
            y: margin.top + 54,
            class:
              "atl-scatter-equation-text",
          }
        );

      rSquaredText.textContent =
        `R² = ${format(
          metrics.rSquared,
          3
        )}`;

      svg.appendChild(
        rSquaredText
      );
    }

    metrics.pairs.forEach(
      pair => {
        const point =
          svgElement(
            "circle",
            {
              cx:
                scaleX(
                  pair.observed
                ),
              cy:
                scaleY(
                  pair.modeled
                ),
              r: 3.2,
              class:
                `atl-scatter-point ` +
                `atl-scatter-point--${sourceKey}`,
            }
          );

        const title =
          svgElement(
            "title"
          );

        title.textContent =
          `Observado: ${format(
            pair.observed,
            3
          )} ${unit}; `
          + `modelo: ${format(
            pair.modeled,
            3
          )} ${unit}`;

        point.appendChild(
          title
        );

        svg.appendChild(
          point
        );
      }
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
            "atl-scatter-axis-label",
        }
      );

    xLabel.textContent =
      `Observado (${unit})`;

    svg.appendChild(
      xLabel
    );

    const yLabel =
      svgElement(
        "text",
        {
          x: 18,
          y:
            margin.top +
            plotHeight / 2,
          transform:
            `rotate(-90 18 ${
              margin.top +
              plotHeight / 2
            })`,
          "text-anchor": "middle",
          class:
            "atl-scatter-axis-label",
        }
      );

    yLabel.textContent =
      `Modelado (${unit})`;

    svg.appendChild(
      yLabel
    );

    container.appendChild(
      svg
    );
  }

  function renderMetrics(
    targetId,
    metrics,
    unit
  ) {
    const target =
      byId(targetId);

    if (!target) {
      return;
    }

    target.innerHTML = `
      <span>
        <strong>BIAS</strong>
        ${format(metrics.bias)} ${unit}
      </span>

      <span>
        <strong>MAE</strong>
        ${format(metrics.mae)} ${unit}
      </span>

      <span>
        <strong>RMSE</strong>
        ${format(metrics.rmse)} ${unit}
      </span>

      <span>
        <strong>r</strong>
        ${format(metrics.pearson)}
      </span>

      <span>
        <strong>R²</strong>
        ${format(metrics.rSquared)}
      </span>
    `;
  }

  function buildScientificInterpretation(
    payload,
    era5,
    nasa
  ) {
    if (
      !era5.count ||
      !nasa.count
    ) {
      return (
        "<strong>Resultado:</strong> " +
        "No existen suficientes pares horarios válidos " +
        "para realizar una comparación científica."
      );
    }

    const era5Rmse =
      number(era5.rmse);

    const nasaRmse =
      number(nasa.rmse);

    const era5Bias =
      number(era5.bias);

    const nasaBias =
      number(nasa.bias);

    const era5R =
      number(era5.pearson);

    const nasaR =
      number(nasa.pearson);

    const lowerRmseSource =
      era5Rmse < nasaRmse
        ? "ERA5-Land"
        : nasaRmse < era5Rmse
          ? "NASA POWER"
          : "ambas fuentes";

    const lowerBiasSource =
      Math.abs(era5Bias) <
      Math.abs(nasaBias)
        ? "ERA5-Land"
        : Math.abs(nasaBias) <
          Math.abs(era5Bias)
          ? "NASA POWER"
          : "ambas fuentes";

    const higherCorrelationSource =
      era5R > nasaR
        ? "ERA5-Land"
        : nasaR > era5R
          ? "NASA POWER"
          : "ambas fuentes";

    const unit =
      payload.unit || "";

    const variable =
      payload.variable;

    const common =
      `Se utilizaron ${era5.count} pares ERA5-Land ` +
      `y ${nasa.count} pares NASA POWER.`;

    if (
      variable === "precipitation"
    ) {
      return (
        "<strong>Interpretación científica:</strong> " +
        `${lowerRmseSource} presenta el menor RMSE ` +
        `para precipitación horaria. Sin embargo, ` +
        `la interpretación de r y R² debe realizarse ` +
        `con cautela debido al predominio de horas sin lluvia ` +
        `y a la naturaleza intermitente de la precipitación. ` +
        `${common}`
      );
    }

    if (
      variable === "pressure"
    ) {
      return (
        "<strong>Interpretación científica:</strong> " +
        `${lowerRmseSource} presenta el menor RMSE, mientras ` +
        `${lowerBiasSource} presenta el menor sesgo absoluto. ` +
        `Las diferencias sistemáticas de presión deben evaluarse ` +
        `considerando la altitud, la resolución espacial del modelo ` +
        `y la referencia barométrica utilizada. ` +
        `${common}`
      );
    }

    if (
      variable === "humidity"
    ) {
      return (
        "<strong>Interpretación científica:</strong> " +
        `${lowerRmseSource} presenta el menor RMSE para humedad ` +
        `relativa; ${higherCorrelationSource} reproduce mejor ` +
        `la variabilidad temporal. ` +
        `${lowerBiasSource} presenta el menor sesgo absoluto. ` +
        `${common}`
      );
    }

    if (
      variable === "dewpoint"
    ) {
      return (
        "<strong>Interpretación científica:</strong> " +
        `${lowerRmseSource} presenta el menor RMSE para el punto ` +
        `de rocío; ${higherCorrelationSource} presenta la mayor ` +
        `correlación temporal. ` +
        `${lowerBiasSource} presenta el menor sesgo absoluto. ` +
        `${common}`
      );
    }

    return (
      "<strong>Interpretación científica:</strong> " +
      `${lowerRmseSource} presenta el menor RMSE para ` +
      `${payload.label.toLowerCase()}; ` +
      `${lowerBiasSource} presenta el menor sesgo absoluto y ` +
      `${higherCorrelationSource} reproduce mejor la variabilidad ` +
      `temporal. ` +
      `RMSE ERA5-Land: ${format(era5Rmse)} ${unit}; ` +
      `RMSE NASA POWER: ${format(nasaRmse)} ${unit}. ` +
      `${common}`
    );
  }


  /* ATMOSLINK_STATION_RESPONSE_ISOLATION_V1 */
  let scatterRequestGeneration = 0;
  
  async function loadScatterValidation() {
    const requestGeneration = ++scatterRequestGeneration;
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
        "validationScatterStatus"
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
        requestGeneration !== scatterRequestGeneration ||
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
        status.innerHTML = `
          <strong>
            Validación no habilitada:
          </strong>
          ${payload.reason}
        `;

        const era5Chart =
          byId("era5ScatterChart");

        const nasaChart =
          byId("nasaScatterChart");

        if (era5Chart) {
          era5Chart.innerHTML =
            "Sin datos publicables.";
        }

        if (nasaChart) {
          nasaChart.innerHTML =
            "Sin datos publicables.";
        }

        const era5N =
          byId("era5ScatterN");

        const nasaN =
          byId("nasaScatterN");

        if (era5N) {
          era5N.textContent =
            "N=0";
        }

        if (nasaN) {
          nasaN.textContent =
            "N=0";
        }

        const era5Metrics =
          byId("era5ScatterMetrics");

        const nasaMetrics =
          byId("nasaScatterMetrics");

        const unavailableMetrics = `
          <span>
            <strong>BIAS</strong>
            —
          </span>

          <span>
            <strong>MAE</strong>
            —
          </span>

          <span>
            <strong>RMSE</strong>
            —
          </span>

          <span>
            <strong>r</strong>
            —
          </span>

          <span>
            <strong>R²</strong>
            —
          </span>
        `;

        if (era5Metrics) {
          era5Metrics.innerHTML =
            unavailableMetrics;
        }

        if (nasaMetrics) {
          nasaMetrics.innerHTML =
            unavailableMetrics;
        }

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

      const era5 =
        calculateMetrics(
          payload.records,
          "era5"
        );

      const nasa =
        calculateMetrics(
          payload.records,
          "nasa"
        );

      byId(
        "era5ScatterTitle"
      ).textContent =
        `${payload.label}: observado vs ERA5-Land`;

      byId(
        "nasaScatterTitle"
      ).textContent =
        `${payload.label}: observado vs NASA POWER`;

      byId(
        "era5ScatterN"
      ).textContent =
        `N=${era5.count}`;

      byId(
        "nasaScatterN"
      ).textContent =
        `N=${nasa.count}`;

      renderScatter(
        "era5ScatterChart",
        era5,
        payload.label,
        payload.unit,
        "era5"
      );

      renderScatter(
        "nasaScatterChart",
        nasa,
        payload.label,
        payload.unit,
        "nasa"
      );

      renderMetrics(
        "era5ScatterMetrics",
        era5,
        payload.unit
      );

      renderMetrics(
        "nasaScatterMetrics",
        nasa,
        payload.unit
      );

      status.innerHTML =
        buildScientificInterpretation(
          payload,
          era5,
          nasa
        );

    } catch (error) {
      console.error(
        "Scatter científico:",
        error
      );

      status.innerHTML = `
        <strong>Error:</strong>
        No fue posible cargar los diagramas
        de dispersión científica.
      `;
    }
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      loadScatterValidation();

      byId(
        "validationScatterVariable"
      )?.addEventListener(
        "change",
        loadScatterValidation
      );

      byId(
        "stationSelector"
      )?.addEventListener(
        "change",
        loadScatterValidation
      );

      window.setInterval(
        loadScatterValidation,
        300000
      );
    }
  );
})();
