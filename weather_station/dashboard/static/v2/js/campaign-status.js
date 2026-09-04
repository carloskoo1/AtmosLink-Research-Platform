/* =========================================================
   ATMOSLINK SCIENTIFIC CAMPAIGN STATUS V2.5

   Funciones:
   - Separa salud operativa de madurez científica.
   - Calcula Scientific Confidence.
   - Determina estado global de campaña.
   - Construye hitos estadísticos automáticos.
   - Mantiene SJ01 excluida mientras esté en laboratorio.
   ========================================================= */

(() => {
  "use strict";

  const VARIABLE =
    "temperature";

  const REFRESH_INTERVAL_MS =
    5 * 60 * 1000;

  const THRESHOLDS = [
    {
      key: "INSUFFICIENT",
      minimum: 0,
      label: "INSUFICIENTE",
    },
    {
      key: "PRELIMINARY",
      minimum: 24,
      label: "PRELIMINAR",
    },
    {
      key: "INTERMEDIATE",
      minimum: 168,
      label: "INTERMEDIA",
    },
    {
      key: "MATURE",
      minimum: 720,
      label: "MADURA",
    },
  ];


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


  function deploymentMode() {
    return String(
      document.documentElement
        .dataset.deploymentMode ||
      ""
    )
      .trim()
      .toUpperCase();
  }


  function finiteNumber(value) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return null;
    }

    const number =
      Number(value);

    return Number.isFinite(number)
      ? number
      : null;
  }


  function parseTimestamp(value) {
    const timestamp =
      new Date(value);

    return Number.isNaN(
      timestamp.getTime()
    )
      ? null
      : timestamp;
  }


  function formatDate(value) {
    const timestamp =
      value instanceof Date
        ? value
        : parseTimestamp(value);

    if (!timestamp) {
      return "Pendiente";
    }

    return new Intl.DateTimeFormat(
      "es-PE",
      {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      }
    ).format(timestamp);
  }


  function formatDateTime(value) {
    const timestamp =
      value instanceof Date
        ? value
        : parseTimestamp(value);

    if (!timestamp) {
      return "No disponible";
    }

    return new Intl.DateTimeFormat(
      "es-PE",
      {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }
    ).format(timestamp);
  }


  function validPair(
    record,
    source
  ) {
    return (
      finiteNumber(
        record?.observed
      ) !== null &&
      finiteNumber(
        record?.[source]
      ) !== null
    );
  }


  function effectiveRecords(records) {
    return records.filter(
      record =>
        validPair(
          record,
          "era5"
        ) &&
        validPair(
          record,
          "nasa"
        )
    );
  }


  function classifyStatus(pairs) {
    if (pairs >= 720) {
      return {
        key: "MATURE",
        label: "MADURA",
        minimum: 720,
        next: null,
      };
    }

    if (pairs >= 168) {
      return {
        key: "INTERMEDIATE",
        label: "INTERMEDIA",
        minimum: 168,
        next: 720,
      };
    }

    if (pairs >= 24) {
      return {
        key: "PRELIMINARY",
        label: "PRELIMINAR",
        minimum: 24,
        next: 168,
      };
    }

    return {
      key: "INSUFFICIENT",
      label: "INSUFICIENTE",
      minimum: 0,
      next: 24,
    };
  }


  function calculateContinuity(
    records
  ) {
    const timestamps =
      records
        .map(
          record =>
            parseTimestamp(
              record.timestamp
            )
        )
        .filter(Boolean)
        .sort(
          (a, b) =>
            a.getTime() -
            b.getTime()
        );

    if (
      timestamps.length < 2
    ) {
      return 0;
    }

    const first =
      timestamps[0];

    const last =
      timestamps[
        timestamps.length - 1
      ];

    const expectedHours =
      Math.max(
        1,
        Math.round(
          (
            last.getTime() -
            first.getTime()
          ) /
          3600000
        ) + 1
      );

    return Math.min(
      1,
      timestamps.length /
      expectedHours
    );
  }


  function calculateModelCoverage(
    records
  ) {
    if (!records.length) {
      return 0;
    }

    const complete =
      records.filter(
        record =>
          validPair(
            record,
            "era5"
          ) &&
          validPair(
            record,
            "nasa"
          )
      ).length;

    return Math.min(
      1,
      complete /
      records.length
    );
  }


  function calculateConfidence(
    effectivePairs,
    continuity,
    modelCoverage
  ) {
    /*
     * Índice compuesto:
     *
     * 50 % cobertura temporal
     * 30 % continuidad
     * 20 % cobertura simultánea de modelos
     *
     * La cobertura alcanza su máximo a las 720 horas.
     */
    const coverageScore =
      Math.min(
        1,
        effectivePairs / 720
      );

    return Math.round(
      (
        coverageScore * 0.50 +
        continuity * 0.30 +
        modelCoverage * 0.20
      ) * 100
    );
  }


  function milestoneDate(
    records,
    threshold
  ) {
    if (
      records.length <
      threshold
    ) {
      return null;
    }

    const record =
      records[
        threshold - 1
      ];

    return parseTimestamp(
      record.timestamp
    );
  }


  function buildMilestones(
    records
  ) {
    const firstRecord =
      records[0] || null;

    return [
      {
        label:
          "Inicio de pares comparables",
        target:
          1,
        achieved:
          records.length >= 1,
        date:
          firstRecord
            ? parseTimestamp(
                firstRecord.timestamp
              )
            : null,
        description:
          "Primer registro con observación local, ERA5-Land y NASA POWER.",
      },

      {
        label:
          "Cobertura mínima",
        target:
          24,
        achieved:
          records.length >= 24,
        date:
          milestoneDate(
            records,
            24
          ),
        description:
          "Se completaron 24 pares horarios comparables.",
      },

      {
        label:
          "Estado preliminar",
        target:
          24,
        achieved:
          records.length >= 24,
        date:
          milestoneDate(
            records,
            24
          ),
        description:
          "La campaña alcanzó el nivel estadístico PRELIMINAR.",
      },

      {
        label:
          "Estado intermedio",
        target:
          168,
        achieved:
          records.length >= 168,
        date:
          milestoneDate(
            records,
            168
          ),
        description:
          "Se completó una semana de pares horarios comparables.",
      },

      {
        label:
          "Estado maduro",
        target:
          720,
        achieved:
          records.length >= 720,
        date:
          milestoneDate(
            records,
            720
          ),
        description:
          "Se completaron 30 días de pares horarios comparables.",
      },
    ];
  }


  function ensurePanel() {
    let panel =
      byId(
        "scientificCampaignStatus"
      );

    if (panel) {
      return panel;
    }

    panel =
      document.createElement(
        "section"
      );

    panel.id =
      "scientificCampaignStatus";

    panel.className =
      "atl-campaign-status";

    const maturityPanel =
      byId(
        "scientificValidationMaturity"
      );

    const readinessPanel =
      byId(
        "atmoslinkScientificReadiness"
      );

    if (maturityPanel) {
      maturityPanel
        .insertAdjacentElement(
          "afterend",
          panel
        );

      return panel;
    }

    if (readinessPanel) {
      readinessPanel
        .insertAdjacentElement(
          "afterend",
          panel
        );

      return panel;
    }

    const main =
      document.querySelector(
        "main"
      );

    main?.prepend(panel);

    return panel;
  }


  function correctOperationalHealthLabel() {
    document
      .querySelectorAll(
        "*"
      )
      .forEach(element => {
        if (
          element.children.length >
          0
        ) {
          return;
        }

        const text =
          element.textContent
            ?.trim();

        if (
          text ===
          "Operational Scientific Health"
        ) {
          element.textContent =
            "Operational System Health";
        }
      });
  }


  function milestonesHtml(
    milestones
  ) {
    return milestones.map(
      (milestone, index) => {
        const stateClass =
          milestone.achieved
            ? "atl-campaign-milestone--achieved"
            : "atl-campaign-milestone--pending";

        return `
          <article class="atl-campaign-milestone ${stateClass}">

            <div class="atl-campaign-milestone__marker">
              ${
                milestone.achieved
                  ? "✓"
                  : index + 1
              }
            </div>

            <div class="atl-campaign-milestone__content">

              <span class="atl-campaign-milestone__date">
                ${
                  milestone.achieved
                    ? formatDate(
                        milestone.date
                      )
                    : "Pendiente"
                }
              </span>

              <strong>
                ${milestone.label}
              </strong>

              <p>
                ${milestone.description}
              </p>

            </div>

          </article>
        `;
      }
    ).join("");
  }


  function renderExcluded(
    stationId
  ) {
    const panel =
      ensurePanel();

    if (!panel) {
      return;
    }

    panel.dataset.status =
      "EXCLUDED";

    panel.innerHTML = `
      <div class="atl-campaign-status__header">

        <div>
          <span class="atl-campaign-status__eyebrow">
            SCIENTIFIC CAMPAIGN STATUS
          </span>

          <h2>
            ${stationId} · Campaña científica
          </h2>

          <p>
            La estación permanece en laboratorio.
            El estado científico global se habilitará
            después de la instalación física en Cerro
            San José y de la generación de pares
            horarios comparables.
          </p>
        </div>

        <div class="atl-campaign-status__summary">

          <strong>
            EXCLUIDA
          </strong>

          <span>
            Scientific Confidence: 0%
          </span>

        </div>

      </div>

      <div class="atl-campaign-confidence">

        <div class="atl-campaign-confidence__labels">
          <span>Scientific Confidence</span>
          <strong>0%</strong>
        </div>

        <div class="atl-campaign-confidence__track">
          <span style="width: 0%"></span>
        </div>

      </div>

      <div class="atl-campaign-status__grid">

        <div>
          <strong>Estado estadístico</strong>
          <span>NO HABILITADO</span>
        </div>

        <div>
          <strong>Pares efectivos</strong>
          <span>0 horas</span>
        </div>

        <div>
          <strong>Continuidad</strong>
          <span>No aplica</span>
        </div>

        <div>
          <strong>Ubicación científica</strong>
          <span>Laboratorio</span>
        </div>

      </div>

      <div class="atl-campaign-status__notice">
        SJ01 no debe incorporarse todavía a análisis
        espaciales ni a inferencias sobre Cerro San José.
      </div>
    `;
  }


  function renderCampaign(
    stationId,
    records
  ) {
    const panel =
      ensurePanel();

    if (!panel) {
      return;
    }

    const effective =
      effectiveRecords(
        records
      )
      .sort(
        (a, b) => {
          const left =
            parseTimestamp(
              a.timestamp
            );

          const right =
            parseTimestamp(
              b.timestamp
            );

          return (
            left?.getTime() || 0
          ) - (
            right?.getTime() || 0
          );
        }
      );

    const pairs =
      effective.length;

    const status =
      classifyStatus(
        pairs
      );

    const continuity =
      calculateContinuity(
        effective
      );

    const modelCoverage =
      calculateModelCoverage(
        records
      );

    const confidence =
      calculateConfidence(
        pairs,
        continuity,
        modelCoverage
      );

    const milestones =
      buildMilestones(
        effective
      );

    const firstTimestamp =
      effective[0]
        ?.timestamp ||
      null;

    const lastTimestamp =
      effective[
        effective.length - 1
      ]?.timestamp ||
      null;

    const days =
      pairs / 24;

    const remaining =
      status.next === null
        ? 0
        : Math.max(
            0,
            status.next -
            pairs
          );

    panel.dataset.status =
      status.key;

    panel.innerHTML = `
      <div class="atl-campaign-status__header">

        <div>
          <span class="atl-campaign-status__eyebrow">
            SCIENTIFIC CAMPAIGN STATUS
          </span>

          <h2>
            ${stationId} · Estado científico global
          </h2>

          <p>
            La clasificación combina cobertura temporal,
            continuidad de la serie y disponibilidad
            simultánea de ERA5-Land y NASA POWER.
          </p>
        </div>

        <div class="atl-campaign-status__summary">

          <strong>
            ${status.label}
          </strong>

          <span>
            Scientific Confidence:
            ${confidence}%
          </span>

        </div>

      </div>

      <div class="atl-campaign-confidence">

        <div class="atl-campaign-confidence__labels">
          <span>
            Scientific Confidence
          </span>

          <strong>
            ${confidence}%
          </strong>
        </div>

        <div class="atl-campaign-confidence__track">
          <span style="width: ${confidence}%"></span>
        </div>

      </div>

      <div class="atl-campaign-status__grid">

        <div>
          <strong>Madurez estadística</strong>
          <span>${status.label}</span>
        </div>

        <div>
          <strong>Pares efectivos</strong>
          <span>
            ${pairs} h ·
            ${days.toFixed(1)} días
          </span>
        </div>

        <div>
          <strong>Continuidad temporal</strong>
          <span>
            ${(continuity * 100).toFixed(1)}%
          </span>
        </div>

        <div>
          <strong>Cobertura de modelos</strong>
          <span>
            ${(modelCoverage * 100).toFixed(1)}%
          </span>
        </div>

        <div>
          <strong>Inicio comparable</strong>
          <span>
            ${formatDateTime(
              firstTimestamp
            )}
          </span>
        </div>

        <div>
          <strong>Último par</strong>
          <span>
            ${formatDateTime(
              lastTimestamp
            )}
          </span>
        </div>

        <div>
          <strong>Siguiente nivel</strong>
          <span>
            ${
              status.next === null
                ? "Nivel máximo alcanzado"
                : `${remaining} pares restantes`
            }
          </span>
        </div>

        <div>
          <strong>Criterio de madurez</strong>
          <span>
            720 h para campaña madura
          </span>
        </div>

      </div>

      <div class="atl-campaign-milestones">

        <div class="atl-campaign-milestones__header">

          <div>
            <span class="atl-campaign-status__eyebrow">
              AUTOMATED SCIENTIFIC TRACEABILITY
            </span>

            <h3>
              Hitos estadísticos de campaña
            </h3>
          </div>

          <span class="atl-campaign-milestones__badge">
            ${pairs} pares
          </span>

        </div>

        <div class="atl-campaign-milestones__list">
          ${milestonesHtml(
            milestones
          )}
        </div>

      </div>
    `;
  }


  function renderError(
    stationId,
    message
  ) {
    const panel =
      ensurePanel();

    if (!panel) {
      return;
    }

    panel.dataset.status =
      "ERROR";

    panel.innerHTML = `
      <div class="atl-campaign-status__header">

        <div>
          <span class="atl-campaign-status__eyebrow">
            SCIENTIFIC CAMPAIGN STATUS
          </span>

          <h2>
            ${stationId} · Estado no disponible
          </h2>

          <p>
            No se pudo calcular el estado global:
            ${message}
          </p>
        </div>

        <div class="atl-campaign-status__summary">
          <strong>ERROR</strong>
          <span>Reintento automático</span>
        </div>

      </div>
    `;
  }


  async function loadCampaignStatus() {
    correctOperationalHealthLabel();

    const stationId =
      selectedStationId();

    if (
      deploymentMode() ===
      "LABORATORY"
    ) {
      renderExcluded(
        stationId
      );

      return;
    }

    try {
      const response =
        await fetch(
          `/api/scientific/hourly`
          + `?station_id=${encodeURIComponent(
            stationId
          )}`
          + `&variable=${encodeURIComponent(
            VARIABLE
          )}`,
          {
            cache: "no-store",
            headers: {
              Accept:
                "application/json",
            },
          }
        );

      const payload =
        await response.json();

      if (
        payload.status ===
        "excluded"
      ) {
        renderExcluded(
          stationId
        );

        return;
      }

      if (
        !response.ok ||
        payload.status !==
        "ok"
      ) {
        throw new Error(
          payload.error ||
          `HTTP ${response.status}`
        );
      }

      const records =
        Array.isArray(
          payload.records
        )
          ? payload.records
          : [];

      renderCampaign(
        stationId,
        records
      );

    } catch (error) {
      console.error(
        "AtmosLink campaign status:",
        error
      );

      renderError(
        stationId,
        error.message ||
        "Error desconocido"
      );
    }
  }


  function scheduleRefresh() {
    window.clearTimeout(
      scheduleRefresh.timer
    );

    scheduleRefresh.timer =
      window.setTimeout(
        loadCampaignStatus,
        150
      );
  }


  document.addEventListener(
    "DOMContentLoaded",
    () => {
      window.setTimeout(
        loadCampaignStatus,
        500
      );

      byId("stationSelector")
        ?.addEventListener(
          "change",
          scheduleRefresh
        );

      window.setInterval(
        loadCampaignStatus,
        REFRESH_INTERVAL_MS
      );
    }
  );


  window.addEventListener(
    "atmoslink:deployment-mode",
    scheduleRefresh
  );


  window.addEventListener(
    "focus",
    scheduleRefresh
  );


  window.AtmosLinkCampaignStatus = {
    refresh:
      loadCampaignStatus,
  };
})();


