(() => {
    "use strict";

    const REFRESH_MS = 30000;

    const SJ01_FIELD_START =
        "2026-08-31T16:00:00-05:00";

    const state = {
        CU01: null,
        SJ01: null,
        throughput: null,
        historyCU01: [],
        historySJ01: [],
        lastRefresh: null
    };


    const $ = (id) => document.getElementById(id);


    function safeNumber(value) {
        if (
            value === null ||
            value === undefined ||
            value === ""
        ) {
            return null;
        }

        const n = Number(value);

        return Number.isFinite(n)
            ? n
            : null;
    }


    function fmt(value, digits = 1) {
        const n = safeNumber(value);

        if (n === null) {
            return "--";
        }

        return n.toFixed(digits);
    }


    function fmtInteger(value) {
        const n = safeNumber(value);

        if (n === null) {
            return "--";
        }

        return Math.round(n).toString();
    }


    function fmtDate(value) {
        if (!value) {
            return "--";
        }

        try {
            const d = new Date(value);

            if (Number.isNaN(d.getTime())) {
                return String(value);
            }

            return d.toLocaleString(
                "es-PE",
                {
                    day: "2-digit",
                    month: "2-digit",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit"
                }
            );
        } catch (_) {
            return String(value);
        }
    }


    function stationFreshness(data) {
        if (!data) {
            return {
                level: "stale",
                text: "SIN DATOS",
                age: null
            };
        }

        const age =
            Number(data.observation_age_seconds);

        if (!Number.isFinite(age)) {
            return {
                level: "stale",
                text: "SIN DATOS",
                age: null
            };
        }

        if (age <= 180) {
            return {
                level: "fresh",
                text: "DATO FRESCO",
                age
            };
        }

        if (age <= 600) {
            return {
                level: "delayed",
                text: "RETRASADO",
                age
            };
        }

        return {
            level: "stale",
            text: "SIN DATOS RECIENTES",
            age
        };
    }


    function radioFreshness(radio) {
        if (
            !radio ||
            !radio.timestamp_local
        ) {
            return {
                level: "stale",
                text: "RF SIN DATOS",
                age: null
            };
        }

        const age =
            Number(radio.age_seconds);

        if (!Number.isFinite(age)) {
            return {
                level: "delayed",
                text: "RF SIN EDAD",
                age: null
            };
        }

        if (age <= 120) {
            return {
                level: "fresh",
                text: "RF FRESCA",
                age
            };
        }

        if (age <= 300) {
            return {
                level: "delayed",
                text: "RF RETRASADA",
                age
            };
        }

        return {
            level: "stale",
            text: "RF SIN ACTUALIZAR",
            age
        };
    }


    function humanAge(seconds) {
        const value = Number(seconds);

        if (!Number.isFinite(value) || value < 0) {
            return "--";
        }

        const s = Math.round(value);

        if (s < 60) {
            return `hace ${s} s`;
        }

        const minutes = Math.floor(s / 60);
        const remainingSeconds = s % 60;

        if (minutes < 60) {
            return remainingSeconds
                ? `hace ${minutes} min ${remainingSeconds} s`
                : `hace ${minutes} min`;
        }

        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;

        if (hours < 24) {
            return remainingMinutes
                ? `hace ${hours} h ${remainingMinutes} min`
                : `hace ${hours} h`;
        }

        const days = Math.floor(hours / 24);
        const remainingHours = hours % 24;

        return remainingHours
            ? `hace ${days} d ${remainingHours} h`
            : `hace ${days} d`;
    }


    function radioObject() {
        const candidates = [
            state.SJ01?.radio,
            state.CU01?.radio
        ];

        for (const radio of candidates) {
            if (
                radio &&
                typeof radio === "object" &&
                (
                    radio.timestamp_local ||
                    radio.snr_dl !== null ||
                    radio.mcs_dl !== null ||
                    radio.sta_dl_rssi !== null
                )
            ) {
                return radio;
            }
        }

        return {};
    }


    function setStatus(id, level, text) {
        const node = $(id);

        if (!node) {
            return;
        }

        node.classList.remove(
            "online",
            "waiting",
            "error",
            "fresh",
            "delayed",
            "stale"
        );

        node.classList.add(level);

        node.textContent =
            text || "--";
    }


    function setText(id, value) {
        const node = $(id);

        if (node) {
            node.textContent = value;
        }
    }


    function renderStation(prefix, data) {
        if (!data) {
            return;
        }

        setText(
            `${prefix}-temp`,
            fmt(data.temp_avg_C, 2)
        );

        setText(
            `${prefix}-hum`,
            fmt(data.hum_avg_pct, 2)
        );

        setText(
            `${prefix}-pres`,
            fmt(data.pres_avg_hPa, 2)
        );

        setText(
            `${prefix}-rain`,
            fmt(data.rain_1h_mm, 2)
        );

        setText(
            `${prefix}-wind`,
            fmt(data.wind_speed_ms, 1)
        );

        setText(
            `${prefix}-gust`,
            fmt(data.wind_gust_ms, 2)
        );

        setText(
            `${prefix}-dir`,
            fmt(data.wind_direction_deg, 1) + "°"
        );

        setText(
            `${prefix}-dirtext`,
            data.wind_direction_text || "--"
        );
    }


    function renderHealth() {
        const cu =
            stationFreshness(state.CU01);

        const sj =
            stationFreshness(state.SJ01);

        setStatus(
            "cu01-health",
            cu.level,
            cu.text
        );

        setStatus(
            "sj01-health",
            sj.level,
            sj.text
        );

        setText(
            "cu01-last",
            `${humanAge(cu.age)} · ${
                fmtDate(
                    state.CU01?.weather_timestamp_local ||
                    state.CU01?.timestamp_local
                )
            }`
        );

        setText(
            "sj01-last",
            `${humanAge(sj.age)} · ${
                fmtDate(
                    state.SJ01?.weather_timestamp_local ||
                    state.SJ01?.timestamp_local
                )
            }`
        );

        const radio =
            radioObject();

        const rf =
            radioFreshness(radio);

        setStatus(
            "radio-health",
            rf.level,
            rf.text
        );

        setText(
            "radio-last",
            `${humanAge(rf.age)} · ${
                fmtDate(radio.timestamp_local)
            }`
        );
    }


    function renderRF() {
        const radio = radioObject();

        const rssiDL =
            radio.sta_dl_rssi ??
            radio.rssi_c0p;

        const rssiUL =
            radio.sta_ul_rssi ??
            radio.rssi_c1p;

        setText(
            "rf-rssi-dl",
            fmt(rssiDL, 0)
        );

        setText(
            "rf-rssi-ul",
            fmt(rssiUL, 0)
        );

        setText(
            "rf-snr-dl",
            fmt(radio.snr_dl, 0)
        );

        setText(
            "rf-snr-ul",
            fmt(radio.snr_ul, 0)
        );

        setText(
            "rf-mcs-dl",
            fmtInteger(radio.mcs_dl)
        );

        setText(
            "rf-mcs-ul",
            fmtInteger(radio.mcs_ul)
        );

        setText(
            "rf-rate-dl",
            fmt(radio.dl_rate, 1)
        );

        setText(
            "rf-age",
            fmtInteger(radio.age_seconds)
        );
    }


    function mountActiveThroughputPanel() {
        if ($("active-throughput-panel")) {
            return;
        }

        const radioView = $("view-radio");

        if (!radioView) {
            return;
        }

        radioView.insertAdjacentHTML(
            "beforeend",
            `
            <section
                id="active-throughput-panel"
                class="active-throughput-panel"
            >
                <div class="active-throughput-header">
                    <div>
                        <span class="panel-kicker">
                            MEDICIÓN ACTIVA
                        </span>

                        <h3>
                            iperf3 + ICMP
                        </h3>

                        <p>
                            Throughput TCP medido y latencia de extremo a extremo.
                            No corresponde al Link Rate reportado por Cambium.
                        </p>
                    </div>

                    <div
                        id="active-throughput-status"
                        class="status-pill delayed"
                    >
                        ESPERANDO
                    </div>
                </div>

                <div class="active-throughput-grid">

                    <div class="active-metric">
                        <span>Throughput DL</span>
                        <strong id="active-dl">--</strong>
                        <small>Mbps · iperf3</small>
                    </div>

                    <div class="active-metric">
                        <span>Throughput UL</span>
                        <strong id="active-ul">--</strong>
                        <small>Mbps · iperf3</small>
                    </div>

                    <div class="active-metric">
                        <span>RTT promedio</span>
                        <strong id="active-rtt">--</strong>
                        <small>ms · ICMP</small>
                    </div>

                    <div class="active-metric">
                        <span>Pérdida</span>
                        <strong id="active-loss">--</strong>
                        <small>% · ICMP</small>
                    </div>

                    <div class="active-metric">
                        <span>Retrans. DL</span>
                        <strong id="active-retr-dl">--</strong>
                        <small>TCP</small>
                    </div>

                    <div class="active-metric">
                        <span>Retrans. UL</span>
                        <strong id="active-retr-ul">--</strong>
                        <small>TCP</small>
                    </div>

                </div>

                <div class="active-throughput-meta">

                    <div>
                        <span>Configuración</span>
                        <strong id="active-rf-config">
                            -- MHz · -- MHz
                        </strong>
                    </div>

                    <div>
                        <span>Potencia TX</span>
                        <strong id="active-tx-power">
                            AP -- · SM --
                        </strong>
                    </div>

                    <div>
                        <span>Última prueba</span>
                        <strong id="active-last">
                            --
                        </strong>
                    </div>

                    <div>
                        <span>Edad</span>
                        <strong id="active-age">
                            --
                        </strong>
                    </div>

                </div>

                <div class="active-throughput-note">
                    <strong>Separación metodológica:</strong>
                    Link Rate Cambium ≠ throughput activo iperf3.
                </div>

            </section>
            `
        );
    }


    function throughputFreshness(data) {
        const age =
            safeNumber(data?.age_seconds);

        if (
            !data ||
            data.status !== "ok" ||
            age === null
        ) {
            return {
                level: "stale",
                text: "SIN MEDICIÓN",
                age: age
            };
        }

        /*
         * La prueba se ejecuta cada 15 min.
         * Hasta 20 min: comportamiento normal.
         * 20–35 min: retrasada.
         * >35 min: sin medición reciente.
         */
        if (age <= 1200) {
            return {
                level: "fresh",
                text: "MEDICIÓN FRESCA",
                age: age
            };
        }

        if (age <= 2100) {
            return {
                level: "delayed",
                text: "MEDICIÓN RETRASADA",
                age: age
            };
        }

        return {
            level: "stale",
            text: "SIN MEDICIÓN RECIENTE",
            age: age
        };
    }


    function renderActiveThroughput() {
        const data = state.throughput;

        if (!data) {
            return;
        }

        const dl = data.dl || {};
        const ul = data.ul || {};
        const cfg = data.configuration || {};

        setText(
            "active-dl",
            fmt(dl.throughput_mbps, 2)
        );

        setText(
            "active-ul",
            fmt(ul.throughput_mbps, 2)
        );

        /*
         * Ping se ejecuta asociado a ambas direcciones.
         * Preferimos UL y usamos DL como fallback.
         */
        const rtt =
            safeNumber(ul.rtt_avg_ms) ??
            safeNumber(dl.rtt_avg_ms);

        const loss =
            safeNumber(ul.loss_pct) ??
            safeNumber(dl.loss_pct);

        setText(
            "active-rtt",
            fmt(rtt, 3)
        );

        setText(
            "active-loss",
            fmt(loss, 1)
        );

        setText(
            "active-retr-dl",
            fmtInteger(dl.retransmits)
        );

        setText(
            "active-retr-ul",
            fmtInteger(ul.retransmits)
        );

        const freq =
            safeNumber(cfg.frequency_mhz);

        const width =
            safeNumber(cfg.channel_width_mhz);

        setText(
            "active-rf-config",
            `${
                freq === null
                    ? "--"
                    : fmt(freq, 0)
            } MHz · ${
                width === null
                    ? "--"
                    : fmt(width, 0)
            } MHz`
        );

        const apPower =
            safeNumber(cfg.ap_tx_power_dbm);

        const smPower =
            safeNumber(cfg.sm_tx_power_dbm);

        setText(
            "active-tx-power",
            `AP ${
                apPower === null
                    ? "--"
                    : fmt(apPower, 0)
            } dBm · SM ${
                smPower === null
                    ? "--"
                    : fmt(smPower, 0)
            } dBm`
        );

        setText(
            "active-last",
            fmtDate(data.timestamp_local)
        );

        const freshness =
            throughputFreshness(data);

        setText(
            "active-age",
            humanAge(freshness.age)
        );

        setStatus(
            "active-throughput-status",
            freshness.level,
            freshness.text
        );
    }


    async function refreshThroughput() {
        try {
            const response = await fetch(
                "/api/v4/throughput/latest",
                {
                    cache: "no-store"
                }
            );

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            state.throughput =
                await response.json();

            renderActiveThroughput();

        } catch (error) {

            console.error(
                "AtmosLink V4 throughput error:",
                error
            );

            state.throughput = null;

            setStatus(
                "active-throughput-status",
                "stale",
                "ERROR API"
            );

            setText(
                "active-age",
                "--"
            );
        }
    }


    function stationDetailHTML(data, stationId) {
        if (!data) {
            return `
                <div class="detail-card">
                    <span>Estado</span>
                    <strong>--</strong>
                    <small>Sin datos disponibles</small>
                </div>
            `;
        }

        const items = [
            [
                "Temperatura",
                fmt(data.temp_avg_C, 2),
                "°C"
            ],
            [
                "Humedad relativa",
                fmt(data.hum_avg_pct, 2),
                "%"
            ],
            [
                "Presión",
                fmt(data.pres_avg_hPa, 2),
                "hPa"
            ],
            [
                "Punto de rocío",
                fmt(data.dew_point_C, 2),
                "°C"
            ],
            [
                "Lluvia 1 min",
                fmt(data.rain_1min_mm, 2),
                "mm"
            ],
            [
                "Lluvia 1 hora",
                fmt(data.rain_1h_mm, 2),
                "mm"
            ],
            [
                "Lluvia acumulada",
                fmt(data.rain_total_mm, 2),
                "mm"
            ],
            [
                "Viento",
                fmt(data.wind_speed_ms, 1),
                "m/s"
            ],
            [
                "Dirección",
                fmt(data.wind_direction_deg, 1),
                `° ${data.wind_direction_text || ""}`
            ],
            [
                "Ráfaga",
                fmt(data.wind_gust_ms, 1),
                "m/s"
            ],
            [
                "BME",
                String(data.bme_ok ?? "--"),
                "estado"
            ],
            [
                "Pluviómetro",
                String(data.rain_ok ?? "--"),
                "estado"
            ],
            [
                "Anemómetro",
                String(data.wind_ok ?? "--"),
                "estado"
            ],
            [
                "Edad observación",
                fmtInteger(
                    data.observation_age_seconds
                ),
                "s"
            ],
            [
                "Firmware",
                data.firmware_version || "--",
                data.firmware_build
                    ? `build ${data.firmware_build}`
                    : ""
            ],
            [
                "Fuente",
                data.source_kind || "--",
                stationId === "SJ01"
                    ? "sincronización remota"
                    : "estación local"
            ]
        ];

        return items
            .map(
                ([label, value, unit]) => `
                    <div class="detail-card">
                        <span>${label}</span>
                        <strong>${value}</strong>
                        <small>${unit}</small>
                    </div>
                `
            )
            .join("");
    }


    function radioDetailHTML() {
        const radio = radioObject();

        const rssiDL =
            radio.sta_dl_rssi ??
            radio.rssi_c0p;

        const rssiUL =
            radio.sta_ul_rssi ??
            radio.rssi_c1p;

        const items = [
            ["RSSI DL", fmt(rssiDL, 0), "dBm"],
            ["RSSI UL", fmt(rssiUL, 0), "dBm"],
            ["SNR DL", fmt(radio.snr_dl, 0), "dB"],
            ["SNR UL", fmt(radio.snr_ul, 0), "dB"],
            ["MCS DL", fmtInteger(radio.mcs_dl), ""],
            ["MCS UL", fmtInteger(radio.mcs_ul), ""],
            ["Link Rate DL", fmt(radio.dl_rate, 1), "Mbps"],
            ["Link Rate UL", fmt(radio.ul_rate, 1), "Mbps"],
            ["Edad RF", fmtInteger(radio.age_seconds), "s"],
            ["Fuente", radio.source || "--", ""],
            ["Nota", radio.note || "--", ""],
            ["Error", radio.error || "Sin error", ""]
        ];

        return items
            .map(
                ([label, value, unit]) => `
                    <div class="detail-card">
                        <span>${label}</span>
                        <strong>${value}</strong>
                        <small>${unit}</small>
                    </div>
                `
            )
            .join("");
    }


    function renderDetails() {
        const cu =
            $("cu01-detail");

        const sj =
            $("sj01-detail");

        const rf =
            $("radio-detail");

        if (cu) {
            cu.innerHTML =
                stationDetailHTML(
                    state.CU01,
                    "CU01"
                );
        }

        if (sj) {
            sj.innerHTML =
                stationDetailHTML(
                    state.SJ01,
                    "SJ01"
                );
        }

        if (rf) {
            rf.innerHTML =
                radioDetailHTML();
        }
    }


    function extractTemperature(records) {
        return (records || [])
            .map(
                (r) => ({
                    value: safeNumber(r.temp_avg_C),
                    timestamp:
                        r.weather_timestamp_local ||
                        r.timestamp_local
                })
            )
            .filter(
                (x) => x.value !== null
            );
    }


    function drawLineChart(svgId, records) {
        const svg = $(svgId);

        if (!svg) {
            return;
        }

        const stationId =
            svgId.includes("cu01")
                ? "CU01"
                : "SJ01";

        const config =
            observationChartConfig(stationId);

        const parseTime = record => {
            const raw =
                record?.timestamp_local ??
                record?.weather_timestamp_local ??
                null;

            if (!raw) {
                return null;
            }

            const normalized =
                String(raw).replace(
                    /^(\d{4}-\d{2}-\d{2}) /,
                    "$1T"
                );

            const d = new Date(normalized);

            return Number.isNaN(d.getTime())
                ? null
                : d;
        };

        const points =
            (records ?? [])
                .map(record => {
                    const value =
                        Number(record?.temp_avg_C);

                    return {
                        value:
                            Number.isFinite(value)
                                ? value
                                : null,
                        time:
                            parseTime(record)
                    };
                })
                .filter(
                    point =>
                        point.value !== null
                );

        if (points.length < 2) {
            svg.innerHTML = `
                <text
                    x="500"
                    y="140"
                    text-anchor="middle"
                    class="chart-label"
                >
                    Datos insuficientes
                </text>
            `;
            return;
        }

        const width = 1000;
        const height = 300;

        const left = 70;
        const right = 20;
        const top = 20;
        const bottom = 48;

        const usableW =
            width - left - right;

        const usableH =
            height - top - bottom;

        const values =
            points.map(p => p.value);

        let min =
            Math.min(...values);

        let max =
            Math.max(...values);

        let range =
            max - min;

        if (range === 0) {
            range =
                Math.abs(max) > 0
                    ? Math.abs(max) * 0.1
                    : 1;
        }

        min -= range * 0.08;
        max += range * 0.08;

        if (
            ["humidity", "rain1h", "wind", "gust"]
                .includes(
                    observationChartSelection[
                        stationId
                    ]
                ) &&
            min < 0
        ) {
            min = 0;
        }

        const times =
            points.map(
                p =>
                    p.time
                        ? p.time.getTime()
                        : null
            );

        const useTime =
            times.every(Number.isFinite);

        const tMin =
            useTime
                ? Math.min(...times)
                : 0;

        const tMax =
            useTime
                ? Math.max(...times)
                : points.length - 1;

        const tRange =
            Math.max(
                1,
                tMax - tMin
            );

        const coords =
            points.map(
                (point, index) => {

                    const domain =
                        useTime
                            ? point.time.getTime()
                            : index;

                    const x =
                        left +
                        (
                            (domain - tMin) /
                            tRange
                        ) * usableW;

                    const y =
                        top +
                        (
                            1 -
                            (
                                (point.value - min) /
                                (max - min)
                            )
                        ) * usableH;

                    return {
                        ...point,
                        x,
                        y
                    };
                }
            );

        const polyline =
            coords
                .map(
                    p =>
                        `${p.x.toFixed(1)},${p.y.toFixed(1)}`
                )
                .join(" ");

        const area =
            [
                `${coords[0].x},${height - bottom}`,
                ...coords.map(
                    p => `${p.x},${p.y}`
                ),
                `${coords[coords.length - 1].x},${height - bottom}`
            ].join(" ");

        const yParts = [];

        for (let i = 0; i <= 4; i++) {
            const fraction =
                i / 4;

            const y =
                top +
                usableH * fraction;

            const value =
                max -
                (max - min) * fraction;

            yParts.push(`
                <line
                    x1="${left}"
                    y1="${y}"
                    x2="${width - right}"
                    y2="${y}"
                    class="chart-grid"
                />

                <text
                    x="${left - 10}"
                    y="${y + 4}"
                    text-anchor="end"
                    class="chart-axis-label"
                >
                    ${value.toFixed(
                        config.unit === "mm" ? 2 : 1
                    )}
                </text>
            `);
        }

        const formatTime = date =>
            new Intl.DateTimeFormat(
                "es-PE",
                {
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                    timeZone: "America/Lima"
                }
            ).format(date);

        const xParts = [];

        for (let i = 0; i <= 5; i++) {
            const fraction =
                i / 5;

            const x =
                left +
                usableW * fraction;

            let label = "";

            if (useTime) {
                label =
                    formatTime(
                        new Date(
                            tMin +
                            tRange * fraction
                        )
                    );
            }

            xParts.push(`
                <text
                    x="${x}"
                    y="${height - 19}"
                    text-anchor="middle"
                    class="chart-axis-label"
                >
                    ${label}
                </text>
            `);
        }

        svg.setAttribute(
            "viewBox",
            `0 0 ${width} ${height}`
        );

        svg.innerHTML = `
            ${yParts.join("")}
            ${xParts.join("")}

            <line
                x1="${left}"
                y1="${top}"
                x2="${left}"
                y2="${height - bottom}"
                class="chart-axis"
            />

            <line
                x1="${left}"
                y1="${height - bottom}"
                x2="${width - right}"
                y2="${height - bottom}"
                class="chart-axis"
            />

            <text
                x="18"
                y="${height / 2}"
                class="chart-axis-unit"
                text-anchor="middle"
                transform="rotate(-90 18 ${height / 2})"
            >
                ${config.unit}
            </text>

            <text
                x="${width - right}"
                y="${height - 4}"
                class="chart-axis-unit"
                text-anchor="end"
            >
                Hora local (-05)
            </text>

            <polygon
                points="${area}"
                class="chart-area"
            ></polygon>

            <polyline
                points="${polyline}"
                class="chart-line"
            ></polyline>

            <line
                id="${svgId}-hover-line"
                class="chart-hover-line"
                x1="0"
                y1="${top}"
                x2="0"
                y2="${height - bottom}"
                visibility="hidden"
            />

            <circle
                id="${svgId}-hover-dot"
                class="chart-hover-dot"
                cx="0"
                cy="0"
                r="5"
                visibility="hidden"
            />

            <g
                id="${svgId}-tooltip"
                class="chart-tooltip"
                visibility="hidden"
            >
                <rect
                    width="205"
                    height="58"
                    rx="7"
                    class="chart-tooltip-bg"
                ></rect>

                <text
                    x="10"
                    y="20"
                    class="chart-tooltip-time"
                ></text>

                <text
                    x="10"
                    y="42"
                    class="chart-tooltip-value"
                ></text>
            </g>

            <rect
                id="${svgId}-overlay"
                x="${left}"
                y="${top}"
                width="${usableW}"
                height="${usableH}"
                fill="transparent"
                style="cursor:crosshair"
            />
        `;

        const overlay =
            document.getElementById(
                `${svgId}-overlay`
            );

        const hoverLine =
            document.getElementById(
                `${svgId}-hover-line`
            );

        const hoverDot =
            document.getElementById(
                `${svgId}-hover-dot`
            );

        const tooltip =
            document.getElementById(
                `${svgId}-tooltip`
            );

        const timeText =
            tooltip.querySelector(
                ".chart-tooltip-time"
            );

        const valueText =
            tooltip.querySelector(
                ".chart-tooltip-value"
            );

        const formatDateTime = date => {
            if (!date) {
                return "Hora no disponible";
            }

            return new Intl.DateTimeFormat(
                "es-PE",
                {
                    day: "2-digit",
                    month: "2-digit",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                    hour12: false,
                    timeZone: "America/Lima"
                }
            ).format(date);
        };

        overlay.addEventListener(
            "pointermove",
            event => {

                const rect =
                    svg.getBoundingClientRect();

                const mouseX =
                    (
                        (event.clientX - rect.left) /
                        rect.width
                    ) * width;

                let nearest =
                    coords[0];

                let distance =
                    Math.abs(
                        nearest.x - mouseX
                    );

                for (
                    let i = 1;
                    i < coords.length;
                    i++
                ) {
                    const d =
                        Math.abs(
                            coords[i].x -
                            mouseX
                        );

                    if (d < distance) {
                        nearest =
                            coords[i];

                        distance = d;
                    }
                }

                hoverLine.setAttribute(
                    "x1",
                    nearest.x
                );

                hoverLine.setAttribute(
                    "x2",
                    nearest.x
                );

                hoverLine.setAttribute(
                    "visibility",
                    "visible"
                );

                hoverDot.setAttribute(
                    "cx",
                    nearest.x
                );

                hoverDot.setAttribute(
                    "cy",
                    nearest.y
                );

                hoverDot.setAttribute(
                    "visibility",
                    "visible"
                );

                timeText.textContent =
                    formatDateTime(
                        nearest.time
                    );

                const decimals =
                    config.unit === "mm"
                        ? 2
                        : (
                            config.unit === "hPa"
                                ? 2
                                : 1
                        );

                valueText.textContent =
                    `${config.label}: ` +
                    `${nearest.value.toFixed(decimals)} ` +
                    `${config.unit}`;

                let tx =
                    nearest.x + 12;

                if (tx + 205 > width - right) {
                    tx =
                        nearest.x - 217;
                }

                let ty =
                    nearest.y - 70;

                if (ty < top) {
                    ty =
                        nearest.y + 12;
                }

                tooltip.setAttribute(
                    "transform",
                    `translate(${tx},${ty})`
                );

                tooltip.setAttribute(
                    "visibility",
                    "visible"
                );
            }
        );

        overlay.addEventListener(
            "pointerleave",
            () => {
                hoverLine.setAttribute(
                    "visibility",
                    "hidden"
                );

                hoverDot.setAttribute(
                    "visibility",
                    "hidden"
                );

                tooltip.setAttribute(
                    "visibility",
                    "hidden"
                );
            }
        );
    }


    /*
     * V4 — selector de variable para últimas observaciones.
     *
     * Reutiliza drawLineChart() sin modificar el backend:
     * la variable elegida se proyecta temporalmente sobre
     * temp_avg_C, que es el campo consumido por el renderer
     * histórico original.
     */

    const observationChartVariables = {
        temperature: {
            label: "Temperatura",
            unit: "°C",
            field: "temp_avg_C"
        },
        humidity: {
            label: "Humedad relativa",
            unit: "%",
            field: "hum_avg_pct"
        },
        pressure: {
            label: "Presión",
            unit: "hPa",
            field: "pres_avg_hPa"
        },
        rain1h: {
            label: "Lluvia 1 h",
            unit: "mm",
            field: "rain_1h_mm"
        },
        wind: {
            label: "Velocidad del viento",
            unit: "m/s",
            field: "wind_speed_ms"
        },
        gust: {
            label: "Ráfaga",
            unit: "m/s",
            field: "wind_gust_ms"
        }
    };


    const observationChartSelection = {
        CU01: "temperature",
        SJ01: "temperature"
    };


    function observationChartConfig(stationId) {
        const key =
            observationChartSelection[stationId] ??
            "temperature";

        return (
            observationChartVariables[key] ??
            observationChartVariables.temperature
        );
    }


    function observationChartRecords(
        records,
        stationId
    ) {
        const config =
            observationChartConfig(stationId);

        return (records ?? []).map(record => {

            const raw =
                record?.[config.field];

            const numeric =
                raw === null ||
                raw === undefined ||
                raw === ""
                    ? null
                    : Number(raw);

            return {
                ...record,
                temp_avg_C:
                    Number.isFinite(numeric)
                        ? numeric
                        : null
            };
        });
    }


    function updateObservationChartTitle(
        stationId
    ) {
        const config =
            observationChartConfig(stationId);

        const svg =
            document.getElementById(
                `chart-${stationId.toLowerCase()}`
            );

        if (!svg) {
            return;
        }

        let host = svg.parentElement;

        for (
            let depth = 0;
            host && depth < 6;
            depth += 1,
            host = host.parentElement
        ) {
            const headings =
                host.querySelectorAll(
                    "h2, h3, h4"
                );

            for (const heading of headings) {

                const text =
                    heading.textContent.trim();

                if (
                    text.includes(stationId) &&
                    (
                        text.includes("Temperatura") ||
                        text.includes("Humedad") ||
                        text.includes("Presión") ||
                        text.includes("Lluvia") ||
                        text.includes("Viento") ||
                        text.includes("Ráfaga") ||
                        text.includes("Velocidad")
                    )
                ) {
                    heading.textContent =
                        `${config.label} ${stationId}`;

                    return;
                }
            }
        }
    }


    function ensureObservationChartSelector(
        stationId
    ) {
        const stationLower =
            stationId.toLowerCase();

        const svg =
            document.getElementById(
                `chart-${stationLower}`
            );

        if (!svg) {
            return;
        }

        const selectId =
            `chart-variable-${stationLower}`;

        let select =
            document.getElementById(selectId);

        if (!select) {

            const control =
                document.createElement("div");

            control.className =
                "chart-variable-control";

            const label =
                document.createElement("label");

            label.setAttribute(
                "for",
                selectId
            );

            label.textContent =
                "Variable";

            select =
                document.createElement("select");

            select.id = selectId;

            select.className =
                "chart-variable-select";

            for (
                const [key, config]
                of Object.entries(
                    observationChartVariables
                )
            ) {
                const option =
                    document.createElement(
                        "option"
                    );

                option.value = key;

                option.textContent =
                    `${config.label} · ${config.unit}`;

                select.appendChild(option);
            }

            select.value =
                observationChartSelection[
                    stationId
                ];

            select.addEventListener(
                "change",
                () => {
                    observationChartSelection[
                        stationId
                    ] = select.value;

                    renderObservationChart(
                        stationId
                    );
                }
            );

            control.appendChild(label);
            control.appendChild(select);

            svg.insertAdjacentElement(
                "beforebegin",
                control
            );
        }

        select.value =
            observationChartSelection[
                stationId
            ];
    }


    function renderObservationChart(
        stationId
    ) {
        const stationLower =
            stationId.toLowerCase();

        const history =
            stationId === "CU01"
                ? state.historyCU01
                : state.historySJ01;

        ensureObservationChartSelector(
            stationId
        );

        updateObservationChartTitle(
            stationId
        );

        drawLineChart(
            `chart-${stationLower}`,
            observationChartRecords(
                history,
                stationId
            )
        );
    }


    function renderAll() {
        renderStation(
            "cu01",
            state.CU01
        );

        renderStation(
            "sj01",
            state.SJ01
        );

        renderHealth();
        renderRF();
        renderDetails();

        setText(
            "corridor-cu01-temp",
            `${fmt(state.CU01?.temp_avg_C, 1)} °C`
        );

        setText(
            "corridor-sj01-temp",
            `${fmt(state.SJ01?.temp_avg_C, 1)} °C`
        );

        renderObservationChart(
            "CU01"
        );

        renderObservationChart(
            "SJ01"
        );

        if (state.lastRefresh) {
            setText(
                "footer-update",
                `Actualización: ${fmtDate(state.lastRefresh)}`
            );
        }
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


    async function refresh() {
        try {
            const [
                cu01,
                sj01,
                hcu,
                hsj
            ] = await Promise.all([
                fetchJSON(
                    "/api/station/latest?station_id=CU01"
                ),
                fetchJSON(
                    "/api/station/latest?station_id=SJ01"
                ),
                fetchJSON(
                    "/api/station/history?station_id=CU01&limit=120"
                ),
                fetchJSON(
                    "/api/station/history?station_id=SJ01&limit=120"
                )
            ]);

            state.CU01 = cu01;
            state.SJ01 = sj01;

            state.historyCU01 =
                Array.isArray(hcu?.records)
                    ? hcu.records
                    : [];

            state.historySJ01 =
                Array.isArray(hsj?.records)
                    ? hsj.records
                    : [];

            state.lastRefresh =
                new Date().toISOString();

            renderAll();

            $("api-dot")?.classList.remove(
                "error"
            );

            $("api-dot")?.classList.add(
                "online"
            );

            setText(
                "api-state",
                "API multisede conectada"
            );

        } catch (error) {

            console.error(
                "AtmosLink UI V4 refresh error:",
                error
            );

            $("api-dot")?.classList.remove(
                "online"
            );

            $("api-dot")?.classList.add(
                "error"
            );

            setText(
                "api-state",
                "Error de API"
            );
        }
    }



    function systemHealthStateLabel(state) {
        const labels = {
            healthy: "HEALTHY",
            warning: "WARNING",
            error: "ERROR",
            disabled: "DISABLED"
        };

        return labels[state] || "UNKNOWN";
    }


    function systemHealthStateClass(state) {
        if (state === "healthy") {
            return "healthy";
        }

        if (state === "warning") {
            return "warning";
        }

        if (state === "error") {
            return "error";
        }

        if (state === "disabled") {
            return "disabled";
        }

        return "unknown";
    }


    function mountSystemHealthPanel() {
        if ($("system-health-panel")) {
            return;
        }

        const healthGrid =
            document.querySelector(
                "#view-global .health-grid"
            );

        if (!healthGrid) {
            console.warn(
                "System Health: health-grid no encontrado"
            );
            return;
        }

        healthGrid.insertAdjacentHTML(
            "afterend",
            `
            <section
                id="system-health-panel"
                class="system-health-panel"
            >
                <div class="system-health-heading">

                    <div>
                        <div class="eyebrow">
                            SALUD OPERATIVA DE LA PLATAFORMA
                        </div>

                        <h2>
                            System Health
                        </h2>

                        <p>
                            Estado funcional de servicios,
                            temporizadores y frescura real
                            de las fuentes de datos.
                        </p>
                    </div>

                    <span
                        id="system-health-overall"
                        class="system-health-overall unknown"
                    >
                        CONSULTANDO
                    </span>

                </div>

                <div
                    id="system-health-grid"
                    class="system-health-grid"
                >
                    <div class="system-health-loading">
                        Consultando componentes...
                    </div>
                </div>

                <div class="system-health-footer">
                    <span>
                        Evaluación funcional basada en systemd
                        + frescura de datos.
                    </span>

                    <span id="system-health-updated">
                        --
                    </span>
                </div>
            </section>
            `
        );
    }


    function renderSystemHealth(data) {
        const grid =
            $("system-health-grid");

        const overall =
            $("system-health-overall");

        const updated =
            $("system-health-updated");

        if (!grid || !overall) {
            return;
        }

        const components =
            data?.components ?? {};

        const order = [
            "dashboard",
            "logger_cu01",
            "scheduler",
            "sync_sj01",
            "rf_monitor",
            "rf_config",
            "throughput",
            "backup",
            "watchdog",
            "legacy_rflogger"
        ];

        const descriptions = {
            dashboard:
                "Dashboard científico V4",

            logger_cu01:
                "Adquisición meteorológica CU01",

            scheduler:
                "Procesamiento y tareas centrales",

            sync_sj01:
                "Sincronización remota SJ01",

            rf_monitor:
                "Telemetría RF ePMP",

            rf_config:
                "Configuración Force 4600C",

            throughput:
                "Medición activa iperf3 + ICMP",

            backup:
                "Respaldo remoto dual",

            watchdog:
                "Supervisión de frescura meteorológica",

            legacy_rflogger:
                "Componente legado no operativo"
        };

        const cards = order
            .map((key) => {
                const component =
                    components[key];

                if (!component) {
                    return "";
                }

                const state =
                    component.state || "unknown";

                const stateClass =
                    systemHealthStateClass(state);

                const stateLabel =
                    systemHealthStateLabel(state);

                const age =
                    component.age_label &&
                    component.age_label !== "—"
                        ? component.age_label
                        : null;

                const timestamp =
                    component.timestamp || null;

                const informational =
                    component.informational === true;

                let detail = "";

                if (age) {
                    detail =
                        `Dato reciente · ${age}`;
                }
                else if (state === "disabled") {
                    detail =
                        "Deshabilitado intencionalmente";
                }
                else if (state === "healthy") {
                    detail =
                        "Operación nominal";
                }
                else {
                    detail =
                        "Requiere revisión";
                }

                return `
                    <article
                        class="
                            system-health-card
                            ${stateClass}
                            ${informational
                                ? "informational"
                                : ""}
                        "
                    >
                        <div class="system-health-card-top">

                            <div>
                                <div class="system-health-component">
                                    ${component.label || key}
                                </div>

                                <div class="system-health-description">
                                    ${descriptions[key] || ""}
                                </div>
                            </div>

                            <span
                                class="
                                    system-health-status
                                    ${stateClass}
                                "
                            >
                                ${stateLabel}
                            </span>

                        </div>

                        <div class="system-health-meta">
                            <span>
                                ${detail}
                            </span>

                            ${
                                timestamp
                                    ? `
                                        <span
                                            class="system-health-timestamp"
                                            title="${timestamp}"
                                        >
                                            ${timestamp}
                                        </span>
                                      `
                                    : ""
                            }
                        </div>

                    </article>
                `;
            })
            .join("");

        grid.innerHTML =
            cards ||
            `
                <div class="system-health-loading">
                    Sin información de componentes.
                </div>
            `;

        const overallState =
            data?.overall || "unknown";

        overall.className =
            "system-health-overall " +
            systemHealthStateClass(
                overallState
            );

        overall.textContent =
            systemHealthStateLabel(
                overallState
            );

        if (updated) {
            updated.textContent =
                "Actualizado: " +
                new Date().toLocaleTimeString(
                    "es-PE",
                    {
                        hour12: false
                    }
                );
        }
    }


    async function refreshSystemHealth() {
        try {
            const response =
                await fetch(
                    "/api/v4/system-health",
                    {
                        cache: "no-store"
                    }
                );

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            const data =
                await response.json();

            renderSystemHealth(data);
        }
        catch (error) {
            console.error(
                "System Health:",
                error
            );

            const overall =
                $("system-health-overall");

            const grid =
                $("system-health-grid");

            if (overall) {
                overall.className =
                    "system-health-overall error";

                overall.textContent =
                    "ERROR API";
            }

            if (grid) {
                grid.innerHTML =
                    `
                    <div class="
                        system-health-loading
                        system-health-error
                    ">
                        No fue posible consultar
                        /api/v4/system-health
                    </div>
                    `;
            }
        }
    }


    function setupNavigation() {
        const titles = {
            global: "Estado global",
            cu01: "CU01 · Cerro Cuñacales",
            sj01: "SJ01 · Cerro San José",
            radio: "Radio Link · 7000 MHz · 20 MHz"
        };

        document
            .querySelectorAll(".nav-item")
            .forEach(
                (button) => {

                    button.addEventListener(
                        "click",
                        () => {

                            const view =
                                button.dataset.view;

                            document
                                .querySelectorAll(
                                    ".nav-item"
                                )
                                .forEach(
                                    (node) =>
                                        node.classList.remove(
                                            "active"
                                        )
                                );

                            button.classList.add(
                                "active"
                            );

                            document
                                .querySelectorAll(
                                    ".view"
                                )
                                .forEach(
                                    (node) =>
                                        node.classList.remove(
                                            "active"
                                        )
                                );

                            const target =
                                $(`view-${view}`);

                            if (target) {
                                target.classList.add(
                                    "active"
                                );
                            }

                            setText(
                                "page-title",
                                titles[view] ||
                                "AtmosLink"
                            );

                            window.scrollTo({
                                top: 0,
                                behavior: "smooth"
                            });
                        }
                    );
                }
            );
    }


    function updateClock() {
        setText(
            "clock",
            new Date().toLocaleString(
                "es-PE",
                {
                    weekday: "short",
                    day: "2-digit",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit"
                }
            )
        );
    }


    function init() {
        console.info(
            "AtmosLink UI V4",
            {
                sj01FieldStart:
                    SJ01_FIELD_START
            }
        );

        setupNavigation();

        updateClock();
        setInterval(
            updateClock,
            1000
        );

        mountActiveThroughputPanel();
        mountSystemHealthPanel();

        refresh();
        refreshThroughput();
        refreshSystemHealth();

        setInterval(
            refreshSystemHealth,
            30000
        );

        setInterval(
            refresh,
            REFRESH_MS
        );

        setInterval(
            refreshThroughput,
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
