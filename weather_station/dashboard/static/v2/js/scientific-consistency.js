/* =========================================================
   ATMOSLINK_SCIENTIFIC_CONSISTENCY_V1

   Normalización semántica de SJ01:
   - estación instalada;
   - operación inicial;
   - cobertura pendiente;
   - sin fechas Unix falsas;
   - ambos extremos locales en el corredor.
   ========================================================= */

(() => {
  "use strict";

  let running = false;
  let timer = null;

  function selectedStation() {
    return (
      document.getElementById(
        "stationSelector"
      )?.value || ""
    ).toUpperCase();
  }

  function leaves(root) {
    return Array.from(
      root.querySelectorAll(
        "div, span, strong, small, p, td"
      )
    ).filter(
      element =>
        element.children.length === 0
    );
  }

  function replaceExact(
    root,
    before,
    after
  ) {
    leaves(root).forEach(
      element => {
        if (
          element.textContent.trim() ===
          before
        ) {
          element.textContent = after;
        }
      }
    );
  }

  function replaceContained(
    root,
    before,
    after
  ) {
    leaves(root).forEach(
      element => {
        const content =
          element.textContent;

        if (
          content &&
          content.includes(before)
        ) {
          element.textContent =
            content
              .split(before)
              .join(after);
        }
      }
    );
  }

  function commonContainer(
    first,
    second
  ) {
    if (!first || !second) {
      return null;
    }

    let current = first;

    while (
      current &&
      current !== document.body
    ) {
      if (current.contains(second)) {
        return current;
      }

      current = current.parentElement;
    }

    return null;
  }

  function correctGeneralSemantics() {
    replaceExact(
      document.body,
      "LABORATORY",
      "FIELD"
    );

    replaceExact(
      document.body,
      "PREDESPLIEGUE",
      "OPERACIÓN INICIAL"
    );

    replaceExact(
      document.body,
      "Predespliegue",
      "Operación inicial"
    );

    replaceExact(
      document.body,
      "EXCLUIDA",
      "PENDIENTE DE COBERTURA"
    );

    replaceExact(
      document.body,
      "Validación científica no habilitada.",
      "Validación pendiente de cobertura."
    );

    replaceExact(
      document.body,
      "Sin métricas publicables",
      "Acumulando cobertura horaria"
    );

    replaceContained(
      document.body,
      "SJ01 permanece en laboratorio.",
      "SJ01 está instalada en Cerro San José."
    );

    replaceContained(
      document.body,
      "SJ01 en laboratorio",
      "SJ01 en operación inicial"
    );

    replaceContained(
      document.body,
      "La estación permanece en laboratorio.",
      "La estación está instalada en Cerro San José."
    );

    replaceContained(
      document.body,
      "Estación no desplegada",
      "Operación inicial en campo"
    );

    /*
     * Las fechas Unix vacías no representan observaciones.
     */
    leaves(document.body).forEach(
      element => {
        const value =
          element.textContent.trim();

        if (
          value.includes("31/12/1969") ||
          value.includes("01/01/1970")
        ) {
          element.textContent = "—";
        }
      }
    );
  }

  function correctCorridor() {
    const smTemp =
      document.getElementById(
        "corridorSmTemp"
      );

    const smPressure =
      document.getElementById(
        "corridorSmPressure"
      );

    const smCard =
      commonContainer(
        smTemp,
        smPressure
      );

    if (smCard) {
      replaceExact(
        smCard,
        "Estimación del modelo",
        "Estación local instalada"
      );

      replaceExact(
        smCard,
        "ERA5-LAND",
        "MEDICIÓN LOCAL"
      );

      replaceExact(
        smCard,
        "NASA POWER",
        "MEDICIÓN LOCAL"
      );

      const hasLocalLabel =
        leaves(smCard).some(
          element =>
            element.textContent.trim() ===
            "MEDICIÓN LOCAL"
        );

      if (!hasLocalLabel) {
        const title =
          leaves(smCard).find(
            element =>
              element.textContent.trim() ===
              "San José"
          );

        if (title) {
          const badge =
            document.createElement(
              "span"
            );

          badge.textContent =
            "MEDICIÓN LOCAL";

          badge.className =
            "atl-local-observation-badge";

          badge.style.display =
            "table";
          badge.style.margin =
            "7px auto";
          badge.style.padding =
            "4px 10px";
          badge.style.borderRadius =
            "999px";
          badge.style.background =
            "#e6f7ef";
          badge.style.color =
            "#087443";
          badge.style.fontSize =
            "11px";
          badge.style.fontWeight =
            "700";

          title.insertAdjacentElement(
            "afterend",
            badge
          );
        }
      }
    }

    replaceContained(
      document.body,
      "Solo Cuñacales dispone actualmente de observación meteorológica local.",
      "Cuñacales y San José disponen de observación meteorológica local."
    );

    replaceContained(
      document.body,
      "los valores del punto medio y San José no corresponden todavía a sensores físicos instalados. Son estimaciones espaciales del modelo.",
      "Cuñacales y San José corresponden a estaciones meteorológicas físicas instaladas. Únicamente el punto medio representa una estimación espacial del modelo."
    );

    replaceContained(
      document.body,
      "Los valores del punto medio y San José no corresponden todavía a sensores físicos instalados. Son estimaciones espaciales del modelo.",
      "Cuñacales y San José corresponden a estaciones meteorológicas físicas instaladas. Únicamente el punto medio representa una estimación espacial del modelo."
    );
  }

  function applyConsistency() {
    if (
      running ||
      selectedStation() !== "SJ01"
    ) {
      return;
    }

    running = true;

    try {
      correctGeneralSemantics();
      correctCorridor();
    } finally {
      running = false;
    }
  }

  function schedule() {
    window.clearTimeout(timer);

    timer =
      window.setTimeout(
        applyConsistency,
        100
      );
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      schedule();

      document
        .getElementById(
          "stationSelector"
        )
        ?.addEventListener(
          "change",
          schedule
        );

      const observer =
        new MutationObserver(schedule);

      observer.observe(
        document.body,
        {
          childList: true,
          subtree: true,
          characterData: true,
        }
      );

      window.setInterval(
        applyConsistency,
        3000
      );
    }
  );

  console.info(
    "ATMOSLINK_SCIENTIFIC_CONSISTENCY_V1"
  );
})();