/* =========================================================
   ATMOSLINK_ZERO_PAIRS_DATE_GUARD_V1
   Evita mostrar 1969/1970 cuando no existen pares.
   ========================================================= */
(() => {
  "use strict";

  let atlZeroDateRunning = false;
  let atlZeroDateTimer = null;

  function atlZeroDateLeaves(root) {
    return Array.from(
      root.querySelectorAll(
        "div, span, strong, small, p"
      )
    ).filter(
      element =>
        element.children.length === 0
    );
  }

  function atlZeroDateSelectedStation() {
    return (
      document.getElementById(
        "stationSelector"
      )?.value || ""
    ).toUpperCase();
  }

  function atlZeroDateFindCampaign() {
    const title =
      atlZeroDateLeaves(
        document.body
      ).find(
        element =>
          element.textContent.trim() ===
          "SCIENTIFIC CAMPAIGN STATUS"
      );

    if (!title) {
      return null;
    }

    let current = title;

    while (
      current &&
      current !== document.body
    ) {
      const content =
        current.textContent || "";

      if (
        content.includes(
          "Inicio comparable"
        ) &&
        content.includes(
          "Último par"
        ) &&
        content.includes(
          "Pares efectivos"
        )
      ) {
        return current;
      }

      current = current.parentElement;
    }

    return null;
  }

  function atlZeroDateSetCard(
    panel,
    label,
    value
  ) {
    const labelElement =
      atlZeroDateLeaves(panel)
        .find(
          element =>
            element.textContent.trim() ===
            label
        );

    const card =
      labelElement?.parentElement;

    if (!card) {
      return;
    }

    const candidates =
      atlZeroDateLeaves(card)
        .filter(
          element =>
            element !== labelElement &&
            element.textContent.trim()
        );

    if (candidates.length) {
      candidates[
        candidates.length - 1
      ].textContent = value;
    }
  }

  function atlZeroDateApply() {
    if (
      atlZeroDateRunning ||
      atlZeroDateSelectedStation()
        !== "SJ01"
    ) {
      return;
    }

    const panel =
      atlZeroDateFindCampaign();

    if (!panel) {
      return;
    }

    const content =
      panel.textContent || "";

    const zeroPairs =
      content.includes("0 pares") ||
      content.includes("0 h · 0.0 días") ||
      content.includes("0 pares efectivos");

    if (!zeroPairs) {
      return;
    }

    atlZeroDateRunning = true;

    try {
      atlZeroDateSetCard(
        panel,
        "Inicio comparable",
        "—"
      );

      atlZeroDateSetCard(
        panel,
        "Último par",
        "—"
      );

      atlZeroDateLeaves(panel)
        .forEach(
          element => {
            const value =
              element.textContent.trim();

            if (
              value.includes("1969") ||
              value.includes("1970")
            ) {
              element.textContent = "—";
            }
          }
        );
    } finally {
      atlZeroDateRunning = false;
    }
  }

  function atlZeroDateSchedule() {
    window.clearTimeout(
      atlZeroDateTimer
    );

    atlZeroDateTimer =
      window.setTimeout(
        atlZeroDateApply,
        100
      );
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      atlZeroDateSchedule();

      document
        .getElementById(
          "stationSelector"
        )
        ?.addEventListener(
          "change",
          atlZeroDateSchedule
        );

      const observer =
        new MutationObserver(
          atlZeroDateSchedule
        );

      observer.observe(
        document.body,
        {
          childList: true,
          subtree: true,
          characterData: true,
        }
      );

      window.setInterval(
        atlZeroDateApply,
        5000
      );
    }
  );

  console.info(
    "ATMOSLINK_ZERO_PAIRS_DATE_GUARD_V1"
  );
})();
