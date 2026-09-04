(() => {
  "use strict";

  const directions = [
    "N", "NNE", "NE", "ENE",
    "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW",
    "W", "WNW", "NW", "NNW"
  ];

  const byId = id => document.getElementById(id);

  function localIsoDate(date) {
    const offset =
      date.getTimezoneOffset() * 60000;

    return new Date(date.getTime() - offset)
      .toISOString()
      .slice(0, 10);
  }

  function displayDate(value) {
    if (!value) {
      return "—";
    }

    return value
      .split("-")
      .reverse()
      .join("/");
  }

  function updateDateVisibility() {
    const period =
      byId("professionalWindRosePeriod")
        ?.value || "24h";

    const label =
      byId("professionalWindRoseDateLabel");

    if (label) {
      label.hidden = period !== "date";
    }
  }

  function stationId() {
    return byId("stationSelector")?.value || "CU01";
  }

  function setText(id, value) {
    const element = byId(id);

    if (element) {
      element.textContent = value;
    }
  }

  function format(value, digits = 2) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
      return "—";
    }

    return number.toLocaleString(
      "es-PE",
      {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
      }
    );
  }

  function polar(cx, cy, radius, angleDegrees) {
    const angle =
      (angleDegrees - 90) * Math.PI / 180;

    return {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle)
    };
  }

  function sectorPath(
    cx,
    cy,
    innerRadius,
    outerRadius,
    startAngle,
    endAngle
  ) {
    const p1 = polar(
      cx, cy, outerRadius, startAngle
    );
    const p2 = polar(
      cx, cy, outerRadius, endAngle
    );
    const p3 = polar(
      cx, cy, innerRadius, endAngle
    );
    const p4 = polar(
      cx, cy, innerRadius, startAngle
    );

    return [
      `M ${p1.x} ${p1.y}`,
      `A ${outerRadius} ${outerRadius} 0 0 1 ${p2.x} ${p2.y}`,
      `L ${p3.x} ${p3.y}`,
      `A ${innerRadius} ${innerRadius} 0 0 0 ${p4.x} ${p4.y}`,
      "Z"
    ].join(" ");
  }

  function speedColor(speed, maximum) {
    const ratio =
      maximum > 0
        ? Math.min(speed / maximum, 1)
        : 0;

    const hue = 205 - ratio * 170;

    return `hsl(${hue} 78% 48%)`;
  }

  function renderChart(payload) {
    const container =
      byId("professionalWindRoseChart");

    if (!container) {
      return;
    }

    const sectors = Array.isArray(
      payload.sectors
    )
      ? payload.sectors
      : [];

    if (!payload.samples || !sectors.length) {
      container.innerHTML =
        '<div class="atl-chart-empty">' +
        'No existen observaciones direccionales ' +
        'válidas para este periodo.</div>';
      return;
    }

    const width = 620;
    const height = 620;
    const cx = 310;
    const cy = 310;
    const innerRadius = 25;
    const maximumRadius = 235;

    const maxFrequency = Math.max(
      ...sectors.map(
        item => Number(item.frequency_pct) || 0
      ),
      1
    );

    const maxSpeed = Math.max(
      ...sectors.map(
        item => Number(item.speed_avg_ms) || 0
      ),
      1
    );

    const circles = [0.25, 0.5, 0.75, 1]
      .map(ratio => {
        const radius =
          innerRadius +
          (maximumRadius - innerRadius) * ratio;

        const label =
          format(maxFrequency * ratio, 1) + " %";

        return `
          <circle cx="${cx}" cy="${cy}"
                  r="${radius}"
                  fill="none"
                  stroke="#d8e5f1"
                  stroke-width="1"/>
          <text x="${cx + 5}"
                y="${cy - radius + 14}"
                font-size="11"
                fill="#71849b">${label}</text>
        `;
      })
      .join("");

    const axes = directions
      .map((direction, index) => {
        const angle = index * 22.5;
        const end = polar(
          cx,
          cy,
          maximumRadius + 10,
          angle
        );
        const label = polar(
          cx,
          cy,
          maximumRadius + 32,
          angle
        );

        return `
          <line x1="${cx}" y1="${cy}"
                x2="${end.x}" y2="${end.y}"
                stroke="#e5edf5"
                stroke-width="1"/>
          <text x="${label.x}"
                y="${label.y}"
                text-anchor="middle"
                dominant-baseline="middle"
                font-size="12"
                font-weight="700"
                fill="#284866">${direction}</text>
        `;
      })
      .join("");

    const petals = sectors
      .map((item, index) => {
        const frequency =
          Number(item.frequency_pct) || 0;

        const speed =
          Number(item.speed_avg_ms) || 0;

        const radius =
          innerRadius +
          (maximumRadius - innerRadius) *
          frequency / maxFrequency;

        const start = index * 22.5 - 10;
        const end = index * 22.5 + 10;

        const path = sectorPath(
          cx,
          cy,
          innerRadius,
          radius,
          start,
          end
        );

        const color = speedColor(
          speed,
          maxSpeed
        );

        return `
          <path d="${path}"
                fill="${color}"
                fill-opacity="0.78"
                stroke="#ffffff"
                stroke-width="1.5">
            <title>${item.sector}: ${format(
              frequency,
              2
            )} % · ${format(
              speed,
              2
            )} m/s · N=${item.count}</title>
          </path>
        `;
      })
      .join("");

    container.innerHTML = `
      <svg viewBox="0 0 ${width} ${height}"
           role="img"
           aria-label="Rosa de vientos">
        <circle cx="${cx}" cy="${cy}"
                r="${maximumRadius + 12}"
                fill="#fbfdff"
                stroke="#cdddeb"
                stroke-width="1.5"/>
        ${circles}
        ${axes}
        ${petals}
        <circle cx="${cx}" cy="${cy}"
                r="${innerRadius}"
                fill="#082f55"/>
        <text x="${cx}" y="${cy + 4}"
              text-anchor="middle"
              font-size="11"
              font-weight="700"
              fill="#ffffff">VIENTO</text>
      </svg>
    `;
  }

  function timeFromTimestamp(value) {
    if (!value || String(value).length < 16) {
      return "—";
    }

    return String(value).slice(11, 16);
  }

  function renderHourlyChart(payload) {
    const container =
      byId("windHourlyChart");

    const subtitle =
      byId("windHourlySubtitle");

    if (!container) {
      return;
    }

    const rows = Array.isArray(
      payload.hourly_summary
    )
      ? payload.hourly_summary
      : [];

    if (!payload.selected_date || !rows.length) {
      container.innerHTML =
        '<div class="atl-chart-empty">' +
        'Seleccione una fecha específica para ' +
        'visualizar la evolución horaria.</div>';

      if (subtitle) {
        subtitle.textContent =
          "La gráfica está disponible para días calendario.";
      }

      return;
    }

    if (subtitle) {
      subtitle.textContent =
        `Fecha: ${displayDate(
          payload.selected_date
        )} · medias, máximos y ráfagas por hora.`;
    }

    const width = 1180;
    const height = 390;
    const left = 64;
    const right = 24;
    const top = 28;
    const bottom = 58;
    const chartWidth = width - left - right;
    const chartHeight = height - top - bottom;

    const numericValues = rows.flatMap(
      row => [
        Number(row.speed_avg_ms),
        Number(row.speed_max_ms),
        Number(row.gust_max_ms)
      ].filter(Number.isFinite)
    );

    const maximum = Math.max(
      ...numericValues,
      1
    );

    const yMaximum =
      Math.ceil(maximum * 1.15 * 2) / 2;

    const x = index =>
      left +
      chartWidth * index /
      Math.max(rows.length - 1, 1);

    const y = value =>
      top +
      chartHeight *
      (1 - Number(value) / yMaximum);

    const horizontalGrid = [0, 0.25, 0.5, 0.75, 1]
      .map(ratio => {
        const value = yMaximum * ratio;
        const py = y(value);

        return `
          <line x1="${left}"
                y1="${py}"
                x2="${width - right}"
                y2="${py}"
                stroke="#dce7f1"
                stroke-width="1"/>
          <text x="${left - 10}"
                y="${py + 4}"
                text-anchor="end"
                font-size="12"
                fill="#60738c">
            ${format(value, 1)}
          </text>
        `;
      })
      .join("");

    const verticalGrid = rows
      .map((row, index) => {
        if (index % 3 !== 0) {
          return "";
        }

        const px = x(index);

        return `
          <line x1="${px}"
                y1="${top}"
                x2="${px}"
                y2="${height - bottom}"
                stroke="#edf2f7"
                stroke-width="1"/>
          <text x="${px}"
                y="${height - bottom + 24}"
                text-anchor="middle"
                font-size="12"
                fill="#60738c">
            ${row.hour}
          </text>
        `;
      })
      .join("");

    function points(field) {
      return rows
        .map((row, index) => {
          const value = Number(row[field]);

          return Number.isFinite(value)
            ? `${x(index)},${y(value)}`
            : null;
        })
        .filter(Boolean)
        .join(" ");
    }

    function markers(field, color, label) {
      return rows
        .map((row, index) => {
          const value = Number(row[field]);

          if (!Number.isFinite(value)) {
            return "";
          }

          return `
            <circle cx="${x(index)}"
                    cy="${y(value)}"
                    r="3.2"
                    fill="${color}"
                    stroke="#ffffff"
                    stroke-width="1">
              <title>
                ${row.hour} · ${label}: 
                ${format(value, 2)} m/s
              </title>
            </circle>
          `;
        })
        .join("");
    }

    container.innerHTML = `
      <svg viewBox="0 0 ${width} ${height}"
           role="img"
           aria-label="Evolución horaria del viento">
        <rect x="${left}"
              y="${top}"
              width="${chartWidth}"
              height="${chartHeight}"
              rx="10"
              fill="#ffffff"
              stroke="#d7e3ee"/>

        ${horizontalGrid}
        ${verticalGrid}

        <text x="18"
              y="${top + chartHeight / 2}"
              transform="rotate(-90 18 ${
                top + chartHeight / 2
              })"
              text-anchor="middle"
              font-size="12"
              font-weight="700"
              fill="#48647e">
          Velocidad (m/s)
        </text>

        <polyline
          points="${points("speed_avg_ms")}"
          fill="none"
          stroke="#1686c8"
          stroke-width="3"
          stroke-linejoin="round"
          stroke-linecap="round"/>

        <polyline
          points="${points("speed_max_ms")}"
          fill="none"
          stroke="#18a46b"
          stroke-width="2.5"
          stroke-linejoin="round"
          stroke-linecap="round"/>

        <polyline
          points="${points("gust_max_ms")}"
          fill="none"
          stroke="#e68222"
          stroke-width="2.5"
          stroke-linejoin="round"
          stroke-linecap="round"/>

        ${markers(
          "speed_avg_ms",
          "#1686c8",
          "Media"
        )}

        ${markers(
          "speed_max_ms",
          "#18a46b",
          "Máxima"
        )}

        ${markers(
          "gust_max_ms",
          "#e68222",
          "Ráfaga"
        )}
      </svg>
    `;
  }

  async function loadWindRose() {
    const period =
      byId("professionalWindRosePeriod")
        ?.value || "24h";

    const station = stationId();

    const selectedDate =
      byId("professionalWindRoseDate")
        ?.value || "";

    const status =
      byId("professionalWindRoseStatus");

    if (status) {
      status.textContent =
        "Cargando observaciones direccionales…";
    }

    try {
      const response = await fetch(
        "/api/windrose" +
        `?station_id=${encodeURIComponent(station)}` +
        `&period=${encodeURIComponent(period)}` +
        (
          period === "date" && selectedDate
            ? `&date=${encodeURIComponent(
                selectedDate
              )}`
            : ""
        ),
        {
          cache: "no-store",
          headers: {
            Accept: "application/json"
          }
        }
      );

      const payload = await response.json();

      if (!response.ok || payload.status === "error") {
        throw new Error(
          payload.error ||
          `HTTP ${response.status}`
        );
      }

      setText(
        "windRoseStation",
        station === "SJ01"
          ? "SJ01 · Cerro San José"
          : "CU01 · Cerro Cuñacales"
      );

      setText(
        "windRoseSelectedDate",
        payload.selected_date
          ? displayDate(payload.selected_date)
          : "Ventana móvil"
      );

      setText(
        "windRoseCoverage",
        payload.coverage_pct == null
          ? "No aplica"
          : `${format(
              payload.coverage_pct,
              2
            )} %`
      );

      setText(
        "windRoseSamples",
        payload.samples ?? 0
      );

      setText(
        "windRoseDominant",
        payload.dominant_sector ?? "—"
      );

      setText(
        "windRoseDominantFrequency",
        payload.dominant_frequency_pct == null
          ? "—"
          : `${format(
              payload.dominant_frequency_pct,
              2
            )} %`
      );

      setText(
        "windRoseAverage",
        payload.speed_avg_ms == null
          ? "—"
          : `${format(
              payload.speed_avg_ms,
              2
            )} m/s`
      );

      setText(
        "windRoseMaximum",
        payload.speed_max_ms == null
          ? "—"
          : `${format(
              payload.speed_max_ms,
              2
            )} m/s`
      );

      setText(
        "windRoseGust",
        payload.gust_max_ms == null
          ? "No disponible"
          : `${format(
              payload.gust_max_ms,
              2
            )} m/s`
      );

      setText(
        "windRoseMaximumTime",
        timeFromTimestamp(
          payload.speed_max_timestamp
        )
      );

      setText(
        "windRoseGustTime",
        timeFromTimestamp(
          payload.gust_max_timestamp
        )
      );

      setText(
        "windRoseCalm",
        payload.calm_frequency_pct == null
          ? "—"
          : `${format(
              payload.calm_frequency_pct,
              2
            )} %`
      );

      const interpretation =
        byId("windRoseInterpretation");

      if (payload.samples > 0) {
        if (status) {
          status.innerHTML =
            "<strong>Resultado:</strong> " +
            `${payload.samples} observaciones válidas. ` +
            `La dirección predominante es ` +
            `${payload.dominant_sector} ` +
            `con ${format(
              payload.dominant_frequency_pct,
              2
            )} % de frecuencia.`;
        }

        if (interpretation) {
          interpretation.textContent =
            "La longitud radial representa la frecuencia " +
            "del sector y el color representa su velocidad " +
            "media. La dirección indica la procedencia " +
            "meteorológica del viento.";
        }
      } else {
        if (status) {
          status.innerHTML =
            "<strong>Resultado:</strong> " +
            "No existen datos direccionales válidos " +
            "para el periodo seleccionado.";
        }

        if (interpretation) {
          interpretation.textContent =
            "La estación no dispone de muestras válidas " +
            "en este intervalo.";
        }
      }

      renderChart(payload);
      renderHourlyChart(payload);

    } catch (error) {
      if (status) {
        status.innerHTML =
          "<strong>Error:</strong> " +
          String(error.message || error);
      }

      const chart =
        byId("professionalWindRoseChart");

      if (chart) {
        chart.innerHTML =
          '<div class="atl-chart-empty">' +
          'No fue posible cargar la rosa de vientos.' +
          '</div>';
      }
    }
  }

  function initialize() {
    const periodSelect =
      byId("professionalWindRosePeriod");

    const dateInput =
      byId("professionalWindRoseDate");

    if (dateInput) {
      const today = new Date();
      const yesterday = new Date(today);

      yesterday.setDate(
        today.getDate() - 1
      );

      dateInput.max = localIsoDate(today);

      if (!dateInput.value) {
        dateInput.value =
          localIsoDate(yesterday);
      }

      dateInput.addEventListener(
        "change",
        loadWindRose
      );
    }

    periodSelect?.addEventListener(
      "change",
      () => {
        updateDateVisibility();
        loadWindRose();
      }
    );

    updateDateVisibility();

    byId("stationSelector")
      ?.addEventListener(
        "change",
        () => {
          window.setTimeout(
            loadWindRose,
            100
          );
        }
      );

    loadWindRose();

    window.setInterval(
      loadWindRose,
      60000
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      initialize
    );
  } else {
    initialize();
  }
})();
