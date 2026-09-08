(() => {
    "use strict";

    const REFRESH_MS = 60000;

    const scientificState = {
        CU01: {
            latest: null,
            scientific: null
        },
        SJ01: {
            latest: null,
            scientific: null
        }
    };


    function number(value) {
        if (
            value === null ||
            value === undefined ||
            value === ""
        ) {
            return null;
        }

        const n = Number(value);

        return Number.isFinite(n) ? n : null;
    }


    function normalizedKey(value) {
        return String(value || "")
            .toLowerCase()
            .replace(/[^a-z0-9]/g, "");
    }


    function objectBranch(root, aliases) {
        if (!root || typeof root !== "object") {
            return null;
        }

        const normalizedAliases =
            aliases.map(normalizedKey);

        const queue = [root];
        const visited = new Set();

        while (queue.length) {
            const current = queue.shift();

            if (
                !current ||
                typeof current !== "object" ||
                visited.has(current)
            ) {
                continue;
            }

            visited.add(current);

            for (
                const [key, value]
                of Object.entries(current)
            ) {
                const nk = normalizedKey(key);

                if (
                    normalizedAliases.some(
                        alias =>
                            nk === alias ||
                            nk.includes(alias)
                    ) &&
                    value &&
                    typeof value === "object"
                ) {
                    return value;
                }
            }

            for (const value of Object.values(current)) {
                if (
                    value &&
                    typeof value === "object"
                ) {
                    queue.push(value);
                }
            }
        }

        return null;
    }


    function findNumeric(root, aliases) {
        if (!root || typeof root !== "object") {
            return null;
        }

        const normalizedAliases =
            aliases.map(normalizedKey);

        const queue = [root];
        const visited = new Set();

        while (queue.length) {
            const current = queue.shift();

            if (
                !current ||
                typeof current !== "object" ||
                visited.has(current)
            ) {
                continue;
            }

            visited.add(current);

            for (
                const [key, value]
                of Object.entries(current)
            ) {
                const nk = normalizedKey(key);

                if (
                    normalizedAliases.some(
                        alias =>
                            nk === alias ||
                            nk.includes(alias)
                    )
                ) {
                    const n = number(value);

                    if (n !== null) {
                        return n;
                    }
                }
            }

            for (const value of Object.values(current)) {
                if (
                    value &&
                    typeof value === "object"
                ) {
                    queue.push(value);
                }
            }
        }

        return null;
    }


    function getModelBranch(
        latest,
        scientific,
        model
    ) {
        const aliases =
            model === "era5"
                ? [
                    "era5",
                    "era5land"
                ]
                : [
                    "nasa",
                    "nasapower",
                    "power"
                ];

        return (
            objectBranch(scientific, aliases) ||
            objectBranch(latest, aliases) ||
            (
                model === "era5"
                    ? latest?.era5
                    : latest?.nasa_power
            ) ||
            null
        );
    }


    const variables = [
        {
            id: "temp",
            label: "Temperatura",
            unit: "°C",
            local: ["temp_avg_C"],
            era5: [
                "temp_c",
                "temperature_c",
                "air_temperature_c",
                "t2m_c"
            ],
            nasa: [
                "temp_c",
                "temperature_c",
                "t2m",
                "t2m_c"
            ],
            threshold: [1.5, 3.0]
        },
        {
            id: "rh",
            label: "Humedad relativa",
            unit: "%",
            local: ["hum_avg_pct"],
            era5: [
                "rh_pct",
                "humidity_pct",
                "relative_humidity_pct"
            ],
            nasa: [
                "rh_pct",
                "humidity_pct",
                "relative_humidity_pct",
                "rh2m"
            ],
            threshold: [8, 15]
        },
        {
            id: "pressure",
            label: "Presión",
            unit: "hPa",
            local: ["pres_avg_hPa"],
            era5: [
                "press_hpa",
                "pressure_hpa",
                "pres_hpa",
                "surface_pressure_hpa"
            ],
            nasa: [
                "press_hpa",
                "pressure_hpa",
                "pres_hpa",
                "ps"
            ],
            threshold: [3, 7]
        },
        {
            id: "rain",
            label: "Precipitación",
            unit: "mm",
            local: [
                "rain_1h_mm",
                "rain_1min_mm"
            ],
            era5: [
                "precip_mm",
                "precipitation_mm",
                "rain_mm",
                "total_precipitation_mm"
            ],
            nasa: [
                "precip_mm",
                "precipitation_mm",
                "rain_mm",
                "prectotcorr"
            ],
            threshold: [1, 5]
        },
        {
            id: "wind",
            label: "Viento",
            unit: "m/s",
            local: ["wind_speed_ms"],
            era5: [
                "wind_ms",
                "wind_speed_ms",
                "wind10m_ms"
            ],
            nasa: [
                "wind10m_ms",
                "wind_ms",
                "wind_speed_ms",
                "ws10m"
            ],
            threshold: [1.5, 3]
        }
    ];


    function localValue(latest, aliases) {
        for (const key of aliases) {
            const n = number(latest?.[key]);

            if (n !== null) {
                return n;
            }
        }

        return null;
    }


    function modelValue(branch, aliases) {
        if (!branch) {
            return null;
        }

        return findNumeric(
            branch,
            aliases
        );
    }


    function formatValue(value, unit) {
        const n = number(value);

        if (n === null) {
            return `<span class="scientific-na">—</span>`;
        }

        const digits =
            unit === "hPa"
                ? 2
                : 2;

        return `${n.toFixed(digits)} ${unit}`;
    }


    function delta(model, observed) {
        const m = number(model);
        const o = number(observed);

        if (
            m === null ||
            o === null
        ) {
            return null;
        }

        return m - o;
    }


    function deltaClass(
        value,
        thresholds
    ) {
        if (value === null) {
            return "";
        }

        const abs = Math.abs(value);

        if (abs <= thresholds[0]) {
            return "good";
        }

        if (abs <= thresholds[1]) {
            return "medium";
        }

        return "high";
    }


    function formatDelta(
        value,
        unit,
        thresholds
    ) {
        if (value === null) {
            return `
                <span class="scientific-na">
                    —
                </span>
            `;
        }

        const sign =
            value > 0
                ? "+"
                : "";

        const css =
            deltaClass(
                value,
                thresholds
            );

        return `
            <span class="scientific-delta ${css}">
                ${sign}${value.toFixed(2)} ${unit}
            </span>
        `;
    }


    function sourceAvailable(branch) {
        if (!branch) {
            return false;
        }

        return variables.some(
            variable =>
                modelValue(
                    branch,
                    [
                        ...variable.era5,
                        ...variable.nasa
                    ]
                ) !== null
        );
    }


    function strictLocalValue(
        branch,
        variable
    ) {
        if (!branch || !variable) {
            return null;
        }

        const label =
            String(variable.label ?? "")
                .trim()
                .toLowerCase();

        const mapping = {
            "temperatura": "temperature_c",
            "humedad relativa": "humidity_pct",
            "presión": "pressure_hpa",
            "precipitación": "precipitation_mm",
            "viento": "wind_ms",
        };

        const key = mapping[label];

        if (!key) {
            return null;
        }

        const value = branch[key];

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


    /*
     * ============================================================
     * ATMOSLINK V4.2 — SCIENTIFIC SOURCE COMPARISON
     * ============================================================
     *
     * La comparación histórica se consume exclusivamente desde
     * /api/scientific/hourly. El frontend NO reconstruye ni
     * interpola coincidencias científicas.
     */

    const scientificChartSelection = {
        CU01: "temperature",
        SJ01: "temperature"
    };

    const scientificChartMode = {
        CU01: "timeseries",
        SJ01: "timeseries"
    };

    const scientificChartVariables = {
        temperature: {
            label: "Temperatura",
            unit: "°C"
        },
        humidity: {
            label: "Humedad relativa",
            unit: "%"
        },
        pressure: {
            label: "Presión atmosférica",
            unit: "hPa"
        },
        dewpoint: {
            label: "Punto de rocío",
            unit: "°C"
        },
        precipitation: {
            label: "Precipitación horaria",
            unit: "mm"
        },
        wind: {
            label: "Velocidad del viento",
            unit: "m/s"
        }
    };


    function scientificChartShell(stationId) {
        const selected =
            scientificChartSelection[stationId]
            ?? "temperature";

        const options = Object.entries(
            scientificChartVariables
        )
        .map(([key, definition]) => `
            <option
                value="${key}"
                ${key === selected ? "selected" : ""}
            >
                ${definition.label} · ${definition.unit}
            </option>
        `)
        .join("");

        return `
            <div
                class="scientific-history"
                id="scientific-history-${stationId.toLowerCase()}"
            >
                <div class="scientific-history-tabs">
                    <button
                        type="button"
                        class="scientific-history-tab active"
                        data-station="${stationId}"
                        data-mode="timeseries"
                    >
                        Serie temporal
                    </button>

                    <button
                        type="button"
                        class="scientific-history-tab"
                        data-station="${stationId}"
                        data-mode="delta"
                    >
                        Δ respecto al local
                    </button>

                    <button
                        type="button"
                        class="scientific-history-tab"
                        data-station="${stationId}"
                        data-mode="concordance"
                    >
                        Concordancia
                    </button>

                    <button
                        type="button"
                        class="scientific-history-tab"
                        data-station="${stationId}"
                        data-mode="summary"
                    >
                        Resumen
                    </button>
                </div>

                <div class="scientific-history-header">
                    <div>
                        <div class="scientific-history-eyebrow">
                            SERIE TEMPORAL VALIDADA
                        </div>

                        <strong>
                            Local · ERA5-Land · NASA POWER
                        </strong>
                    </div>

                    <select
                        class="scientific-history-select"
                        id="scientific-history-select-${stationId.toLowerCase()}"
                        aria-label="Variable científica ${stationId}"
                    >
                        ${options}
                    </select>
                </div>

                <div
                    class="scientific-history-summary"
                    id="scientific-history-summary-${stationId.toLowerCase()}"
                >
                    Cargando serie científica…
                </div>

                <div class="scientific-history-chart-wrap">
                    <svg
                        class="scientific-history-chart"
                        id="scientific-history-chart-${stationId.toLowerCase()}"
                        viewBox="0 0 900 330"
                        preserveAspectRatio="none"
                        role="img"
                        aria-label="Comparación temporal ${stationId}"
                    ></svg>
                </div>

                <div
                    class="scientific-history-legend"
                    id="scientific-history-legend-${stationId.toLowerCase()}"
                >
                    <span class="scientific-history-legend-item">
                        <i class="scientific-history-key local"></i>
                        Sensor local
                    </span>

                    <span class="scientific-history-legend-item">
                        <i class="scientific-history-key era5"></i>
                        ERA5-Land
                    </span>

                    <span class="scientific-history-legend-item">
                        <i class="scientific-history-key nasa"></i>
                        NASA POWER
                    </span>
                </div>

                <div class="scientific-history-note">
                    Los huecos representan ausencia real de una
                    fuente. No se interpolan ni se prolongan datos.
                    Hora mostrada: local UTC−5.
                </div>
            </div>
        `;
    }


    function scientificDate(value) {
        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return null;
        }

        return date;
    }


    function scientificLocalTime(value) {
        const date = scientificDate(value);

        if (!date) {
            return "—";
        }

        return new Intl.DateTimeFormat(
            "es-PE",
            {
                timeZone: "America/Lima",
                day: "2-digit",
                month: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false
            }
        ).format(date);
    }


    function scientificNumber(value) {
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


    function scientificSvgElement(name, attrs = {}) {
        const node =
            document.createElementNS(
                "http://www.w3.org/2000/svg",
                name
            );

        for (const [key, value] of Object.entries(attrs)) {
            node.setAttribute(key, String(value));
        }

        return node;
    }


    function scientificDrawDelta(
        stationId,
        payload
    ) {
        const svg =
            document.getElementById(
                `scientific-history-chart-${stationId.toLowerCase()}`
            );

        const summary =
            document.getElementById(
                `scientific-history-summary-${stationId.toLowerCase()}`
            );

        if (!svg || !summary) {
            return;
        }

        svg.innerHTML = "";

        const allRecords =
            Array.isArray(payload?.records)
                ? payload.records
                : [];

        let lastComparableIndex = -1;

        for (
            let i = allRecords.length - 1;
            i >= 0;
            i--
        ) {
            const record = allRecords[i];

            if (
                scientificNumber(record?.era5) !== null ||
                scientificNumber(record?.nasa) !== null
            ) {
                lastComparableIndex = i;
                break;
            }
        }

        const records =
            lastComparableIndex >= 0
                ? allRecords.slice(
                    Math.max(0, lastComparableIndex - 167),
                    lastComparableIndex + 1
                )
                : allRecords.slice(-168);

        const variableKey =
            scientificChartSelection[stationId]
            ?? "temperature";

        const variable =
            scientificChartVariables[variableKey]
            ?? scientificChartVariables.temperature;

        const parsed = records
            .map(record => {
                const timestamp =
                    scientificDate(record.timestamp);

                const observed =
                    scientificNumber(record.observed);

                const era5 =
                    scientificNumber(record.era5);

                const nasa =
                    scientificNumber(record.nasa);

                return {
                    timestamp,
                    deltaEra5:
                        observed !== null &&
                        era5 !== null
                            ? era5 - observed
                            : null,
                    deltaNasa:
                        observed !== null &&
                        nasa !== null
                            ? nasa - observed
                            : null
                };
            })
            .filter(record => record.timestamp);

        const era5Count =
            parsed.filter(
                r => r.deltaEra5 !== null
            ).length;

        const nasaCount =
            parsed.filter(
                r => r.deltaNasa !== null
            ).length;

        const legend =
            document.getElementById(
                `scientific-history-legend-${stationId.toLowerCase()}`
            );

        if (legend) {
            legend.innerHTML = `
                <span class="scientific-history-legend-item">
                    <i class="scientific-history-key era5"></i>
                    Δ ERA5-Land
                </span>

                <span class="scientific-history-legend-item">
                    <i class="scientific-history-key nasa"></i>
                    Δ NASA POWER
                </span>

                <span class="scientific-history-legend-item">
                    <i class="scientific-history-key zero"></i>
                    Δ = 0
                </span>
            `;
        }

        summary.innerHTML = `
            <strong>Diferencia respecto a observación local</strong>
            · ${payload?.label ?? variable.label}
            · Ventana mostrada: ERA5 ${era5Count} pares
            · NASA ${nasaCount} pares
            · Δ = referencia − local
        `;

        const numericValues = [];

        for (const record of parsed) {
            if (record.deltaEra5 !== null) {
                numericValues.push(record.deltaEra5);
            }

            if (record.deltaNasa !== null) {
                numericValues.push(record.deltaNasa);
            }
        }

        if (!numericValues.length) {
            const text =
                scientificSvgElement(
                    "text",
                    {
                        x: 450,
                        y: 165,
                        "text-anchor": "middle",
                        class: "scientific-chart-empty"
                    }
                );

            text.textContent =
                "Sin pares comparables para Δ";

            svg.appendChild(text);
            return;
        }

        const W = 900;
        const H = 330;

        const margin = {
            left: 72,
            right: 24,
            top: 20,
            bottom: 58
        };

        const chartWidth =
            W - margin.left - margin.right;

        const chartHeight =
            H - margin.top - margin.bottom;

        let minY =
            Math.min(
                ...numericValues,
                0
            );

        let maxY =
            Math.max(
                ...numericValues,
                0
            );

        if (minY === maxY) {
            minY -= 1;
            maxY += 1;
        }

        const padding =
            Math.max(
                (maxY - minY) * 0.08,
                0.1
            );

        minY -= padding;
        maxY += padding;

        const minTime =
            parsed[0].timestamp.getTime();

        let maxTime =
            parsed[
                parsed.length - 1
            ].timestamp.getTime();

        if (minTime === maxTime) {
            maxTime += 3600000;
        }

        const xScale = time =>
            margin.left +
            (
                (
                    time.getTime() - minTime
                ) /
                (
                    maxTime - minTime
                )
            ) * chartWidth;

        const yScale = value =>
            margin.top +
            (
                1 -
                (
                    (value - minY) /
                    (maxY - minY)
                )
            ) * chartHeight;

        for (let i = 0; i <= 4; i++) {
            const ratio = i / 4;

            const y =
                margin.top +
                ratio * chartHeight;

            const value =
                maxY -
                ratio * (maxY - minY);

            svg.appendChild(
                scientificSvgElement(
                    "line",
                    {
                        x1: margin.left,
                        x2: W - margin.right,
                        y1: y,
                        y2: y,
                        class: "scientific-chart-grid"
                    }
                )
            );

            const label =
                scientificSvgElement(
                    "text",
                    {
                        x: margin.left - 12,
                        y: y + 4,
                        "text-anchor": "end",
                        class: "scientific-chart-axis-label"
                    }
                );

            label.textContent =
                value.toFixed(
                    Math.abs(maxY - minY) < 10
                        ? 1
                        : 0
                );

            svg.appendChild(label);
        }

        const zeroY = yScale(0);

        svg.appendChild(
            scientificSvgElement(
                "line",
                {
                    x1: margin.left,
                    x2: W - margin.right,
                    y1: zeroY,
                    y2: zeroY,
                    class: "scientific-delta-zero"
                }
            )
        );

        const tickCount =
            Math.min(
                5,
                Math.max(
                    2,
                    parsed.length
                )
            );

        for (let i = 0; i < tickCount; i++) {
            const index =
                Math.round(
                    i *
                    (parsed.length - 1) /
                    (tickCount - 1)
                );

            const record =
                parsed[index];

            const x =
                xScale(record.timestamp);

            const label =
                scientificSvgElement(
                    "text",
                    {
                        x,
                        y: H - 28,
                        "text-anchor": "middle",
                        class: "scientific-chart-axis-label"
                    }
                );

            label.textContent =
                scientificLocalTime(
                    record.timestamp
                );

            svg.appendChild(label);
        }

        const unitLabel =
            scientificSvgElement(
                "text",
                {
                    x: 14,
                    y: margin.top + chartHeight / 2,
                    transform:
                        `rotate(-90 14 ${
                            margin.top +
                            chartHeight / 2
                        })`,
                    "text-anchor": "middle",
                    class: "scientific-chart-unit"
                }
            );

        unitLabel.textContent =
            `Δ ${variable.unit}`;

        svg.appendChild(unitLabel);

        function drawSeries(
            key,
            cssClass
        ) {
            let segment = [];

            function flush() {
                if (segment.length === 1) {
                    const p = segment[0];

                    svg.appendChild(
                        scientificSvgElement(
                            "circle",
                            {
                                cx: p.x,
                                cy: p.y,
                                r: 2.7,
                                class:
                                    `scientific-chart-point ${cssClass}`
                            }
                        )
                    );
                }

                if (segment.length >= 2) {
                    const points =
                        segment
                            .map(
                                p =>
                                    `${p.x},${p.y}`
                            )
                            .join(" ");

                    svg.appendChild(
                        scientificSvgElement(
                            "polyline",
                            {
                                points,
                                fill: "none",
                                class:
                                    `scientific-chart-line ${cssClass}`
                            }
                        )
                    );
                }

                segment = [];
            }

            for (const record of parsed) {
                const value =
                    record[key];

                if (value === null) {
                    flush();
                    continue;
                }

                segment.push({
                    x: xScale(
                        record.timestamp
                    ),
                    y: yScale(value)
                });
            }

            flush();
        }

        drawSeries(
            "deltaEra5",
            "scientific-series-era5"
        );

        drawSeries(
            "deltaNasa",
            "scientific-series-nasa"
        );

        const hoverLine =
            scientificSvgElement(
                "line",
                {
                    y1: margin.top,
                    y2: margin.top + chartHeight,
                    class: "scientific-history-hover-line"
                }
            );

        hoverLine.style.display = "none";
        svg.appendChild(hoverLine);

        const hoverBox =
            scientificSvgElement(
                "g",
                {
                    class: "scientific-history-tooltip"
                }
            );

        hoverBox.style.display = "none";

        const tooltipBg =
            scientificSvgElement(
                "rect",
                {
                    width: 205,
                    height: 66,
                    rx: 7,
                    class: "scientific-history-tooltip-bg"
                }
            );

        const tooltipText =
            scientificSvgElement(
                "text",
                {
                    x: 10,
                    y: 18,
                    class: "scientific-history-tooltip-text"
                }
            );

        hoverBox.appendChild(tooltipBg);
        hoverBox.appendChild(tooltipText);
        svg.appendChild(hoverBox);

        const overlay =
            scientificSvgElement(
                "rect",
                {
                    x: margin.left,
                    y: margin.top,
                    width: chartWidth,
                    height: chartHeight,
                    class: "scientific-history-overlay"
                }
            );

        overlay.addEventListener(
            "mousemove",
            event => {
                const rect =
                    svg.getBoundingClientRect();

                const mouseX =
                    (
                        event.clientX -
                        rect.left
                    ) *
                    (
                        W / rect.width
                    );

                let nearest =
                    parsed[0];

                let nearestDistance =
                    Infinity;

                for (const record of parsed) {
                    const distance =
                        Math.abs(
                            xScale(
                                record.timestamp
                            ) -
                            mouseX
                        );

                    if (
                        distance <
                        nearestDistance
                    ) {
                        nearestDistance =
                            distance;

                        nearest = record;
                    }
                }

                const x =
                    xScale(
                        nearest.timestamp
                    );

                hoverLine.setAttribute(
                    "x1",
                    x
                );

                hoverLine.setAttribute(
                    "x2",
                    x
                );

                hoverLine.style.display = "";

                const lines = [
                    scientificLocalTime(
                        nearest.timestamp
                    ),
                    `Δ ERA5: ${
                        nearest.deltaEra5 === null
                            ? "—"
                            : nearest.deltaEra5.toFixed(2)
                    } ${variable.unit}`,
                    `Δ NASA: ${
                        nearest.deltaNasa === null
                            ? "—"
                            : nearest.deltaNasa.toFixed(2)
                    } ${variable.unit}`
                ];

                tooltipText.innerHTML = "";

                lines.forEach(
                    (line, index) => {
                        const tspan =
                            scientificSvgElement(
                                "tspan",
                                {
                                    x: 10,
                                    dy:
                                        index === 0
                                            ? 0
                                            : 18
                                }
                            );

                        tspan.textContent =
                            line;

                        tooltipText.appendChild(
                            tspan
                        );
                    }
                );

                const tooltipX =
                    x > W - 235
                        ? x - 215
                        : x + 10;

                hoverBox.setAttribute(
                    "transform",
                    `translate(${tooltipX},${margin.top + 8})`
                );

                hoverBox.style.display = "";
            }
        );

        overlay.addEventListener(
            "mouseleave",
            () => {
                hoverLine.style.display =
                    "none";

                hoverBox.style.display =
                    "none";
            }
        );

        svg.appendChild(overlay);
    }



    function scientificSampleMaturity(n) {
        /*
         * Política operativa AtmosLink.
         *
         * Estos umbrales NO constituyen una norma estadística
         * universal. Se utilizan como indicador de madurez
         * descriptiva del conjunto disponible.
         */
        if (n < 10) {
            return {
                key: "insufficient",
                label: "INSUFICIENTE",
                description:
                    "Muestra demasiado pequeña para interpretar métricas de asociación."
            };
        }

        if (n < 30) {
            return {
                key: "preliminary",
                label: "PRELIMINAR",
                description:
                    "Resultados descriptivos preliminares."
            };
        }

        if (n < 100) {
            return {
                key: "moderate",
                label: "MODERADA",
                description:
                    "Muestra con utilidad descriptiva moderada."
            };
        }

        return {
            key: "robust",
            label: "ROBUSTA DESCRIPTIVAMENTE",
            description:
                "Muestra amplia para análisis descriptivo."
        };
    }


    function scientificMetrics(pairs) {
        const valid =
            Array.isArray(pairs)
                ? pairs.filter(
                    pair =>
                        Number.isFinite(pair?.observed) &&
                        Number.isFinite(pair?.reference)
                )
                : [];

        const n = valid.length;

        const maturity =
            scientificSampleMaturity(n);

        if (!n) {
            return {
                n: 0,
                bias: null,
                mae: null,
                rmse: null,
                r2: null,
                nse: null,
                maturity
            };
        }

        const errors =
            valid.map(
                pair =>
                    pair.reference -
                    pair.observed
            );

        const bias =
            errors.reduce(
                (a, b) => a + b,
                0
            ) / n;

        const mae =
            errors.reduce(
                (a, b) =>
                    a + Math.abs(b),
                0
            ) / n;

        const mse =
            errors.reduce(
                (a, b) =>
                    a + b * b,
                0
            ) / n;

        const rmse =
            Math.sqrt(mse);

        const observedMean =
            valid.reduce(
                (a, pair) =>
                    a + pair.observed,
                0
            ) / n;

        const referenceMean =
            valid.reduce(
                (a, pair) =>
                    a + pair.reference,
                0
            ) / n;

        /*
         * r² de Pearson:
         * cuadrado del coeficiente de correlación lineal.
         */
        let covariance = 0;
        let varianceObserved = 0;
        let varianceReference = 0;

        for (const pair of valid) {
            const dx =
                pair.observed -
                observedMean;

            const dy =
                pair.reference -
                referenceMean;

            covariance += dx * dy;
            varianceObserved += dx * dx;
            varianceReference += dy * dy;
        }

        let r2 = null;

        if (
            n >= 2 &&
            varianceObserved > 0 &&
            varianceReference > 0
        ) {
            const r =
                covariance /
                Math.sqrt(
                    varianceObserved *
                    varianceReference
                );

            r2 = r * r;
        }

        /*
         * NSE — Nash-Sutcliffe Efficiency.
         *
         * Esta era la expresión que anteriormente estaba
         * etiquetada incorrectamente como R².
         */
        const ssRes =
            valid.reduce(
                (a, pair) => {
                    const d =
                        pair.observed -
                        pair.reference;

                    return a + d * d;
                },
                0
            );

        const ssTot =
            valid.reduce(
                (a, pair) => {
                    const d =
                        pair.observed -
                        observedMean;

                    return a + d * d;
                },
                0
            );

        const nse =
            ssTot > 0
                ? 1 - ssRes / ssTot
                : null;

        return {
            n,
            bias,
            mae,
            rmse,
            r2,
            nse,
            maturity
        };
    }


    function scientificMetricValue(
        value,
        digits = 2
    ) {
        return Number.isFinite(value)
            ? value.toFixed(digits)
            : "—";
    }


    function scientificMetricsHTML(
        variable,
        era5Metrics,
        nasaMetrics
    ) {
        function associationValue(
            metric,
            value
        ) {
            /*
             * Con N < 10 evitamos presentar r²/NSE como
             * indicadores interpretables.
             */
            if (
                metric.n < 10 ||
                !Number.isFinite(value)
            ) {
                return "—";
            }

            return value.toFixed(3);
        }

        function card(
            source,
            metric
        ) {
            return `
                <div class="scientific-metrics-card">

                    <div class="scientific-metrics-card-head">
                        <strong>${source}</strong>

                        <span class="
                            scientific-maturity-badge
                            ${metric.maturity.key}
                        ">
                            ${metric.maturity.label}
                        </span>
                    </div>

                    <span>
                        N
                        <b>${metric.n}</b>
                    </span>

                    <span>
                        Bias
                        <b>
                            ${scientificMetricValue(
                                metric.bias
                            )} ${variable.unit}
                        </b>
                    </span>

                    <span>
                        MAE
                        <b>
                            ${scientificMetricValue(
                                metric.mae
                            )} ${variable.unit}
                        </b>
                    </span>

                    <span>
                        RMSE
                        <b>
                            ${scientificMetricValue(
                                metric.rmse
                            )} ${variable.unit}
                        </b>
                    </span>

                    <span>
                        r²
                        <b>
                            ${associationValue(
                                metric,
                                metric.r2
                            )}
                        </b>
                    </span>

                    <span>
                        NSE
                        <b>
                            ${associationValue(
                                metric,
                                metric.nse
                            )}
                        </b>
                    </span>

                    <small class="scientific-maturity-detail">
                        ${metric.maturity.description}
                    </small>

                </div>
            `;
        }

        return `
            <div class="scientific-metrics-panel">

                <div class="scientific-metrics-header">
                    MÉTRICAS SOBRE PARES COMPARABLES
                </div>

                <div class="scientific-metrics-grid">
                    ${card(
                        "ERA5-Land",
                        era5Metrics
                    )}

                    ${card(
                        "NASA POWER",
                        nasaMetrics
                    )}
                </div>

                <div class="scientific-metrics-note">
                    Bias = media(referencia − local).
                    MAE y RMSE cuantifican magnitud de diferencia.
                    r² representa asociación lineal.
                    NSE evalúa reproducción respecto a la variabilidad
                    observada. Para N &lt; 10, r² y NSE se ocultan
                    como indicadores interpretables.
                    La clasificación de madurez es una política
                    operativa AtmosLink y no una norma estadística
                    universal.
                </div>

            </div>
        `;
    }


    function scientificFullPairs(
        payload,
        sourceKey
    ) {
        const records =
            Array.isArray(payload?.records)
                ? payload.records
                : [];

        const pairs = [];

        for (const record of records) {

            const observed =
                scientificNumber(
                    record?.observed
                );

            const reference =
                scientificNumber(
                    record?.[sourceKey]
                );

            if (
                observed === null ||
                reference === null
            ) {
                continue;
            }

            pairs.push({
                observed,
                reference
            });
        }

        return pairs;
    }


    function scientificSummaryMetric(
        metric,
        key,
        digits = 2
    ) {
        if (
            metric?.n < 10 &&
            ["r2", "nse"].includes(key)
        ) {
            return "—";
        }

        const value =
            metric?.[key];

        return Number.isFinite(value)
            ? value.toFixed(digits)
            : "—";
    }


    function scientificDrawSummary(
        stationId,
        datasets
    ) {
        const svg =
            document.getElementById(
                `scientific-history-chart-${stationId.toLowerCase()}`
            );

        const summary =
            document.getElementById(
                `scientific-history-summary-${stationId.toLowerCase()}`
            );

        const legend =
            document.getElementById(
                `scientific-history-legend-${stationId.toLowerCase()}`
            );

        if (!svg || !summary) {
            return;
        }

        /*
         * En modo Resumen no utilizamos el SVG como gráfica.
         * Insertamos una matriz HTML dentro del mismo contenedor.
         */
        const wrap =
            svg.parentElement;

        if (!wrap) {
            return;
        }

        svg.style.display = "none";

        let matrix =
            wrap.querySelector(
                ".scientific-summary-matrix"
            );

        if (!matrix) {
            matrix =
                document.createElement(
                    "div"
                );

            matrix.className =
                "scientific-summary-matrix";

            wrap.appendChild(
                matrix
            );
        }

        if (legend) {
            legend.innerHTML = `
                <span class="scientific-history-legend-item">
                    Resumen estadístico por variable y fuente
                </span>
            `;
        }

        summary.innerHTML = `
            <strong>Resumen científico multivariable</strong>
            · dataset comparable completo disponible
            · métricas calculadas exclusivamente sobre pares válidos
        `;

        const variableOrder = [
            "temperature",
            "humidity",
            "pressure",
            "dewpoint",
            "precipitation",
            "wind"
        ];

        const rows = [];

        for (const variableKey of variableOrder) {

            const payload =
                datasets?.[variableKey];

            if (!payload) {
                continue;
            }

            const definition =
                scientificChartVariables[
                    variableKey
                ];

            const era5Pairs =
                scientificFullPairs(
                    payload,
                    "era5"
                );

            const nasaPairs =
                scientificFullPairs(
                    payload,
                    "nasa"
                );

            const era5 =
                scientificMetrics(
                    era5Pairs
                );

            const nasa =
                scientificMetrics(
                    nasaPairs
                );

            rows.push(`
                <tr>
                    <td rowspan="2" class="scientific-summary-variable">
                        <strong>
                            ${definition?.label ?? payload?.label ?? variableKey}
                        </strong>
                        <small>
                            ${definition?.unit ?? ""}
                        </small>
                    </td>

                    <td>ERA5-Land</td>
                    <td>${era5.n}</td>

                    <td>
                        ${scientificSummaryMetric(
                            era5,
                            "bias"
                        )}
                    </td>

                    <td>
                        ${scientificSummaryMetric(
                            era5,
                            "mae"
                        )}
                    </td>

                    <td>
                        ${scientificSummaryMetric(
                            era5,
                            "rmse"
                        )}
                    </td>

                    <td>
                        ${scientificSummaryMetric(
                            era5,
                            "r2",
                            3
                        )}
                    </td>

                    <td>
                        ${scientificSummaryMetric(
                            era5,
                            "nse",
                            3
                        )}
                    </td>

                    <td>
                        <span class="
                            scientific-maturity-badge
                            ${era5.maturity.key}
                        ">
                            ${era5.maturity.label}
                        </span>
                    </td>
                </tr>

                <tr>
                    <td>NASA POWER</td>
                    <td>${nasa.n}</td>

                    <td>
                        ${scientificSummaryMetric(
                            nasa,
                            "bias"
                        )}
                    </td>

                    <td>
                        ${scientificSummaryMetric(
                            nasa,
                            "mae"
                        )}
                    </td>

                    <td>
                        ${scientificSummaryMetric(
                            nasa,
                            "rmse"
                        )}
                    </td>

                    <td>
                        ${scientificSummaryMetric(
                            nasa,
                            "r2",
                            3
                        )}
                    </td>

                    <td>
                        ${scientificSummaryMetric(
                            nasa,
                            "nse",
                            3
                        )}
                    </td>

                    <td>
                        <span class="
                            scientific-maturity-badge
                            ${nasa.maturity.key}
                        ">
                            ${nasa.maturity.label}
                        </span>
                    </td>
                </tr>
            `);
        }

        matrix.innerHTML = `
            <div class="scientific-summary-heading">
                MATRIZ CIENTÍFICA · ${stationId}
            </div>

            <div class="scientific-summary-table-wrap">
                <table class="scientific-summary-table">

                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th>Fuente</th>
                            <th>N</th>
                            <th>Bias</th>
                            <th>MAE</th>
                            <th>RMSE</th>
                            <th>r²</th>
                            <th>NSE</th>
                            <th>Madurez</th>
                        </tr>
                    </thead>

                    <tbody>
                        ${rows.join("")}
                    </tbody>

                </table>
            </div>

            <div class="scientific-summary-note">
                Bias = referencia − observación local.
                MAE y RMSE expresan magnitud de diferencia.
                r² representa asociación lineal.
                NSE evalúa reproducción respecto a la variabilidad observada.
                Para N &lt; 10, r² y NSE no se presentan como
                indicadores interpretables.
                Cada variable utiliza todos sus pares válidos disponibles.
            </div>
        `;
    }


    function scientificRestoreChart(
        stationId
    ) {
        const svg =
            document.getElementById(
                `scientific-history-chart-${stationId.toLowerCase()}`
            );

        if (!svg) {
            return;
        }

        svg.style.display = "";

        const wrap =
            svg.parentElement;

        const matrix =
            wrap?.querySelector(
                ".scientific-summary-matrix"
            );

        if (matrix) {
            matrix.remove();
        }
    }



    function scientificDrawConcordance(
        stationId,
        payload
    ) {
        const svg =
            document.getElementById(
                `scientific-history-chart-${stationId.toLowerCase()}`
            );

        const summary =
            document.getElementById(
                `scientific-history-summary-${stationId.toLowerCase()}`
            );

        const legend =
            document.getElementById(
                `scientific-history-legend-${stationId.toLowerCase()}`
            );

        if (!svg || !summary) {
            return;
        }

        svg.innerHTML = "";

        const allRecords =
            Array.isArray(payload?.records)
                ? payload.records
                : [];

        /*
         * Igual que en las otras vistas:
         * anclar la ventana al último registro donde exista
         * al menos una referencia externa.
         */
        let lastComparableIndex = -1;

        for (
            let i = allRecords.length - 1;
            i >= 0;
            i--
        ) {
            const record = allRecords[i];

            if (
                scientificNumber(record?.era5) !== null ||
                scientificNumber(record?.nasa) !== null
            ) {
                lastComparableIndex = i;
                break;
            }
        }

        const records =
            lastComparableIndex >= 0
                ? allRecords.slice(
                    Math.max(
                        0,
                        lastComparableIndex - 167
                    ),
                    lastComparableIndex + 1
                )
                : allRecords.slice(-168);

        const variableKey =
            scientificChartSelection[stationId]
            ?? "temperature";

        const variable =
            scientificChartVariables[variableKey]
            ?? scientificChartVariables.temperature;

        const era5Pairs = [];
        const nasaPairs = [];

        for (const record of records) {

            const timestamp =
                scientificDate(
                    record.timestamp
                );

            const observed =
                scientificNumber(
                    record.observed
                );

            const era5 =
                scientificNumber(
                    record.era5
                );

            const nasa =
                scientificNumber(
                    record.nasa
                );

            if (
                timestamp &&
                observed !== null &&
                era5 !== null
            ) {
                era5Pairs.push({
                    timestamp,
                    observed,
                    reference: era5,
                    source: "ERA5-Land"
                });
            }

            if (
                timestamp &&
                observed !== null &&
                nasa !== null
            ) {
                nasaPairs.push({
                    timestamp,
                    observed,
                    reference: nasa,
                    source: "NASA POWER"
                });
            }
        }

        const era5Metrics =
            scientificMetrics(
                era5Pairs
            );

        const nasaMetrics =
            scientificMetrics(
                nasaPairs
            );

        summary.innerHTML = `
            <strong>Concordancia con observación local</strong>
            · ${payload?.label ?? variable.label}
            · Ventana mostrada:
            ERA5 ${era5Pairs.length} pares
            · NASA ${nasaPairs.length} pares

            ${scientificMetricsHTML(
                variable,
                era5Metrics,
                nasaMetrics
            )}
        `;

        if (legend) {
            legend.innerHTML = `
                <span class="scientific-history-legend-item">
                    <i class="scientific-concordance-dot era5"></i>
                    ERA5-Land
                </span>

                <span class="scientific-history-legend-item">
                    <i class="scientific-concordance-dot nasa"></i>
                    NASA POWER
                </span>

                <span class="scientific-history-legend-item">
                    <i class="scientific-history-key identity"></i>
                    y = x
                </span>
            `;
        }

        const allPairs = [
            ...era5Pairs,
            ...nasaPairs
        ];

        if (!allPairs.length) {

            const text =
                scientificSvgElement(
                    "text",
                    {
                        x: 450,
                        y: 165,
                        "text-anchor": "middle",
                        class: "scientific-chart-empty"
                    }
                );

            text.textContent =
                "Sin pares comparables para concordancia";

            svg.appendChild(text);

            return;
        }

        /*
         * Una única escala común X/Y.
         *
         * Esto es imprescindible para que la diagonal y=x
         * tenga interpretación geométrica correcta.
         */
        const values = [];

        for (const pair of allPairs) {
            values.push(
                pair.observed,
                pair.reference
            );
        }

        let minValue =
            Math.min(...values);

        let maxValue =
            Math.max(...values);

        if (minValue === maxValue) {
            minValue -= 1;
            maxValue += 1;
        }

        const padding =
            Math.max(
                (maxValue - minValue) * 0.08,
                0.1
            );

        minValue -= padding;
        maxValue += padding;

        const W = 900;
        const H = 330;

        const margin = {
            left: 74,
            right: 28,
            top: 20,
            bottom: 62
        };

        const chartWidth =
            W - margin.left - margin.right;

        const chartHeight =
            H - margin.top - margin.bottom;

        const xScale = value =>
            margin.left +
            (
                (value - minValue) /
                (maxValue - minValue)
            ) * chartWidth;

        const yScale = value =>
            margin.top +
            (
                1 -
                (
                    (value - minValue) /
                    (maxValue - minValue)
                )
            ) * chartHeight;

        /*
         * Grid común.
         */
        for (let i = 0; i <= 4; i++) {

            const ratio =
                i / 4;

            const value =
                minValue +
                ratio *
                (maxValue - minValue);

            const x =
                xScale(value);

            const y =
                yScale(value);

            svg.appendChild(
                scientificSvgElement(
                    "line",
                    {
                        x1: x,
                        x2: x,
                        y1: margin.top,
                        y2:
                            margin.top +
                            chartHeight,
                        class:
                            "scientific-chart-grid"
                    }
                )
            );

            svg.appendChild(
                scientificSvgElement(
                    "line",
                    {
                        x1: margin.left,
                        x2:
                            margin.left +
                            chartWidth,
                        y1: y,
                        y2: y,
                        class:
                            "scientific-chart-grid"
                    }
                )
            );

            const xLabel =
                scientificSvgElement(
                    "text",
                    {
                        x,
                        y: H - 32,
                        "text-anchor": "middle",
                        class:
                            "scientific-chart-axis-label"
                    }
                );

            xLabel.textContent =
                value.toFixed(
                    Math.abs(
                        maxValue -
                        minValue
                    ) < 10
                        ? 1
                        : 0
                );

            svg.appendChild(xLabel);

            const yLabel =
                scientificSvgElement(
                    "text",
                    {
                        x:
                            margin.left -
                            12,
                        y: y + 4,
                        "text-anchor": "end",
                        class:
                            "scientific-chart-axis-label"
                    }
                );

            yLabel.textContent =
                value.toFixed(
                    Math.abs(
                        maxValue -
                        minValue
                    ) < 10
                        ? 1
                        : 0
                );

            svg.appendChild(yLabel);
        }

        /*
         * Diagonal ideal y=x.
         */
        svg.appendChild(
            scientificSvgElement(
                "line",
                {
                    x1:
                        xScale(minValue),
                    y1:
                        yScale(minValue),
                    x2:
                        xScale(maxValue),
                    y2:
                        yScale(maxValue),
                    class:
                        "scientific-concordance-identity"
                }
            )
        );

        /*
         * Títulos de ejes.
         */
        const xTitle =
            scientificSvgElement(
                "text",
                {
                    x:
                        margin.left +
                        chartWidth / 2,
                    y: H - 8,
                    "text-anchor": "middle",
                    class:
                        "scientific-chart-unit"
                }
            );

        xTitle.textContent =
            `Observación local (${variable.unit})`;

        svg.appendChild(xTitle);

        const yTitle =
            scientificSvgElement(
                "text",
                {
                    x: 15,
                    y:
                        margin.top +
                        chartHeight / 2,
                    transform:
                        `rotate(-90 15 ${
                            margin.top +
                            chartHeight / 2
                        })`,
                    "text-anchor": "middle",
                    class:
                        "scientific-chart-unit"
                }
            );

        yTitle.textContent =
            `Referencia (${variable.unit})`;

        svg.appendChild(yTitle);

        /*
         * Tooltip.
         */
        const tooltip =
            scientificSvgElement(
                "g",
                {
                    class:
                        "scientific-history-tooltip"
                }
            );

        tooltip.style.display =
            "none";

        const tooltipBg =
            scientificSvgElement(
                "rect",
                {
                    width: 225,
                    height: 84,
                    rx: 7,
                    class:
                        "scientific-history-tooltip-bg"
                }
            );

        const tooltipText =
            scientificSvgElement(
                "text",
                {
                    x: 10,
                    y: 18,
                    class:
                        "scientific-history-tooltip-text"
                }
            );

        tooltip.appendChild(
            tooltipBg
        );

        tooltip.appendChild(
            tooltipText
        );

        svg.appendChild(
            tooltip
        );

        function drawPoints(
            pairs,
            cssClass
        ) {
            for (const pair of pairs) {

                const x =
                    xScale(
                        pair.observed
                    );

                const y =
                    yScale(
                        pair.reference
                    );

                const circle =
                    scientificSvgElement(
                        "circle",
                        {
                            cx: x,
                            cy: y,
                            r: 3.8,
                            class:
                                `scientific-concordance-point ${cssClass}`
                        }
                    );

                circle.addEventListener(
                    "mouseenter",
                    () => {

                        tooltipText.innerHTML =
                            "";

                        const delta =
                            pair.reference -
                            pair.observed;

                        const lines = [
                            pair.source,
                            scientificLocalTime(
                                pair.timestamp
                            ),
                            `Local: ${
                                pair.observed.toFixed(2)
                            } ${variable.unit}`,
                            `Referencia: ${
                                pair.reference.toFixed(2)
                            } ${variable.unit}`,
                            `Δ: ${
                                delta.toFixed(2)
                            } ${variable.unit}`
                        ];

                        lines.forEach(
                            (
                                line,
                                index
                            ) => {

                                const tspan =
                                    scientificSvgElement(
                                        "tspan",
                                        {
                                            x: 10,
                                            dy:
                                                index === 0
                                                    ? 0
                                                    : 15
                                        }
                                    );

                                tspan.textContent =
                                    line;

                                tooltipText
                                    .appendChild(
                                        tspan
                                    );
                            }
                        );

                        let tooltipX =
                            x + 10;

                        if (
                            tooltipX +
                            225 >
                            W - 5
                        ) {
                            tooltipX =
                                x - 235;
                        }

                        let tooltipY =
                            y - 15;

                        if (tooltipY < 5) {
                            tooltipY = 5;
                        }

                        if (
                            tooltipY +
                            84 >
                            H - 5
                        ) {
                            tooltipY =
                                H - 89;
                        }

                        tooltip.setAttribute(
                            "transform",
                            `translate(${tooltipX},${tooltipY})`
                        );

                        tooltip.style.display =
                            "";
                    }
                );

                circle.addEventListener(
                    "mouseleave",
                    () => {
                        tooltip.style.display =
                            "none";
                    }
                );

                svg.appendChild(
                    circle
                );
            }
        }

        drawPoints(
            era5Pairs,
            "scientific-concordance-era5"
        );

        drawPoints(
            nasaPairs,
            "scientific-concordance-nasa"
        );

        /*
         * Mantener tooltip por encima de los puntos.
         */
        svg.appendChild(
            tooltip
        );
    }



    function scientificDrawHistory(
        stationId,
        payload
    ) {
        const svg =
            document.getElementById(
                `scientific-history-chart-${stationId.toLowerCase()}`
            );

        const summary =
            document.getElementById(
                `scientific-history-summary-${stationId.toLowerCase()}`
            );

        if (!svg || !summary) {
            return;
        }

        svg.innerHTML = "";

        const allRecords =
            Array.isArray(payload?.records)
                ? payload.records
                : [];

        /*
         * Mantener la ventana visual razonable.
         *
         * Se muestran las últimas 168 observaciones horarias
         * disponibles (hasta 7 días) sin modificar el conjunto
         * científico del backend.
         */
        /*
         * Ventana de comparación científica.
         *
         * El gráfico debe estar anclado al último instante
         * donde exista al menos una referencia externa.
         * De ese modo no desplazamos fuera de la ventana
         * las coincidencias ERA5/NASA por la continuidad
         * posterior del sensor local.
         */
        let lastComparableIndex = -1;

        for (
            let i = allRecords.length - 1;
            i >= 0;
            i--
        ) {
            const record = allRecords[i];

            if (
                scientificNumber(record?.era5) !== null ||
                scientificNumber(record?.nasa) !== null
            ) {
                lastComparableIndex = i;
                break;
            }
        }

        const records =
            lastComparableIndex >= 0
                ? allRecords.slice(
                    Math.max(
                        0,
                        lastComparableIndex - 167
                    ),
                    lastComparableIndex + 1
                )
                : allRecords.slice(-168);

        const variableKey =
            scientificChartSelection[stationId]
            ?? "temperature";

        const variable =
            scientificChartVariables[variableKey]
            ?? scientificChartVariables.temperature;

        const matchedEra5 =
            Number(payload?.matched_era5 ?? 0);

        const matchedNasa =
            Number(payload?.matched_nasa ?? 0);

        const fieldStart =
            payload?.field_start_local
                ? ` · Inicio de campo: ${
                    v4FormatScientificDate(
                        payload.field_start_local
                    )
                }`
                : "";

        const legend =
            document.getElementById(
                `scientific-history-legend-${stationId.toLowerCase()}`
            );

        if (legend) {
            legend.innerHTML = `
                <span class="scientific-history-legend-item">
                    <i class="scientific-history-key local"></i>
                    Sensor local
                </span>

                <span class="scientific-history-legend-item">
                    <i class="scientific-history-key era5"></i>
                    ERA5-Land
                </span>

                <span class="scientific-history-legend-item">
                    <i class="scientific-history-key nasa"></i>
                    NASA POWER
                </span>
            `;
        }

        summary.innerHTML = `
            <strong>${payload?.label ?? variable.label}</strong>
            · ERA5: ${matchedEra5} coincidencias
            · NASA: ${matchedNasa} coincidencias
            ${fieldStart}
        `;

        if (!records.length) {
            const text =
                scientificSvgElement(
                    "text",
                    {
                        x: 450,
                        y: 165,
                        "text-anchor": "middle",
                        class: "scientific-chart-empty"
                    }
                );

            text.textContent =
                "Sin observaciones científicas disponibles";

            svg.appendChild(text);
            return;
        }

        const parsed = records
            .map(record => ({
                timestamp:
                    scientificDate(record.timestamp),
                observed:
                    scientificNumber(record.observed),
                era5:
                    scientificNumber(record.era5),
                nasa:
                    scientificNumber(record.nasa)
            }))
            .filter(record => record.timestamp);

        if (!parsed.length) {
            return;
        }

        const numericValues = [];

        for (const record of parsed) {
            for (const key of [
                "observed",
                "era5",
                "nasa"
            ]) {
                if (record[key] !== null) {
                    numericValues.push(record[key]);
                }
            }
        }

        if (!numericValues.length) {
            return;
        }

        const W = 900;
        const H = 330;

        const margin = {
            left: 72,
            right: 24,
            top: 20,
            bottom: 58
        };

        const chartWidth =
            W - margin.left - margin.right;

        const chartHeight =
            H - margin.top - margin.bottom;

        let minY = Math.min(...numericValues);
        let maxY = Math.max(...numericValues);

        if (minY === maxY) {
            minY -= 1;
            maxY += 1;
        }

        const padding =
            Math.max(
                (maxY - minY) * 0.08,
                0.1
            );

        minY -= padding;
        maxY += padding;

        const minTime =
            parsed[0].timestamp.getTime();

        let maxTime =
            parsed[parsed.length - 1]
                .timestamp
                .getTime();

        if (minTime === maxTime) {
            maxTime += 3600000;
        }

        const xScale = time =>
            margin.left +
            (
                (
                    time.getTime() - minTime
                ) /
                (
                    maxTime - minTime
                )
            ) * chartWidth;

        const yScale = value =>
            margin.top +
            (
                1 -
                (
                    (value - minY) /
                    (maxY - minY)
                )
            ) * chartHeight;

        /*
         * Rejilla y eje Y.
         */
        for (let i = 0; i <= 4; i++) {
            const ratio = i / 4;

            const y =
                margin.top +
                ratio * chartHeight;

            const value =
                maxY -
                ratio * (maxY - minY);

            const grid =
                scientificSvgElement(
                    "line",
                    {
                        x1: margin.left,
                        x2: W - margin.right,
                        y1: y,
                        y2: y,
                        class: "scientific-chart-grid"
                    }
                );

            svg.appendChild(grid);

            const label =
                scientificSvgElement(
                    "text",
                    {
                        x: margin.left - 12,
                        y: y + 4,
                        "text-anchor": "end",
                        class: "scientific-chart-axis-label"
                    }
                );

            label.textContent =
                value.toFixed(
                    Math.abs(maxY - minY) < 10
                        ? 1
                        : 0
                );

            svg.appendChild(label);
        }

        /*
         * Eje X en hora local America/Lima.
         */
        const tickCount =
            Math.min(
                5,
                Math.max(
                    2,
                    parsed.length
                )
            );

        for (let i = 0; i < tickCount; i++) {
            const index =
                Math.round(
                    i *
                    (parsed.length - 1) /
                    (tickCount - 1)
                );

            const record =
                parsed[index];

            const x =
                xScale(record.timestamp);

            const label =
                scientificSvgElement(
                    "text",
                    {
                        x,
                        y: H - 28,
                        "text-anchor": "middle",
                        class: "scientific-chart-axis-label"
                    }
                );

            label.textContent =
                scientificLocalTime(
                    record.timestamp
                );

            svg.appendChild(label);
        }

        const unitLabel =
            scientificSvgElement(
                "text",
                {
                    x: 14,
                    y: margin.top + chartHeight / 2,
                    transform:
                        `rotate(-90 14 ${
                            margin.top +
                            chartHeight / 2
                        })`,
                    "text-anchor": "middle",
                    class: "scientific-chart-unit"
                }
            );

        unitLabel.textContent =
            variable.unit;

        svg.appendChild(unitLabel);

        /*
         * Construir segmentos separados.
         *
         * Cada null corta físicamente la línea.
         * No existe interpolación visual entre huecos.
         */
        function drawSeries(key, cssClass) {
            let segment = [];

            function flush() {
                if (segment.length === 1) {
                    const p = segment[0];

                    svg.appendChild(
                        scientificSvgElement(
                            "circle",
                            {
                                cx: p.x,
                                cy: p.y,
                                r: 2.7,
                                class:
                                    `scientific-chart-point ${cssClass}`
                            }
                        )
                    );
                }

                if (segment.length >= 2) {
                    const points =
                        segment
                            .map(
                                p =>
                                    `${p.x},${p.y}`
                            )
                            .join(" ");

                    svg.appendChild(
                        scientificSvgElement(
                            "polyline",
                            {
                                points,
                                fill: "none",
                                class:
                                    `scientific-chart-line ${cssClass}`
                            }
                        )
                    );
                }

                segment = [];
            }

            for (const record of parsed) {
                const value =
                    record[key];

                if (value === null) {
                    flush();
                    continue;
                }

                segment.push({
                    x: xScale(
                        record.timestamp
                    ),
                    y: yScale(value)
                });
            }

            flush();
        }

        drawSeries(
            "observed",
            "scientific-series-local"
        );

        drawSeries(
            "era5",
            "scientific-series-era5"
        );

        drawSeries(
            "nasa",
            "scientific-series-nasa"
        );

        /*
         * Hover científico:
         * selecciona la observación temporal real más próxima.
         */
        const hoverLine =
            scientificSvgElement(
                "line",
                {
                    y1: margin.top,
                    y2: margin.top + chartHeight,
                    class: "scientific-history-hover-line"
                }
            );

        hoverLine.style.display = "none";
        svg.appendChild(hoverLine);

        const hoverBox =
            scientificSvgElement(
                "g",
                {
                    class: "scientific-history-tooltip"
                }
            );

        hoverBox.style.display = "none";

        const tooltipBg =
            scientificSvgElement(
                "rect",
                {
                    width: 205,
                    height: 82,
                    rx: 7,
                    class: "scientific-history-tooltip-bg"
                }
            );

        const tooltipText =
            scientificSvgElement(
                "text",
                {
                    x: 10,
                    y: 18,
                    class: "scientific-history-tooltip-text"
                }
            );

        hoverBox.appendChild(tooltipBg);
        hoverBox.appendChild(tooltipText);
        svg.appendChild(hoverBox);

        const overlay =
            scientificSvgElement(
                "rect",
                {
                    x: margin.left,
                    y: margin.top,
                    width: chartWidth,
                    height: chartHeight,
                    class: "scientific-history-overlay"
                }
            );

        overlay.addEventListener(
            "mousemove",
            event => {
                const rect =
                    svg.getBoundingClientRect();

                const mouseX =
                    (
                        event.clientX -
                        rect.left
                    ) *
                    (
                        W / rect.width
                    );

                let nearest =
                    parsed[0];

                let nearestDistance =
                    Infinity;

                for (const record of parsed) {
                    const distance =
                        Math.abs(
                            xScale(
                                record.timestamp
                            ) -
                            mouseX
                        );

                    if (
                        distance <
                        nearestDistance
                    ) {
                        nearestDistance =
                            distance;

                        nearest = record;
                    }
                }

                const x =
                    xScale(
                        nearest.timestamp
                    );

                hoverLine.setAttribute(
                    "x1",
                    x
                );

                hoverLine.setAttribute(
                    "x2",
                    x
                );

                hoverLine.style.display = "";

                const textLines = [
                    scientificLocalTime(
                        nearest.timestamp
                    ),
                    `Local: ${
                        nearest.observed === null
                            ? "—"
                            : nearest.observed.toFixed(2)
                    } ${variable.unit}`,
                    `ERA5: ${
                        nearest.era5 === null
                            ? "—"
                            : nearest.era5.toFixed(2)
                    } ${variable.unit}`,
                    `NASA: ${
                        nearest.nasa === null
                            ? "—"
                            : nearest.nasa.toFixed(2)
                    } ${variable.unit}`
                ];

                tooltipText.innerHTML = "";

                textLines.forEach(
                    (line, index) => {
                        const tspan =
                            scientificSvgElement(
                                "tspan",
                                {
                                    x: 10,
                                    dy:
                                        index === 0
                                            ? 0
                                            : 18
                                }
                            );

                        tspan.textContent =
                            line;

                        tooltipText.appendChild(
                            tspan
                        );
                    }
                );

                const tooltipX =
                    x > W - 235
                        ? x - 215
                        : x + 10;

                const tooltipY =
                    margin.top + 8;

                hoverBox.setAttribute(
                    "transform",
                    `translate(${tooltipX},${tooltipY})`
                );

                hoverBox.style.display = "";
            }
        );

        overlay.addEventListener(
            "mouseleave",
            () => {
                hoverLine.style.display =
                    "none";

                hoverBox.style.display =
                    "none";
            }
        );

        svg.appendChild(overlay);
    }


    async function loadScientificHistory(
        stationId
    ) {
        const variable =
            scientificChartSelection[stationId]
            ?? "temperature";

        const mode =
            scientificChartMode[stationId]
            ?? "timeseries";

        const summary =
            document.getElementById(
                `scientific-history-summary-${stationId.toLowerCase()}`
            );

        try {

            if (mode === "summary") {

                const variableKeys =
                    Object.keys(
                        scientificChartVariables
                    );

                const responses =
                    await Promise.all(
                        variableKeys.map(
                            async key => [
                                key,
                                await fetchJSON(
                                    `/api/scientific/hourly?station_id=${stationId}&variable=${key}`
                                )
                            ]
                        )
                    );

                const datasets =
                    Object.fromEntries(
                        responses
                    );

                scientificDrawSummary(
                    stationId,
                    datasets
                );

                return;
            }

            scientificRestoreChart(
                stationId
            );

            const payload =
                await fetchJSON(
                    `/api/scientific/hourly?station_id=${stationId}&variable=${variable}`
                );

            if (mode === "delta") {

                scientificDrawDelta(
                    stationId,
                    payload
                );

            } else if (
                mode === "concordance"
            ) {

                scientificDrawConcordance(
                    stationId,
                    payload
                );

            } else {

                scientificDrawHistory(
                    stationId,
                    payload
                );
            }

        } catch (error) {

            console.warn(
                `scientific hourly ${stationId}`,
                error
            );

            if (summary) {
                summary.textContent =
                    "No fue posible cargar el análisis científico.";
            }
        }
    }


    function installScientificHistoryTabs(
        stationId
    ) {
        const buttons =
            document.querySelectorAll(
                `.scientific-history-tab[data-station="${stationId}"]`
            );

        buttons.forEach(button => {
            button.addEventListener(
                "click",
                async () => {
                    scientificChartMode[
                        stationId
                    ] =
                        button.dataset.mode;

                    buttons.forEach(
                        candidate =>
                            candidate.classList.toggle(
                                "active",
                                candidate === button
                            )
                    );

                    await loadScientificHistory(
                        stationId
                    );
                }
            );
        });
    }



    function installScientificHistorySelector(
        stationId
    ) {
        const select =
            document.getElementById(
                `scientific-history-select-${stationId.toLowerCase()}`
            );

        if (!select) {
            return;
        }

        select.addEventListener(
            "change",
            async event => {
                scientificChartSelection[
                    stationId
                ] = event.target.value;

                await loadScientificHistory(
                    stationId
                );
            }
        );
    }



    function panelHTML(
        stationId,
        latest,
        scientific
    ) {
        /*
         * Comparación científica:
         * utilizar exclusivamente el último bucket temporal
         * estrictamente emparejado entre sensor local, ERA5-Land
         * y NASA POWER.
         *
         * latest_available se reserva para informar disponibilidad
         * de fuentes, no para calcular diferencias científicas.
         */
        const strict =
            scientific?.strict_matched ?? null;

        /*
         * Ventana de validez científica de campo.
         *
         * SJ01 fue desplegada físicamente en Cerro San José
         * el 31/08/2026 a las 16:00 -05.
         * Cualquier strict_matched anterior a ese instante
         * no debe utilizarse como comparación de campaña.
         */
        const SJ01_VALID_FROM =
            new Date("2026-08-31T16:00:00-05:00");

        const strictCandidateTime =
            strict?.local?.timestamp_local ??
            strict?.bucket_hour ??
            null;

        const strictCandidateDate =
            strictCandidateTime
                ? new Date(strictCandidateTime)
                : null;

        const strictInsideValidPeriod =
            stationId !== "SJ01"
                ? true
                : (
                    strictCandidateDate instanceof Date &&
                    !Number.isNaN(
                        strictCandidateDate.getTime()
                    ) &&
                    strictCandidateDate >= SJ01_VALID_FROM
                );

        const strictAvailable =
            Boolean(strict?.available) &&
            strictInsideValidPeriod;

        const strictLocal =
            strictAvailable
                ? strict?.local
                : null;

        const era5 =
            strictAvailable
                ? strict?.era5
                : null;

        const nasa =
            strictAvailable
                ? strict?.nasa_power
                : null;

        /*
         * Disponibilidad para la tabla estricta.
         * Estas variables NO representan necesariamente
         * disponibilidad general de la fuente.
         */
        const era5StrictOK =
            sourceAvailable(era5);

        const nasaStrictOK =
            sourceAvailable(nasa);

        /*
         * Disponibilidad general de fuentes:
         * se evalúa desde latest_available y permanece
         * independiente de la existencia de un strict_match
         * científicamente válido.
         */
        const latestAvailable =
            scientific?.latest_available ?? {};

        const era5Latest =
            latestAvailable?.era5 ??
            latestAvailable?.era5_land ??
            null;

        const era5SourceOK =
            Boolean(
                era5Latest?.timestamp_local ??
                era5Latest?.timestamp_utc
            );

        const rows =
            variables.map(
                variable => {

                    const observed =
                        strictLocalValue(
                            strictLocal,
                            variable
                        );

                    const era =
                        modelValue(
                            era5,
                            variable.era5
                        );

                    const nas =
                        modelValue(
                            nasa,
                            variable.nasa
                        );

                    const dEra =
                        delta(
                            era,
                            observed
                        );

                    const dNasa =
                        delta(
                            nas,
                            observed
                        );

                    return `
                        <tr>
                            <td>
                                <div class="scientific-variable">
                                    <strong>
                                        ${variable.label}
                                    </strong>
                                    <small>
                                        ${variable.unit}
                                    </small>
                                </div>
                            </td>

                            <td class="scientific-local">
                                ${formatValue(
                                    observed,
                                    variable.unit
                                )}
                            </td>

                            <td class="scientific-model">
                                ${formatValue(
                                    era,
                                    variable.unit
                                )}
                            </td>

                            <td>
                                ${formatDelta(
                                    dEra,
                                    variable.unit,
                                    variable.threshold
                                )}
                            </td>

                            <td class="scientific-model">
                                ${formatValue(
                                    nas,
                                    variable.unit
                                )}
                            </td>

                            <td>
                                ${formatDelta(
                                    dNasa,
                                    variable.unit,
                                    variable.threshold
                                )}
                            </td>
                        </tr>
                    `;
                }
            )
            .join("");

        const strictHour =
            strictAvailable
                ? (
                    strict?.local?.timestamp_local ??
                    strict?.bucket_hour ??
                    null
                )
                : null;

        const strictHourLabel =
            strictAvailable && strictHour
                ? v4FormatScientificDate(strictHour)
                : (
                    stationId === "SJ01" &&
                    !strictInsideValidPeriod
                        ? "SIN COINCIDENCIA ESTRICTA EN PERÍODO VÁLIDO"
                        : "Sin hora común disponible"
                );

        const nasaAvailability =
            v4NasaAvailability(scientific);

        const nasaCurrentOK =
            ["available", "deferred"].includes(
                nasaAvailability.state
            );

        const availableCount =
            Number(era5SourceOK) +
            Number(nasaCurrentOK);

        const qualityText =
            availableCount === 2
                ? "FUENTES DISPONIBLES"
                : (
                    availableCount === 1
                        ? "FUENTE PARCIAL"
                        : "REFERENCIAS PENDIENTES"
                );

        return `
            <section class="scientific-v31">

                <div class="scientific-v31-header">

                    <div>
                        <div class="eyebrow">
                            CONTRASTE CIENTÍFICO
                        </div>

                        <h3>
                            Comparación atmosférica · ${stationId}
                        </h3>

                        <p>
                            Observación local contrastada con
                            ERA5-Land y NASA POWER.
                        </p>
                    </div>

                    <span class="scientific-v31-title-tag">
                        ${qualityText}
                    </span>

                </div>

                <div class="scientific-v31-statusbar">

                    <span class="scientific-source-state ok">
                        SENSOR LOCAL
                    </span>

                    <span class="
                        scientific-source-state
                        ${era5SourceOK ? "ok" : "pending"}
                    ">
                        ERA5-LAND
                        ${era5SourceOK ? "DISPONIBLE" : "PENDIENTE"}
                    </span>

                    <span class="
                        scientific-source-state
                        ${nasaAvailability.state === "deferred" ? "pending" : (nasaCurrentOK ? "ok" : "pending")}
                    ">
                        ${nasaAvailability.label}
                    </span>

                </div>

                <div class="
                    scientific-match-detail
                    ${strictAvailable ? "" : "invalid-period"}
                ">
                    ${
                        strictAvailable
                            ? `
                                Comparación estricta · Hora común:
                                <strong>${strictHourLabel}</strong>
                              `
                            : (
                                stationId === "SJ01"
                                    ? `
                                        <strong>
                                            SIN COINCIDENCIA ESTRICTA
                                            EN PERÍODO VÁLIDO
                                        </strong>
                                        · SJ01 válida en campo desde
                                        31/08/2026 16:00 -05
                                      `
                                    : `
                                        Comparación estricta:
                                        <strong>
                                            ${strictHourLabel}
                                        </strong>
                                      `
                              )
                    }
                </div>

                <div class="
                    scientific-source-detail
                    ${nasaCurrentOK ? "available" : "pending"}
                ">
                    ${nasaAvailability.detail}
                </div>

                ${scientificChartShell(stationId)}

                <div class="scientific-table-wrap">

                    <table class="scientific-table">

                        <thead>
                            <tr>
                                <th>Variable</th>
                                <th>Sensor local</th>
                                <th>ERA5-Land</th>
                                <th>Δ ERA5</th>
                                <th>NASA POWER</th>
                                <th>Δ NASA</th>
                            </tr>
                        </thead>

                        <tbody>
                            ${rows}
                        </tbody>

                    </table>

                </div>

                <div class="scientific-note">
                    Δ = valor de referencia − observación local.
                    La ausencia de valor se representa con “—” y
                    no se sustituye ni interpola en esta vista.
                    Las diferencias se muestran de forma descriptiva:
                    todavía no representan error, sesgo ni
                    incumplimiento QA/QC hasta verificar alineamiento
                    temporal, resolución espacial, altitud y
                    definición de cada variable.
                </div>

            </section>
        `;
    }


    function installContainers() {
        const definitions = [
            {
                station: "CU01",
                anchor: "cu01-detail",
                id: "scientific-cu01"
            },
            {
                station: "SJ01",
                anchor: "sj01-detail",
                id: "scientific-sj01"
            }
        ];

        for (const def of definitions) {

            if (
                document.getElementById(def.id)
            ) {
                continue;
            }

            const anchor =
                document.getElementById(
                    def.anchor
                );

            if (!anchor) {
                continue;
            }

            const container =
                document.createElement(
                    "div"
                );

            container.id = def.id;

            anchor.insertAdjacentElement(
                "afterend",
                container
            );
        }
    }


    function improveSensorStates() {
        document
            .querySelectorAll(".detail-card")
            .forEach(card => {

                const label =
                    card.querySelector("span");

                const value =
                    card.querySelector("strong");

                const unit =
                    card.querySelector("small");

                if (
                    !label ||
                    !value
                ) {
                    return;
                }

                const name =
                    label.textContent
                        .trim()
                        .toLowerCase();

                const sensorNames = [
                    "bme",
                    "pluviómetro",
                    "anemómetro"
                ];

                if (
                    !sensorNames.includes(name)
                ) {
                    return;
                }

                const raw =
                    value.textContent.trim();

                if (
                    raw === "1" ||
                    raw === "1.0"
                ) {
                    value.textContent = "OK";
                    value.classList.add(
                        "sensor-state-ok"
                    );

                    if (unit) {
                        unit.textContent =
                            "operativo";
                    }
                } else if (
                    raw === "0" ||
                    raw === "0.0"
                ) {
                    value.textContent =
                        "REVISAR";

                    if (unit) {
                        unit.textContent =
                            "sensor";
                    }
                }
            });
    }


    
function v4FormatScientificDate(value) {
    if (!value) return "—";

    const normalized = String(value).includes("T")
        ? String(value)
        : String(value).replace(" ", "T");

    const d = new Date(normalized);

    if (Number.isNaN(d.getTime())) {
        return String(value);
    }

    return new Intl.DateTimeFormat("es-PE", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    }).format(d);
}


function v4NasaAvailability(scientific) {
    const latest = scientific?.latest_available ?? {};
    const nasa = latest?.nasa_power ?? null;

    if (!nasa || !nasa.timestamp_local) {
        return {
            state: "pending",
            label: "NASA POWER PENDIENTE",
            detail: "Sin dato NASA POWER disponible",
        };
    }

    const ageSeconds = Number(latest?.nasa_age_seconds);

    /*
     * NASA POWER tiene disponibilidad diferida.
     * Para el panel científico no interpretamos una edad elevada
     * como fallo del sistema; informamos disponibilidad temporal.
     */
    const pending =
        Number.isFinite(ageSeconds) &&
        ageSeconds > (3 * 24 * 3600);

    const lastValid = v4FormatScientificDate(
        nasa.timestamp_local
    );

    const lastQuery = v4FormatScientificDate(
        nasa.downloaded_at_utc
    );

    const ageLabel =
        latest?.nasa_age_label ?? "—";

    return {
        state: pending ? "deferred" : "available",
        label: pending
            ? "NASA POWER · DISPONIBLE DIFERIDO"
            : "NASA POWER DISPONIBLE",
        detail:
            `Último dato válido: ${lastValid}` +
            ` · Edad: ${ageLabel}` +
            ` · Última consulta: ${lastQuery}`,
    };
}


async function fetchJSON(url) {
        const response =
            await fetch(
                url,
                {
                    cache: "no-store"
                }
            );

        if (!response.ok) {
            throw new Error(
                `${response.status} ${response.statusText}`
            );
        }

        return response.json();
    }


    async function loadStation(stationId) {
        let latest = null;
        let scientific = null;

        try {
            latest =
                await fetchJSON(
                    `/api/station/latest?station_id=${stationId}`
                );
        } catch (error) {
            console.warn(
                `latest ${stationId}`,
                error
            );
        }

        try {
            scientific =
                await fetchJSON(
                    `/api/station/scientific?station_id=${stationId}`
                );
        } catch (error) {
            console.warn(
                `scientific ${stationId}`,
                error
            );
        }

        scientificState[stationId] = {
            latest,
            scientific
        };

        const target =
            document.getElementById(
                `scientific-${stationId.toLowerCase()}`
            );

        if (target) {
            target.innerHTML =
                panelHTML(
                    stationId,
                    latest,
                    scientific
                );

            installScientificHistoryTabs(
                stationId
            );

            installScientificHistorySelector(
                stationId
            );

            await loadScientificHistory(
                stationId
            );
        }
    }


    async function refreshScientific() {
        installContainers();

        await Promise.all([
            loadStation("CU01"),
            loadStation("SJ01")
        ]);

        improveSensorStates();
    }


    function installVersionLabel() {
        const footer =
            document.querySelector(
                ".sidebar-meta"
            );

        if (!footer) {
            return;
        }

        footer.textContent =
            "AtmosLink UI V4.1";

        if (
            !document.querySelector(
                ".v31-version"
            )
        ) {
            const version =
                document.createElement(
                    "div"
                );

            version.className =
                "v31-version";

            version.textContent =
                "Scientific comparison layer";

            footer.insertAdjacentElement(
                "afterend",
                version
            );
        }
    }


    function startObserver() {
        const observer =
            new MutationObserver(
                () => {
                    improveSensorStates();
                }
            );

        observer.observe(
            document.body,
            {
                childList: true,
                subtree: true
            }
        );
    }


    async function init() {
        installContainers();
        installVersionLabel();
        startObserver();

        await refreshScientific();

        setInterval(
            refreshScientific,
            REFRESH_MS
        );
    }


    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            init
        );
    } else {
        init();
    }

})();
