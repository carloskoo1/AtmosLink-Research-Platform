(() => {
    "use strict";

    const REFRESH_MS = 30000;

    const SJ01_FIELD_START =
        "2026-08-31T16:00:00-05:00";

    const state = {
        CU01: null,
        SJ01: null,
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


    function stationOnline(data) {
        if (!data) {
            return false;
        }

        const stateName =
            String(
                data.observation_state ||
                data.status ||
                ""
            ).toUpperCase();

        return (
            stateName === "ONLINE" ||
            stateName === "OK"
        );
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


    function setStatus(id, online, text) {
        const node = $(id);

        if (!node) {
            return;
        }

        node.classList.remove(
            "online",
            "waiting",
            "error"
        );

        node.classList.add(
            online
                ? "online"
                : "error"
        );

        node.textContent =
            text ||
            (
                online
                    ? "ONLINE"
                    : "OFFLINE"
            );
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
            `${prefix}-dir`,
            fmt(data.wind_direction_deg, 1) + "°"
        );

        setText(
            `${prefix}-dirtext`,
            data.wind_direction_text || "--"
        );
    }


    function renderHealth() {
        const cuOnline =
            stationOnline(state.CU01);

        const sjOnline =
            stationOnline(state.SJ01);

        setStatus(
            "cu01-health",
            cuOnline
        );

        setStatus(
            "sj01-health",
            sjOnline
        );

        setText(
            "cu01-last",
            fmtDate(
                state.CU01?.weather_timestamp_local ||
                state.CU01?.timestamp_local
            )
        );

        setText(
            "sj01-last",
            fmtDate(
                state.SJ01?.weather_timestamp_local ||
                state.SJ01?.timestamp_local
            )
        );

        const radio = radioObject();

        const radioOk =
            Boolean(
                radio.timestamp_local &&
                !radio.error
            );

        setStatus(
            "radio-health",
            radioOk,
            radioOk
                ? "ONLINE"
                : "WAITING"
        );

        setText(
            "radio-last",
            fmtDate(radio.timestamp_local)
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
            ["DL Rate", fmt(radio.dl_rate, 1), "Mbps"],
            ["UL Rate", fmt(radio.ul_rate, 1), "Mbps"],
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

        const points =
            extractTemperature(records);

        if (points.length < 2) {
            svg.innerHTML = `
                <text
                    x="500"
                    y="130"
                    text-anchor="middle"
                    class="chart-label"
                >
                    Datos insuficientes
                </text>
            `;
            return;
        }

        const values =
            points.map((p) => p.value);

        let min =
            Math.min(...values);

        let max =
            Math.max(...values);

        if (min === max) {
            min -= 1;
            max += 1;
        }

        const padX = 45;
        const padY = 28;

        const width = 1000;
        const height = 260;

        const usableW =
            width - padX * 2;

        const usableH =
            height - padY * 2;

        const coords =
            points.map(
                (p, index) => {
                    const x =
                        padX +
                        (
                            index /
                            (points.length - 1)
                        ) * usableW;

                    const y =
                        padY +
                        (
                            1 -
                            (
                                (p.value - min) /
                                (max - min)
                            )
                        ) * usableH;

                    return [x, y];
                }
            );

        const polyline =
            coords
                .map(
                    ([x, y]) =>
                        `${x.toFixed(1)},${y.toFixed(1)}`
                )
                .join(" ");

        const area =
            [
                `${coords[0][0]},${height - padY}`,
                ...coords.map(
                    ([x, y]) => `${x},${y}`
                ),
                `${coords[coords.length - 1][0]},${height - padY}`
            ].join(" ");

        const gridLines = [];

        for (let i = 0; i <= 4; i++) {
            const y =
                padY +
                (usableH / 4) * i;

            gridLines.push(`
                <line
                    x1="${padX}"
                    y1="${y}"
                    x2="${width - padX}"
                    y2="${y}"
                    class="chart-grid"
                />
            `);
        }

        svg.innerHTML = `
            ${gridLines.join("")}

            <polygon
                points="${area}"
                class="chart-area"
            ></polygon>

            <polyline
                points="${polyline}"
                class="chart-line"
            ></polyline>
        `;
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

        drawLineChart(
            "chart-cu01",
            state.historyCU01
        );

        drawLineChart(
            "chart-sj01",
            state.historySJ01
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
                "AtmosLink UI v3 refresh error:",
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


    function setupNavigation() {
        const titles = {
            global: "Estado global",
            cu01: "CU01 · Cerro Cuñacales",
            sj01: "SJ01 · Cerro San José",
            radio: "Radio Link · 6 GHz Upper"
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
            "AtmosLink UI v3",
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

        refresh();

        setInterval(
            refresh,
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
