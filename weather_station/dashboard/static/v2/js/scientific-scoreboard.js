/* =========================================================
   ATMOSLINK SCIENTIFIC SCOREBOARD

   Panel científico resumido y dinámico.

   No modifica:
   - Base de datos.
   - APIs.
   - Cálculos estadísticos.
   - Adquisición instrumental.
   ========================================================= */

(() => {
  "use strict";

  let applying = false;
  let observerTimer = null;


  function normalize(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim();
  }


  function byId(id) {
    return document.getElementById(id);
  }


  function stationSelector() {
    return (
      byId("stationSelector") ||
      document.querySelector(
        'select[name="station_id"]'
      ) ||
      document.querySelector(
        'select[id*="station"]'
      )
    );
  }


  function selectedStationId() {
    return normalize(
      stationSelector()?.value ||
      "CU01"
    ).toUpperCase();
  }


  function selectedStationLabel() {
    const selector =
      stationSelector();

    if (!selector) {
      return selectedStationId();
    }

    return normalize(
      selector.options[
        selector.selectedIndex
      ]?.textContent ||
      selectedStationId()
    );
  }


  function leafElements(root = document) {
    return Array.from(
      root.querySelectorAll("*")
    ).filter(
      element =>
        element.children.length === 0
    );
  }


  function findExactText(
    root,
    expected
  ) {
    const target =
      normalize(expected);

    return (
      leafElements(root).find(
        element =>
          normalize(
            element.textContent
          ) === target
      ) ||
      null
    );
  }


  function findValueByLabel(
    root,
    label
  ) {
    const labelElement =
      findExactText(
        root,
        label
      );

    if (!labelElement) {
      return null;
    }

    let container =
      labelElement.parentElement;

    for (
      let depth = 0;
      depth < 4;
      depth += 1
    ) {
      if (!container) {
        break;
      }

      const values =
        leafElements(container)
          .map(
            element =>
              normalize(
                element.textContent
              )
          )
          .filter(
            value =>
              value &&
              value !== label
          );

      if (values.length) {
        return values[
          values.length - 1
        ];
      }

      container =
        container.parentElement;
    }

    return null;
  }


  function scientificRoot() {
    return byId(
      "atmoslinkScientificIntelligence"
    );
  }


  function readinessRoot() {
    const heading =
      Array.from(
        document.querySelectorAll(
          "h1, h2, h3"
        )
      ).find(
        element =>
          /Scientific Readiness Level/i.test(
            normalize(
              element.previousElementSibling
                ?.textContent
            )
          ) ||
          /Madurez estadística/i.test(
            normalize(
              element.textContent
            )
          )
      );

    if (!heading) {
      return null;
    }

    return (
      heading.closest(
        "section, article"
      ) ||
      heading.parentElement
    );
  }


  function parseScore(root) {
    const strong =
      root?.querySelector(
        ".atl-scientific-index__value strong"
      );

    if (strong) {
      const parsed =
        Number(
          normalize(
            strong.textContent
          )
        );

      if (
        Number.isFinite(parsed)
      ) {
        return parsed;
      }
    }

    const text =
      normalize(
        root?.textContent
      );

    const match =
      text.match(
        /(\d{1,3})\s*\/\s*100/
      );

    return match
      ? Number(match[1])
      : null;
  }


  function parseValidationStatus() {
    /*
     * Dictamen científico basado en la estación
     * seleccionada y sus pares efectivos.
     */

    const stationId =
      selectedStationId();

    /*
     * SJ01 permanece excluida mientras la estación
     * se encuentre formalmente en laboratorio.
     */
    if (stationId === "SJ01") {
      return {
        label:
          "EXCLUIDA",

        tone:
          "excluded",

        detail:
          "Estación en laboratorio",

        comparablePairs:
          0,
      };
    }

    const root =
      scientificRoot();

    const pairsText =
      normalize(
        findValueByLabel(
          root,
          "Pares efectivos"
        ) || "0"
      );

    const pairsMatch =
      pairsText.match(
        /\d[\d.,]*/
      );

    const comparablePairs =
      pairsMatch
        ? Number(
            pairsMatch[0].replace(
              /\D/g,
              ""
            )
          )
        : 0;

    if (comparablePairs <= 0) {
      return {
        label:
          "SIN COBERTURA",

        tone:
          "pending",

        detail:
          "Esperando pares comparables",

        comparablePairs:
          0,
      };
    }

    if (comparablePairs < 168) {
      return {
        label:
          "PRELIMINAR",

        tone:
          "preliminary",

        detail:
          `${comparablePairs} pares comparables`,

        comparablePairs,
      };
    }

    if (comparablePairs < 720) {
      return {
        label:
          "INTERMEDIA",

        tone:
          "intermediate",

        detail:
          `${comparablePairs} pares comparables`,

        comparablePairs,
      };
    }

    return {
      label:
        "MADURA",

      tone:
        "mature",

      detail:
        `${comparablePairs} pares comparables`,

      comparablePairs,
    };
  }


  function normalizeMetric(
    value,
    fallback = "—"
  ) {
    const result =
      normalize(value);

    if (
      !result ||
      result === "null" ||
      result === "undefined"
    ) {
      return fallback;
    }

    return result;
  }


  function buildMetrics() {
    const root =
      scientificRoot();

    const validation =
      parseValidationStatus();

    const score =
      parseScore(root);

    const maturity =
      normalizeMetric(
        findValueByLabel(
          root,
          "Madurez"
        ),
        validation.label
      );

    const pairs =
      normalizeMetric(
        findValueByLabel(
          root,
          "Pares efectivos"
        ),
        selectedStationId() === "SJ01"
          ? "0"
          : "—"
      );

    const continuity =
      normalizeMetric(
        findValueByLabel(
          root,
          "Continuidad"
        ),
        selectedStationId() === "SJ01"
          ? "0 %"
          : "—"
      );

    const publication =
      normalizeMetric(
        findValueByLabel(
          root,
          "Preparación de publicación"
        ),
        selectedStationId() === "SJ01"
          ? "0/6"
          : "—"
      );

    const readinessText =
      normalize(
        readinessRoot()?.textContent
      );

    const srlMatch =
      readinessText.match(
        /SRL\s*(\d+)\s*\/\s*(\d+)/i
      );

    const srl =
      srlMatch
        ? `${srlMatch[1]}/${srlMatch[2]}`
        : "—";

    return {
      stationId:
        selectedStationId(),

      stationLabel:
        selectedStationLabel(),

      score:
        score !== null
          ? `${score}/100`
          : "—",

      maturity,
      pairs,
      continuity,
      publication,
      srl,
      validation,
    };
  }


  function metricCard(
    label,
    value,
    detail,
    icon,
    tone = ""
  ) {
    return `
      <article class="
        atl-scientific-scoreboard__metric
        ${tone
          ? `atl-scientific-scoreboard__metric--${tone}`
          : ""
        }
      ">

        <div class="atl-scientific-scoreboard__metric-icon">
          ${icon}
        </div>

        <div class="atl-scientific-scoreboard__metric-content">

          <span>
            ${label}
          </span>

          <strong>
            ${value}
          </strong>

          <small>
            ${detail}
          </small>

        </div>

      </article>
    `;
  }


  function findInsertionPoint() {
    const readiness =
      readinessRoot();

    if (readiness) {
      return {
        element:
          readiness,

        position:
          "afterend",
      };
    }

    const heroTitle =
      Array.from(
        document.querySelectorAll("h1")
      ).find(
        element =>
          normalize(
            element.textContent
          ) ===
          "AtmosLink Scientific Control Center"
      );

    const hero =
      heroTitle?.closest(
        "section, article"
      );

    if (hero) {
      return {
        element:
          hero,

        position:
          "beforebegin",
      };
    }

    return null;
  }


  function renderScoreboard() {
    if (applying) {
      return;
    }

    applying = true;

    try {
      const metrics =
        buildMetrics();

      let scoreboard =
        byId(
          "atmoslinkScientificScoreboard"
        );

      if (!scoreboard) {
        scoreboard =
          document.createElement(
            "section"
          );

        scoreboard.id =
          "atmoslinkScientificScoreboard";

        scoreboard.className =
          "atl-scientific-scoreboard";

        const insertion =
          findInsertionPoint();

        if (!insertion) {
          return;
        }

        insertion.element
          .insertAdjacentElement(
            insertion.position,
            scoreboard
          );
      }

      scoreboard.dataset.stationId =
        metrics.stationId;

      scoreboard.dataset.validationTone =
        metrics.validation.tone;

      scoreboard.innerHTML = `
        <div class="atl-scientific-scoreboard__header">

          <div>

            <span class="atl-scientific-scoreboard__eyebrow">
              ATMOSLINK SCIENTIFIC SCOREBOARD
            </span>

            <h2>
              ${metrics.stationLabel}
            </h2>

            <p>
              Síntesis ejecutiva del estado científico,
              madurez estadística y preparación de publicación.
            </p>

          </div>

          <div class="
            atl-scientific-scoreboard__state
            atl-scientific-scoreboard__state--${metrics.validation.tone}
          ">

            <span>
              ESTADO CIENTÍFICO
            </span>

            <strong>
              ${metrics.validation.label}
            </strong>

            <small>
              ${metrics.validation.detail}
            </small>

          </div>

        </div>

        <div class="atl-scientific-scoreboard__metrics">

          ${metricCard(
            "Índice científico",
            metrics.score,
            "AtmosLink Scientific Index",
            "Σ",
            "index"
          )}

          ${metricCard(
            "Madurez estadística",
            metrics.maturity,
            "Nivel actual de cobertura",
            "M"
          )}

          ${metricCard(
            "Pares efectivos",
            metrics.pairs,
            "Observación–modelo",
            "N"
          )}

          ${metricCard(
            "Continuidad temporal",
            metrics.continuity,
            "Serie horaria válida",
            "T"
          )}

          ${metricCard(
            "Preparación de publicación",
            metrics.publication,
            "Criterios completados",
            "P"
          )}

          ${metricCard(
            "Scientific Readiness",
            metrics.srl,
            "Nivel SRL de campaña",
            "R"
          )}

        </div>

        <div class="atl-scientific-scoreboard__footer">

          <div>
            <span>
              Modo
            </span>

            <strong>
              ${
                metrics.stationId === "SJ01"
                  ? "LABORATORY"
                  : "FIELD"
              }
            </strong>
          </div>

          <div>
            <span>
              Comparación espacial
            </span>

            <strong>
              ${
                metrics.stationId === "SJ01"
                  ? "NO HABILITADA"
                  : "HABILITADA"
              }
            </strong>
          </div>

          <div>
            <span>
              Validación de modelos
            </span>

            <strong>
              ${
                metrics.stationId === "SJ01"
                  ? "EXCLUIDA"
                  : "CONDICIONADA A COBERTURA"
              }
            </strong>
          </div>

        </div>
      `;

    } finally {
      applying = false;
    }
  }


  function scheduleRender() {
    window.clearTimeout(
      observerTimer
    );

    observerTimer =
      window.setTimeout(
        renderScoreboard,
        250
      );
  }


  function startObserver() {
    const observer =
      new MutationObserver(
        mutations => {
          const relevant =
            mutations.some(
              mutation =>
                mutation.addedNodes.length ||
                mutation.removedNodes.length ||
                mutation.type ===
                  "characterData"
            );

          if (relevant) {
            scheduleRender();
          }
        }
      );

    observer.observe(
      document.body,
      {
        childList: true,
        subtree: true,
        characterData: true,
      }
    );
  }


  document.addEventListener(
    "DOMContentLoaded",
    () => {
      renderScoreboard();

      window.setTimeout(
        renderScoreboard,
        800
      );

      window.setTimeout(
        renderScoreboard,
        1800
      );

      window.setTimeout(
        renderScoreboard,
        3500
      );

      stationSelector()
        ?.addEventListener(
          "change",
          () => {
            window.setTimeout(
              renderScoreboard,
              600
            );
          }
        );

      startObserver();
    }
  );


  window.addEventListener(
    "focus",
    scheduleRender
  );


  window.addEventListener(
    "atmoslink:station-updated",
    scheduleRender
  );


  window.addEventListener(
    "atmoslink:deployment-mode",
    scheduleRender
  );


  window.setInterval(
    renderScoreboard,
    30000
  );


  window.AtmosLinkScientificScoreboard = {
    refresh:
      renderScoreboard,
  };
})();