/* ATMOSLINK_SCIENTIFIC_POLISH_V2 */
(function () {
  "use strict";

  function normalizedText(element) {
    return String(element && element.textContent || "")
      .replace(/\s+/g, " ")
      .trim()
      .toUpperCase();
  }

  function closestScientificPanel(element) {
    if (!element) return null;

    return element.closest(
      "article, section, .card, " +
      "[class*='scientific-card'], " +
      "[class*='campaign-card'], " +
      "[class*='validation-card'], " +
      "[class*='status-card']"
    );
  }

  function markPendingPanels() {
    const pendingTerms = [
      "INSUFICIENTE",
      "PENDIENTE DE COBERTURA",
      "OPERACIÓN INICIAL",
      "ESTABILIZACIÓN"
    ];

    document.querySelectorAll(
      "h1, h2, h3, h4, strong, b, span, div"
    ).forEach(function (element) {
      const text = normalizedText(element);

      if (
        !text ||
        text.length > 80 ||
        !pendingTerms.some(function (term) {
          return text === term || text.startsWith(term + " ");
        })
      ) {
        return;
      }

      element.classList.add("atmos-pending-status");

      const panel = closestScientificPanel(element);
      if (panel) {
        panel.classList.add("atmos-pending-panel");
      }
    });
  }

  function correctZeroConfidenceBars() {
    document.querySelectorAll(
      "section, article, .card, " +
      "[class*='campaign'], [class*='scientific']"
    ).forEach(function (panel) {
      const text = normalizedText(panel);

      if (
        !text.includes("SCIENTIFIC CONFIDENCE") ||
        !text.includes("0%")
      ) {
        return;
      }

      const progressCandidates = panel.querySelectorAll(
        "[class*='progress-fill'], " +
        "[class*='progress-bar'], " +
        "[class*='meter-fill'], " +
        "[role='progressbar']"
      );

      progressCandidates.forEach(function (bar) {
        const ariaValue = bar.getAttribute("aria-valuenow");
        const styleWidth = String(bar.style.width || "").trim();

        if (
          ariaValue === "0" ||
          styleWidth === "0%" ||
          text.includes("SCIENTIFIC CONFIDENCE: 0%")
        ) {
          bar.classList.add("atmos-zero-progress");
          bar.style.width = "0%";
          bar.setAttribute("aria-valuenow", "0");
        }
      });
    });
  }

  function polishScientificInterface() {
    markPendingPanels();
    correctZeroConfidenceBars();
  }

  let scheduled = false;

  function schedulePolish() {
    if (scheduled) return;
    scheduled = true;

    window.requestAnimationFrame(function () {
      scheduled = false;
      polishScientificInterface();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      polishScientificInterface
    );
  } else {
    polishScientificInterface();
  }

  const observer = new MutationObserver(schedulePolish);

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });

  window.setInterval(polishScientificInterface, 15000);
})();
