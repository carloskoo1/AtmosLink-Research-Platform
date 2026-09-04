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


    function panelHTML(
        stationId,
        latest,
        scientific
    ) {
        const era5 =
            getModelBranch(
                latest,
                scientific,
                "era5"
            );

        const nasa =
            getModelBranch(
                latest,
                scientific,
                "nasa"
            );

        const era5OK =
            sourceAvailable(era5);

        const nasaOK =
            sourceAvailable(nasa);

        const rows =
            variables.map(
                variable => {

                    const observed =
                        localValue(
                            latest,
                            variable.local
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

        const availableCount =
            Number(era5OK) +
            Number(nasaOK);

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
                        ${era5OK ? "ok" : "pending"}
                    ">
                        ERA5-LAND
                        ${era5OK ? "DISPONIBLE" : "PENDIENTE"}
                    </span>

                    <span class="
                        scientific-source-state
                        ${nasaOK ? "ok" : "pending"}
                    ">
                        NASA POWER
                        ${nasaOK ? "DISPONIBLE" : "PENDIENTE"}
                    </span>

                </div>

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
            "AtmosLink UI v3.1";

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
