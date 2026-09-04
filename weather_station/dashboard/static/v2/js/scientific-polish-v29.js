/* =========================================================
   ATMOSLINK SCIENTIFIC POLISH FINAL V2.10

   Correcciones:
   - Persistencia frente al renderizado dinámico.
   - Hero realmente compacto.
   - Índice científico circular.
   - Hallazgos y recomendaciones en tarjetas.
   - Scientific Assistant estable.
   - Botones de exportación profesionales.
   ========================================================= */

(() => {
  "use strict";

  let mutationTimer = null;
  let applying = false;


  function byId(id) {
    return document.getElementById(id);
  }


  function text(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim();
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

    if (!selector) {
      return selectedStationId();
    }

    return text(
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
    const normalized =
      text(expected);

    return leafElements(root)
      .find(
        element =>
          text(
            element.textContent
          ) === normalized
      ) || null;
  }


  function findHero() {
    const title =
      Array.from(
        document.querySelectorAll("h1")
      ).find(
        element =>
          text(element.textContent) ===
          "AtmosLink Scientific Control Center"
      );

    if (!title) {
      return null;
    }

    let current =
      title.parentElement;

    while (
      current &&
      current !== document.body
    ) {
      const content =
        text(
          current.textContent
        );

      if (
        (
          content.includes(
            "Operational System Health"
          ) ||
          content.includes(
            "Operational Scientific Health"
          )
        ) &&
        content.includes(
          "AtmosLink Scientific Control Center"
        )
      ) {
        return current;
      }

      current =
        current.parentElement;
    }

    return (
      title.closest(
        "section, article"
      ) ||
      title.parentElement
    );
  }


  function compactHero() {
    const hero =
      findHero();

    if (!hero) {
      return;
    }

    hero.classList.add(
      "atl-final-hero"
    );

    hero.style.setProperty(
      "min-height",
      "230px",
      "important"
    );

    hero.style.setProperty(
      "padding-top",
      "26px",
      "important"
    );

    hero.style.setProperty(
      "padding-bottom",
      "26px",
      "important"
    );

    hero.querySelectorAll("*")
      .forEach(
        element => {
          if (
            getComputedStyle(
              element
            ).minHeight !== "0px"
          ) {
            element.classList.add(
              "atl-final-hero-child"
            );
          }
        }
      );
  }


  function scientificRoot() {
    return byId(
      "atmoslinkScientificIntelligence"
    );
  }


  function parseScore(root) {
    const strong =
      root?.querySelector(
        ".atl-scientific-index__value strong"
      );

    const score =
      Number(
        text(
          strong?.textContent
        )
      );

    return Number.isFinite(score)
      ? Math.max(
          0,
          Math.min(
            100,
            score
          )
        )
      : null;
  }


  function enhanceIndex(root) {
    const index =
      root?.querySelector(
        ".atl-scientific-index"
      );

    if (
      !index ||
      index.classList.contains(
        "atl-scientific-index--excluded"
      )
    ) {
      return;
    }

    const score =
      parseScore(root);

    if (score === null) {
      return;
    }

    index.classList.add(
      "atl-final-scientific-gauge"
    );

    index.style.setProperty(
      "--atl-final-score",
      `${score}%`
    );

    index.setAttribute(
      "aria-label",
      `AtmosLink Scientific Index ${score} de 100`
    );
  }


  function enhanceLists(root) {
    root
      ?.querySelectorAll(
        ".atl-scientific-intelligence__list"
      )
      .forEach(
        list => {
          list.classList.add(
            "atl-final-scientific-list"
          );
        }
      );

    root
      ?.querySelectorAll(
        ".atl-scientific-intelligence__item"
      )
      .forEach(
        item => {
          item.classList.add(
            "atl-final-scientific-item"
          );
        }
      );
  }


  function enhanceExports() {
    const labels = {
      csv:
        "↓ Dataset horario (.csv)",

      json:
        "↓ Trazabilidad científica (.json)",

      txt:
        "↓ Resumen de investigación (.txt)",

      print:
        "▣ Informe científico (.pdf)",
    };

    document
      .querySelectorAll(
        "[data-export-action]"
      )
      .forEach(
        button => {
          const action =
            button.dataset
              .exportAction;

          if (
            labels[action] &&
            !button.disabled
          ) {
            button.textContent =
              labels[action];
          }
        }
      );
  }


  function extractValue(
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

    const container =
      labelElement.closest(
        "div, article, section"
      );

    if (!container) {
      return null;
    }

    const candidates =
      leafElements(container)
        .map(
          element =>
            text(
              element.textContent
            )
        )
        .filter(
          value =>
            value &&
            value !== label
        );

    return (
      candidates[
        candidates.length - 1
      ] ||
      null
    );
  }


  function extractList(
    root,
    cardIndex
  ) {
    const cards =
      root.querySelectorAll(
        ".atl-scientific-intelligence__card"
      );

    const card =
      cards[cardIndex];

    if (!card) {
      return [];
    }

    return Array.from(
      card.querySelectorAll("li")
    )
      .map(
        item =>
          text(
            item.textContent
          )
      )
      .filter(Boolean)
      .slice(0, 5);
  }


  function assistantListHtml(
    items,
    icon
  ) {
    if (!items.length) {
      return `
        <li>
          <span>${icon}</span>
          <p>
            Aún no existen resultados suficientes.
          </p>
        </li>
      `;
    }

    return items.map(
      item => `
        <li>
          <span>${icon}</span>
          <p>${item}</p>
        </li>
      `
    ).join("");
  }


  function ensureAssistant(root) {
    if (!root) {
      return;
    }

    const excluded =
      root.querySelector(
        ".atl-scientific-index--excluded"
      );

    if (excluded) {
      byId(
        "atmoslinkScientificAssistant"
      )?.remove();

      return;
    }

    const score =
      parseScore(root);

    const maturity =
      extractValue(
        root,
        "Madurez"
      ) ||
      "NO DISPONIBLE";

    const pairs =
      extractValue(
        root,
        "Pares efectivos"
      ) ||
      "—";

    const continuity =
      extractValue(
        root,
        "Continuidad"
      ) ||
      "—";

    const readiness =
      extractValue(
        root,
        "Preparación de publicación"
      ) ||
      "—";

    const findings =
      extractList(
        root,
        0
      );

    const recommendations =
      extractList(
        root,
        1
      );

    let assistant =
      byId(
        "atmoslinkScientificAssistant"
      );

    if (!assistant) {
      assistant =
        document.createElement(
          "section"
        );

      assistant.id =
        "atmoslinkScientificAssistant";

      assistant.className =
        "atl-final-scientific-assistant";

      root.insertAdjacentElement(
        "afterend",
        assistant
      );
    }

    assistant.innerHTML = `
      <div class="atl-final-assistant-header">

        <div>
          <span class="atl-final-assistant-eyebrow">
            ATMOSLINK SCIENTIFIC ASSISTANT
          </span>

          <h2>
            Síntesis científica de la campaña
          </h2>

          <p>
            Interpretación automatizada del estado,
            cobertura y resultados disponibles.
          </p>
        </div>

        <div class="atl-final-assistant-score">

          <span>
            ${maturity}
          </span>

          <strong>
            ${
              score !== null
                ? `${score}/100`
                : "—"
            }
          </strong>

        </div>

      </div>

      <div class="atl-final-assistant-summary">
        La estación ${selectedStationLabel()}
        dispone actualmente de ${pairs} pares efectivos,
        presenta una continuidad de ${continuity} y mantiene
        un nivel de madurez ${maturity}. La preparación para
        publicación registra ${readiness}.
      </div>

      <div class="atl-final-assistant-columns">

        <article>
          <span class="atl-final-assistant-label">
            HALLAZGOS PRIORITARIOS
          </span>

          <ul>
            ${assistantListHtml(
              findings,
              "✓"
            )}
          </ul>
        </article>

        <article>
          <span class="atl-final-assistant-label">
            SIGUIENTES ACCIONES
          </span>

          <ul>
            ${assistantListHtml(
              recommendations,
              "→"
            )}
          </ul>
        </article>

      </div>

      <div class="atl-final-assistant-metrics">

        <div>
          <span>Estación</span>
          <strong>
            ${selectedStationId()}
          </strong>
        </div>

        <div>
          <span>Pares efectivos</span>
          <strong>
            ${pairs}
          </strong>
        </div>

        <div>
          <span>Continuidad</span>
          <strong>
            ${continuity}
          </strong>
        </div>

        <div>
          <span>Readiness</span>
          <strong>
            ${readiness}
          </strong>
        </div>

      </div>

      <p class="atl-final-assistant-note">
        Esta síntesis constituye apoyo automatizado.
        La interpretación definitiva corresponde al
        investigador.
      </p>
    `;
  }


  function applyFinalPolish() {
    if (applying) {
      return;
    }

    applying = true;

    try {
      document.body.classList.add(
        "atl-final-polish-v210"
      );

      compactHero();

      const root =
        scientificRoot();

      if (root) {
        root.classList.add(
          "atl-final-intelligence"
        );

        enhanceIndex(root);

        enhanceLists(root);

        ensureAssistant(root);
      }

      enhanceExports();

    } finally {
      applying = false;
    }
  }


  function schedulePolish() {
    window.clearTimeout(
      mutationTimer
    );

    mutationTimer =
      window.setTimeout(
        applyFinalPolish,
        180
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
                mutation.removedNodes.length
            );

          if (relevant) {
            schedulePolish();
          }
        }
      );

    observer.observe(
      document.body,
      {
        childList: true,
        subtree: true,
      }
    );
  }


  document.addEventListener(
    "DOMContentLoaded",
    () => {
      applyFinalPolish();

      window.setTimeout(
        applyFinalPolish,
        700
      );

      window.setTimeout(
        applyFinalPolish,
        1800
      );

      window.setTimeout(
        applyFinalPolish,
        3500
      );

      startObserver();

      byId("stationSelector")
        ?.addEventListener(
          "change",
          () => {
            window.setTimeout(
              applyFinalPolish,
              600
            );
          }
        );
    }
  );


  window.addEventListener(
    "focus",
    applyFinalPolish
  );


  window.addEventListener(
    "atmoslink:station-updated",
    applyFinalPolish
  );


  window.addEventListener(
    "atmoslink:deployment-mode",
    applyFinalPolish
  );


  window.setInterval(
    applyFinalPolish,
    30000
  );


  window.AtmosLinkFinalPolish = {
    refresh:
      applyFinalPolish,
  };
})();
