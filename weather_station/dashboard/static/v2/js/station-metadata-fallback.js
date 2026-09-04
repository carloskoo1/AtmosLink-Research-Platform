/* =========================================================
   ATMOSLINK STATION METADATA FALLBACK

   Corrige únicamente metadatos visuales ausentes.

   CU01:
   - Rol AP
   - Backend 5.1.1

   SJ01 conserva los metadatos proporcionados por la API.
   ========================================================= */

(() => {
  "use strict";

  let applying = false;
  let timer = null;


  const STATION_METADATA = {
    CU01: {
      role: "AP",
      systemLabel: "Backend 5.1.1",
    },
  };


  function normalize(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim();
  }


  function stationSelector() {
    return (
      document.getElementById("stationSelector") ||
      document.querySelector(
        'select[name="station_id"]'
      ) ||
      document.querySelector(
        'select[id*="station"]'
      )
    );
  }


  function selectedStationId() {
    const selector =
      stationSelector();

    return normalize(
      selector?.value || ""
    ).toUpperCase();
  }


  function leafElements(root = document) {
    return Array.from(
      root.querySelectorAll("*")
    ).filter(
      element =>
        element.children.length === 0
    );
  }


  function findHero() {
    const title =
      Array.from(
        document.querySelectorAll("h1")
      ).find(
        element =>
          normalize(
            element.textContent
          ) ===
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
        normalize(
          current.textContent
        );

      if (
        content.includes(
          "AtmosLink Scientific Control Center"
        ) &&
        (
          content.includes(
            "Operational System Health"
          ) ||
          content.includes(
            "Operational Scientific Health"
          )
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


  function replaceRole(hero, role) {
    const candidates =
      leafElements(hero);

    const roleElement =
      candidates.find(
        element =>
          /^Rol\s*(—|-|UNKNOWN)?$/i.test(
            normalize(
              element.textContent
            )
          )
      );

    if (roleElement) {
      roleElement.textContent =
        `Rol ${role}`;

      roleElement.dataset
        .atmoslinkMetadataFixed =
        "role";
    }
  }


  function replaceSystemLabel(
    hero,
    systemLabel
  ) {
    const candidates =
      leafElements(hero);

    const systemElement =
      candidates.find(
        element => {
          const content =
            normalize(
              element.textContent
            );

          return (
            /^Firmware\s+UNKNOWN/i.test(
              content
            ) ||
            /^Build\s+UNKNOWN/i.test(
              content
            ) ||
            /UNKNOWN\s*·\s*Build\s+UNKNOWN/i.test(
              content
            ) ||
            content ===
              "UNKNOWN"
          );
        }
      );

    if (systemElement) {
      systemElement.textContent =
        systemLabel;

      systemElement.dataset
        .atmoslinkMetadataFixed =
        "system";
    }
  }


  function applyMetadataFallback() {
    if (applying) {
      return;
    }

    applying = true;

    try {
      const stationId =
        selectedStationId();

      const metadata =
        STATION_METADATA[
          stationId
        ];

      if (!metadata) {
        return;
      }

      const hero =
        findHero();

      if (!hero) {
        return;
      }

      replaceRole(
        hero,
        metadata.role
      );

      replaceSystemLabel(
        hero,
        metadata.systemLabel
      );

    } finally {
      applying = false;
    }
  }


  function scheduleApply() {
    window.clearTimeout(timer);

    timer =
      window.setTimeout(
        applyMetadataFallback,
        150
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
            scheduleApply();
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
      applyMetadataFallback();

      window.setTimeout(
        applyMetadataFallback,
        700
      );

      window.setTimeout(
        applyMetadataFallback,
        1800
      );

      window.setTimeout(
        applyMetadataFallback,
        3500
      );

      stationSelector()
        ?.addEventListener(
          "change",
          () => {
            window.setTimeout(
              applyMetadataFallback,
              500
            );
          }
        );

      startObserver();
    }
  );


  window.addEventListener(
    "atmoslink:station-updated",
    scheduleApply
  );


  window.addEventListener(
    "focus",
    scheduleApply
  );


  window.setInterval(
    applyMetadataFallback,
    30000
  );


  window.AtmosLinkStationMetadata = {
    refresh:
      applyMetadataFallback,
  };
})();
