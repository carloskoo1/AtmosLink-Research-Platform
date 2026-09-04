const API={latest:"/api/latest",health:"/api/health",core:"/api/core/status",history:"/api/history",events:"/api/events"};const REFRESH_MS=10000;const $=id=>document.getElementById(id);
function setText(id,value,fallback="—"){const el=$(id);if(!el)return;el.textContent=value===null||value===undefined||value===""?fallback:String(value)}
function number(value,fallback=null){const n=Number(value);return Number.isFinite(n)?n:fallback}
function fmt(value,digits=1){const n=number(value);if(n===null)return"—";return new Intl.NumberFormat("es-PE",{minimumFractionDigits:digits,maximumFractionDigits:digits}).format(n)}
function dateTime(value){if(!value)return"—";const normalized=String(value).includes("T")?String(value):String(value).replace(" ","T");const d=new Date(normalized);if(Number.isNaN(d.getTime()))return String(value);return new Intl.DateTimeFormat("es-PE",{dateStyle:"short",timeStyle:"medium"}).format(d)}
function upper(value,fallback="UNKNOWN"){return String(value??fallback).trim().toUpperCase()}
async function fetchJson(url){const response=await fetch(url,{headers:{Accept:"application/json"},cache:"no-store"});if(!response.ok)throw new Error(`${url}: HTTP ${response.status}`);return response.json()}
async function loadAll(){const entries=Object.entries(API);const settled=await Promise.allSettled(entries.map(([,url])=>fetchJson(url)));const payload={};const errors=[];settled.forEach((result,index)=>{const key=entries[index][0];if(result.status==="fulfilled")payload[key]=result.value;else{payload[key]=key==="history"||key==="events"?[]:{};errors.push(key)}});payload.errors=errors;return payload}
function qualityState(value){const state=upper(value);if(["OK","HEALTHY","FRESH","CURRENT","AVAILABLE"].includes(state))return{score:100,variant:"ok"};if(["WARNING","WAITING","STALE","DEGRADED","OBSERVING"].includes(state))return{score:65,variant:"warning"};if(["NOT_INSTALLED","DISABLED","NOT_ENABLED"].includes(state))return{score:0,variant:"disabled"};return{score:25,variant:"danger"}}
function renderTop(p){const{latest,health}=p;const stationId=health.station_id??latest.station_id??"—";const stationName=health.station_name??latest.station_name??"—";setText("topbarStation",`${stationId} · ${stationName}`);setText("heroStation",`${stationId} · ${stationName}`);setText("heroRole",`Rol ${latest.radio_role??"—"}`);setText("heroVersion",`Backend ${health.version??"—"}`);setText("kpiPlatform",upper(health.status));setText("kpiPlatformDetail",`Base de datos: ${upper(health.database?.status)}`);setText("kpiAcquisition",upper(health.operational_state));setText("kpiAcquisitionDetail",latest.observation_age_label??"—");const q=latest.scientific_quality??{};const ok=upper(q.era5)==="OK"&&upper(q.nasa_power)==="OK";setText("kpiSources",ok?"AVAILABLE":"DEGRADED");setText("kpiSourcesDetail",`ERA5 ${upper(q.era5)} · NASA ${upper(q.nasa_power)}`);setText("kpiRadio",upper(q.radio_link));setText("kpiRadioDetail",latest.radio_note??"—")}
function renderWeather(l){setText("temperatureValue",fmt(l.local_temp_avg_c??l.temp_avg_C));setText("humidityValue",fmt(l.local_hum_avg_pct??l.hum_avg_pct));setText("pressureValue",fmt(l.local_press_hpa??l.pres_avg_hPa));setText("dewPointValue",fmt(l.local_dew_point_c??l.dew_point_C));setText("rainHourValue",fmt(l.local_rain_1h_mm??l.rain_1h_mm,2));setText("rainTotalValue",fmt(l.local_rain_total_mm??l.rain_total_mm,2));const rainState=
l.local_rain_ok===1||l.rain_ok===1
?(Number(l.local_rain_1h_mm??l.rain_1h_mm??0)>0
?"RAIN"
:"NO RAIN")
:"UNKNOWN";

setText("rainState",rainState);setText("weatherTimestamp",dateTime(l.weather_timestamp_local??l.timestamp_local))}
function historyRows(h){if(Array.isArray(h))return h;if(Array.isArray(h?.history))return h.history;if(Array.isArray(h?.data))return h.data;if(Array.isArray(h?.rows))return h.rows;return[]}
function choose(row,keys){for(const key of keys){const v=row?.[key];if(v!==null&&v!==undefined&&Number.isFinite(Number(v)))return Number(v)}return null}
function renderSparkline(containerId,values,unit,trendId){const container=$(containerId);if(!container)return;const clean=values.filter(v=>Number.isFinite(v));if(clean.length<2){container.innerHTML='<div class="atl-chart-empty">Datos históricos insuficientes</div>';setText(trendId,"—");return}const width=720,height=220,padX=18,padY=18,min=Math.min(...clean),max=Math.max(...clean),range=max-min||1;const points=clean.map((value,index)=>{const x=padX+index*((width-padX*2)/(clean.length-1));const y=height-padY-((value-min)/range)*(height-padY*2);return`${x.toFixed(2)},${y.toFixed(2)}`}).join(" ");const delta=clean.at(-1)-clean[0];setText(trendId,`${delta>=0?"+":""}${fmt(delta,2)} ${unit}`);container.innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img"><defs><linearGradient id="fill-${containerId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1774c6" stop-opacity=".22"/><stop offset="100%" stop-color="#1774c6" stop-opacity="0"/></linearGradient></defs><polygon points="${padX},${height-padY} ${points} ${width-padX},${height-padY}" fill="url(#fill-${containerId})"/><polyline points="${points}" fill="none" stroke="#0f6cbd" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><text x="${padX}" y="16" fill="#60738c" font-size="12">máx ${fmt(max,2)} ${unit}</text><text x="${padX}" y="${height-4}" fill="#60738c" font-size="12">mín ${fmt(min,2)} ${unit}</text></svg>`}
function renderHistory(h){const rows=historyRows(h).slice(-1440);renderSparkline("temperatureChart",rows.map(r=>choose(r,["local_temp_avg_c","temp_avg_C","temperature_c","temp_c"])),"°C","temperatureTrend");renderSparkline("humidityChart",rows.map(r=>choose(r,["local_hum_avg_pct","hum_avg_pct","humidity_pct","rh_pct"])),"%","humidityTrend");renderSparkline("pressureChart",rows.map(r=>choose(r,["local_press_hpa","pres_avg_hPa","pressure_hpa","press_hpa"])),"hPa","pressureTrend");renderSparkline("rainChart",rows.map(r=>choose(r,["local_rain_1h_mm","rain_1h_mm","precip_mm","rain_mm"])),"mm","rainTrend")}
function source(core){const s=core?.atmospheric_corridor?.sources??{};return s.ERA5??s.NASA??null}
function point(s,n){return s?.points?.[n]??{}}
function renderCorridor(core){const s=source(core);setText("corridorStatus",core?.atmospheric_corridor?.message?"AVAILABLE":"NO DATA");if(!s){$("corridorTable").innerHTML='<div class="atl-chart-empty">Sin corredor atmosférico disponible</div>';return}const ap=point(s,"AP_CUNACALES"),mid=point(s,"MID_LINK"),sm=point(s,"SM_SAN_JOSE");setText("corridorApTemp",`${fmt(ap.temp_c)} °C`);setText("corridorMidTemp",`${fmt(mid.temp_c)} °C`);setText("corridorSmTemp",`${fmt(sm.temp_c)} °C`);setText("corridorApPressure",`${fmt(ap.press_hpa)} hPa`);setText("corridorMidPressure",`${fmt(mid.press_hpa)} hPa`);setText("corridorSmPressure",`${fmt(sm.press_hpa)} hPa`);setText("corridorGradient1",`${fmt(number(mid.temp_c)-number(ap.temp_c),2)} °C`);setText("corridorGradient2",`${fmt(number(sm.temp_c)-number(mid.temp_c),2)} °C`);const rows=(Array.isArray(s.gradients)?s.gradients:[]).map(i=>`<tr><td>${i.label??i.variable??"—"}</td><td>${fmt(i.ap_value,3)} ${i.unit??""}</td><td>${fmt(i.mid_value,3)} ${i.unit??""}</td><td>${fmt(i.sm_value,3)} ${i.unit??""}</td><td>${fmt(i.gradient_ap_to_sm,3)} ${i.unit??""}</td></tr>`).join("");$("corridorTable").innerHTML=`<table><thead><tr><th>Variable</th><th>AP Cuñacales</th><th>Punto medio</th><th>SM San José</th><th>Gradiente AP→SM</th></tr></thead><tbody>${rows}</tbody></table>`}
function renderQuality(latest){const q=latest.scientific_quality??{};const items=[["BME280",q.bme280],["Pluviómetro",q.rain_gauge],["Anemómetro",q.anemometer],["ERA5-Land",q.era5],["NASA POWER",q.nasa_power],["Radioenlace",q.radio_link]];$("qualityList").innerHTML=items.map(([label,state])=>{const x=qualityState(state);return`<div class="atl-quality-row"><span>${label}</span><div class="atl-quality-row__track"><div class="atl-quality-row__bar atl-quality-row__bar--${x.variant}" style="width:${x.score}%"></div></div><strong>${upper(state)}</strong></div>`}).join("");const installed=items.filter(([_,state])=>{
const s=upper(state);
return !["NOT_INSTALLED","NOT_AVAILABLE","DISABLED","NOT_ENABLED"].includes(s);
});

const c=installed.map(([,s])=>qualityState(s));const score=c.length?Math.round(c.reduce((sum,i)=>sum+i.score,0)/c.length):0;setText("scientificHealthScore",`${score}%`);$("scientificHealthBar").style.width=`${score}%`;setText(
"scientificHealthLabel",
`${installed.length}/${items.length} módulos científicos disponibles`
)}
function renderRadio(l){const q=l.scientific_quality??{};setText("radioStatus",upper(q.radio_link));setText("radioRole",l.radio_role??l.radio_local_role);setText("radioRssi",l.radio_sta_dl_rssi??l.radio_rssi_c0p??l.radio_rssi_c0e??"—");setText("radioSnr",l.radio_snr_dl);setText("radioMcs",l.radio_mcs_dl);setText("radioDl",l.radio_dl_rate);setText("radioUl",l.radio_ul_rate);setText("radioNote",l.radio_note??l.radio_error??"Sin observaciones")}
function renderAlerts(core){const a=Array.isArray(core?.alerts?.alerts)?core.alerts.alerts:[];setText("alertCount",a.length);$("alertList").innerHTML=a.length?a.map(x=>`<article class="atl-alert-item ${["DANGER","CRITICAL"].includes(upper(x.severity))?"atl-alert-item--danger":""}"><strong>${x.title??"Alerta"}</strong><p>${x.message??"Sin descripción"}</p></article>`).join(""):'<div class="atl-chart-empty">No existen alertas activas</div>'}
function eventRows(e){if(Array.isArray(e))return e;if(Array.isArray(e?.events))return e.events;if(Array.isArray(e?.data))return e.data;return[]}
function renderEvents(e){const rows=eventRows(e).slice(0,8);$("eventList").innerHTML=rows.length?rows.map(x=>`<article class="atl-event-item"><time>${dateTime(x.timestamp??x.created_at??x.event_time??x.datetime)}</time><div><strong>${x.title??x.category??"Evento"}</strong><p>${x.description??x.message??x.severity??"—"}</p></div></article>`).join(""):'<div class="atl-chart-empty">No hay eventos recientes</div>'}
function renderFooter(p){setText("lastObservation",dateTime(p.health.latest_observation??p.latest.timestamp_local));setText("lastRefresh",dateTime(new Date().toISOString()));setText("footerState",p.errors.length?"DATOS PARCIALES":"EN LÍNEA");setText("connectionState",p.errors.length?"Datos parciales":"Plataforma conectada");const n=$("partialDataNotice");if(p.errors.length){n.hidden=false;n.textContent=`Carga parcial. Endpoints no disponibles: ${p.errors.join(", ")}`}else{n.hidden=true;n.textContent=""}}
async function refresh(){const root=$("proDashboardRoot");root?.classList.add("atl-loading");try{const p=await loadAll();renderTop(p);renderWeather(p.latest);renderHistory(p.history);renderCorridor(p.core);renderQuality(p.latest);renderRadio(p.latest);renderAlerts(p.core);renderEvents(p.events);renderFooter(p)}catch(error){console.error(error);setText("connectionState","Error de conexión");setText("footerState","ERROR")}finally{root?.classList.remove("atl-loading")}}
document.addEventListener("DOMContentLoaded",()=>{refresh();window.setInterval(() => refresh(),REFRESH_MS)});

// AtmosLink UI v2.1 scientific semantics patch
const originalRenderCorridor = renderCorridor;

renderCorridor = function(core) {
  const sources = core?.atmospheric_corridor?.sources ?? {};
  const selectedSource = sources.ERA5 ? "ERA5-Land" :
    sources.NASA ? "NASA POWER" : "No disponible";

  setText("corridorSourceLabel", `Fuente: ${selectedSource}`);
  originalRenderCorridor(core);
};

// AtmosLink UI v2.2 intelligent navigation

function initializeProfessionalNavigation() {
  const app = document.querySelector(".atl-app");
  const toggle = document.getElementById("sidebarToggle");
  const navigation = document.getElementById("proNavigation");
  const internalLinks = Array.from(
    document.querySelectorAll(
      '#proNavigation a[data-section]'
    )
  );

  if (!app || !navigation || !internalLinks.length) {
    return;
  }

  const setActive = (sectionId) => {
    internalLinks.forEach((link) => {
      const active =
        link.dataset.section === sectionId;

      link.classList.toggle(
        "atl-nav__item--active",
        active
      );

      if (active) {
        link.setAttribute(
          "aria-current",
          "page"
        );
      } else {
        link.removeAttribute(
          "aria-current"
        );
      }
    });
  };

  internalLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      const sectionId = link.dataset.section;
      const target =
        document.getElementById(sectionId);

      if (!target) {
        return;
      }

      event.preventDefault();

      target.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });

      history.replaceState(
        null,
        "",
        `#${sectionId}`
      );

      setActive(sectionId);
    });
  });

  const sections = Array.from(
    document.querySelectorAll(
      "[data-nav-section]"
    )
  );

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort(
          (a, b) =>
            b.intersectionRatio -
            a.intersectionRatio
        );

      if (visible.length) {
        setActive(
          visible[0].target.dataset.navSection
        );
      }
    },
    {
      root: null,
      rootMargin: "-18% 0px -62% 0px",
      threshold: [0.05, 0.15, 0.3]
    }
  );

  sections.forEach((section) => {
    observer.observe(section);
  });

  const storedState =
    localStorage.getItem(
      "atmoslink.sidebar.collapsed"
    );

  if (storedState === "true") {
    app.classList.add(
      "atl-sidebar-collapsed"
    );
    toggle?.setAttribute(
      "aria-expanded",
      "false"
    );
  }

  toggle?.addEventListener(
    "click",
    () => {
      const collapsed =
        app.classList.toggle(
          "atl-sidebar-collapsed"
        );

      toggle.setAttribute(
        "aria-expanded",
        String(!collapsed)
      );

      localStorage.setItem(
        "atmoslink.sidebar.collapsed",
        String(collapsed)
      );
    }
  );

  const initialSection =
    window.location.hash.slice(1);

  if (
    initialSection &&
    document.getElementById(initialSection)
  ) {
    window.setTimeout(() => {
      document
        .getElementById(initialSection)
        .scrollIntoView({
          behavior: "auto",
          block: "start"
        });

      setActive(initialSection);
    }, 80);
  } else {
    setActive("dashboard");
  }
}

document.addEventListener(
  "DOMContentLoaded",
  initializeProfessionalNavigation
);

// AtmosLink UI v2.3 — scientific consistency and provenance

let atlV23LatestSnapshot = {};

const atlV23OriginalRenderWeather = renderWeather;
renderWeather = function(latest) {
  atlV23LatestSnapshot = latest ?? {};
  atlV23OriginalRenderWeather(latest);
};

function atlV23Value(value, digits = 3, unit = "") {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return "—";
  }

  return `${fmt(parsed, digits)}${unit ? ` ${unit}` : ""}`;
}

function atlV23LocalValue(variable) {
  const latest = atlV23LatestSnapshot ?? {};

  const map = {
    temp_c:
      latest.local_temp_avg_c ??
      latest.temp_avg_C,

    rh_pct:
      latest.local_hum_avg_pct ??
      latest.hum_avg_pct,

    press_hpa:
      latest.local_press_hpa ??
      latest.pres_avg_hPa,

    precip_mm:
      latest.local_rain_1h_mm ??
      latest.rain_1h_mm,

    wind_ms:
      latest.local_wind_speed_ms ??
      latest.wind_speed_ms
  };

  return map[variable];
}

function atlV23LocalInstalled(variable) {
  const latest = atlV23LatestSnapshot ?? {};

  if (variable === "wind_ms") {
    const windOk =
      Number(
        latest.local_wind_ok ??
        latest.wind_ok
      ) === 1;

    const windValue =
      latest.local_wind_speed_ms ??
      latest.wind_speed_ms;

    return (
      windOk &&
      windValue !== null &&
      windValue !== undefined &&
      Number.isFinite(Number(windValue))
    );
  }

  if (variable === "precip_mm") {
    return Number(
      latest.local_rain_ok ??
      latest.rain_ok
    ) === 1;
  }

  if (
    ["temp_c", "rh_pct", "press_hpa"].includes(variable)
  ) {
    return Number(
      latest.local_bme_ok ??
      latest.bme_ok
    ) === 1;
  }

  return false;
}

function atlV23OriginBadge(kind, label) {
  return `<span class="atl-value-origin atl-value-origin--${kind}">${label}</span>`;
}

const atlV23OriginalRenderCorridor = renderCorridor;

renderCorridor = function(core) {
  const sources =
    core?.atmospheric_corridor?.sources ?? {};

  const sourceName = sources.ERA5
    ? "ERA5-Land"
    : sources.NASA
      ? "NASA POWER"
      : "No disponible";

  const model = sources.ERA5 ?? sources.NASA ?? null;

  setText(
    "corridorSourceLabel",
    `Fuente modelada: ${sourceName}`
  );

  setText(
    "corridorStatus",
    model ? "MODEL + LOCAL" : "NO DATA"
  );

  if (!model) {
    atlV23OriginalRenderCorridor(core);
    return;
  }

  const mid = model?.points?.MID_LINK ?? {};
  const sm = model?.points?.SM_SAN_JOSE ?? {};

  const localTemp = atlV23LocalValue("temp_c");
  const localPressure = atlV23LocalValue("press_hpa");

  setText(
    "corridorApTemp",
    Number.isFinite(Number(localTemp))
      ? `${fmt(localTemp, 1)} °C`
      : "No disponible"
  );

  setText(
    "corridorApPressure",
    Number.isFinite(Number(localPressure))
      ? `${fmt(localPressure, 1)} hPa`
      : "No disponible"
  );

  setText(
    "corridorMidTemp",
    `${fmt(mid.temp_c, 1)} °C`
  );

  setText(
    "corridorMidPressure",
    `${fmt(mid.press_hpa, 1)} hPa`
  );

  setText(
    "corridorSmTemp",
    `${fmt(sm.temp_c, 1)} °C`
  );

  setText(
    "corridorSmPressure",
    `${fmt(sm.press_hpa, 1)} hPa`
  );

  const modelGradients = Array.isArray(model.gradients)
    ? model.gradients
    : [];

  const tempGradient = modelGradients.find(
    (item) => item.variable === "temp_c"
  );

  setText(
    "corridorGradient1",
    tempGradient
      ? `${fmt(
          tempGradient.gradient_ap_to_mid,
          2
        )} °C modelo`
      : "Modelo"
  );

  setText(
    "corridorGradient2",
    tempGradient
      ? `${fmt(
          tempGradient.gradient_mid_to_sm,
          2
        )} °C modelo`
      : "Modelo"
  );

  const apCard = document.querySelector(
    ".atl-corridor-point--observed"
  );

  const modelCards = document.querySelectorAll(
    ".atl-corridor-point--model"
  );

  if (
    apCard &&
    !apCard.querySelector(
      ".atl-corridor-point__source"
    )
  ) {
    const badge = document.createElement("span");
    badge.className =
      "atl-corridor-point__source " +
      "atl-corridor-point__source--observed";
    badge.textContent = "MEDICIÓN LOCAL";
    apCard.insertBefore(
      badge,
      apCard.querySelector("small")
    );
  }

  modelCards.forEach((card) => {
    if (
      card.querySelector(
        ".atl-corridor-point__source"
      )
    ) {
      return;
    }

    const badge = document.createElement("span");
    badge.className =
      "atl-corridor-point__source " +
      "atl-corridor-point__source--model";
    badge.textContent = sourceName.toUpperCase();
    card.insertBefore(
      badge,
      card.querySelector("small")
    );
  });

  const rows = modelGradients.map((item) => {
    const variable = item.variable;
    const installed = atlV23LocalInstalled(variable);
    const local = atlV23LocalValue(variable);

    let apCell;

    if (variable === "wind_ms" && !installed) {
      apCell = `
        <span class="atl-unavailable">
          No disponible
        </span>
        ${atlV23OriginBadge(
          "unavailable",
          "SIN ANEMÓMETRO"
        )}
        <small>
          El sensor de viento local aún no está instalado.
        </small>
      `;
    } else if (installed && Number.isFinite(Number(local))) {
      apCell = `
        ${atlV23Value(
          local,
          variable === "precip_mm" ? 3 : 3,
          item.unit
        )}
        ${atlV23OriginBadge(
          "observed",
          "OBSERVADO"
        )}
      `;
    } else {
      apCell = `
        <span class="atl-unavailable">
          No disponible
        </span>
        ${atlV23OriginBadge(
          "unavailable",
          "SIN DATO LOCAL"
        )}
      `;
    }

    return `
      <tr>
        <td>${item.label ?? variable ?? "—"}</td>
        <td>${apCell}</td>
        <td>
          ${atlV23Value(
            item.mid_value,
            3,
            item.unit
          )}
          ${atlV23OriginBadge(
            "model",
            sourceName.toUpperCase()
          )}
        </td>
        <td>
          ${atlV23Value(
            item.sm_value,
            3,
            item.unit
          )}
          ${atlV23OriginBadge(
            "model",
            sourceName.toUpperCase()
          )}
        </td>
        <td>
          ${atlV23Value(
            item.gradient_ap_to_sm,
            3,
            item.unit
          )}
          ${atlV23OriginBadge(
            "model",
            "GRADIENTE MODELO"
          )}
        </td>
      </tr>
    `;
  }).join("");

  const table = document.getElementById(
    "corridorTable"
  );

  if (table) {
    table.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Variable</th>
            <th>AP Cuñacales</th>
            <th>Punto medio</th>
            <th>SM San José</th>
            <th>Gradiente modelado AP→SM</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }
};

const atlV23OriginalRenderQuality = renderQuality;

renderQuality = function(latest) {
  atlV23OriginalRenderQuality(latest);

  const quality = latest?.scientific_quality ?? {};

  const planned = [
    quality.bme280,
    quality.rain_gauge,
    quality.anemometer,
    quality.era5,
    quality.nasa_power,
    quality.radio_link
  ];

  const installed = planned.filter(
    (state) =>
      ![
        "NOT_INSTALLED",
        "DISABLED",
        "NOT_ENABLED",
        "UNKNOWN"
      ].includes(upper(state))
  );

  const operationalInstalled = installed.filter(
    (state) =>
      ["OK", "HEALTHY", "FRESH", "AVAILABLE"]
        .includes(upper(state))
  );

  const operationalScore = installed.length
    ? Math.round(
        operationalInstalled.length /
        installed.length *
        100
      )
    : 0;

  const coverageScore = Math.round(
    installed.length /
    planned.length *
    100
  );

  setText(
    "scientificHealthScore",
    `${operationalScore}%`
  );

  const bar = document.getElementById(
    "scientificHealthBar"
  );

  if (bar) {
    bar.style.width = `${operationalScore}%`;
  }

  setText(
    "scientificHealthLabel",
    operationalScore >= 90
      ? "Salud de componentes instalados"
      : "Requiere revisión operacional"
  );

  const scoreBox = document.querySelector(
    ".atl-health-score"
  );

  if (scoreBox) {
    const heading = scoreBox.querySelector(
      ".atl-health-score__label"
    );

    if (heading) {
      heading.textContent =
        "Operational Scientific Health";
    }

    let coverage = scoreBox.querySelector(
      ".atl-scientific-coverage"
    );

    if (!coverage) {
      coverage = document.createElement("div");
      coverage.className =
        "atl-scientific-coverage";
      scoreBox.appendChild(coverage);
    }

    coverage.innerHTML = `
      <strong>
        ${operationalInstalled.length}/${installed.length}
        componentes instalados operativos
      </strong>
      <span>
        Cobertura instrumental prevista:
        ${installed.length}/${planned.length}
        (${coverageScore}%)
      </span>
      <span>
        Anemómetro local:
        ${upper(quality.anemometer)}
      </span>
    `;
  }
};

/* =========================================================
   AtmosLink UI v2.4 — Native Multi-Station Support
   ========================================================= */

const ATL_STATION_STORAGE_KEY = "atmoslink_selected_station";
let atlSelectedStation =
  localStorage.getItem(ATL_STATION_STORAGE_KEY) || "CU01";

let atlRefreshGeneration = 0;

const atlOriginalLoadAll = loadAll;
const atlOriginalRenderTop = renderTop;
const atlOriginalRenderCorridor = renderCorridor;
const atlOriginalRenderQuality = renderQuality;
const atlOriginalRenderRadio = renderRadio;


function atlStationLatestAdapter(data) {
  const radio = data.radio ?? {};

  const radioMetrics = [
    radio.mcs_dl,
    radio.mcs_ul,
    radio.snr_dl,
    radio.snr_ul,
    radio.rssi_c0p,
    radio.rssi_c1p,
    radio.sta_dl_rssi,
    radio.sta_ul_rssi,
    radio.dl_rate,
    radio.ul_rate,
  ];

  const hasRadioTelemetry =
    radioMetrics.some(
      value =>
        value !== null &&
        value !== undefined &&
        value !== ""
    );

  const radioAgeSeconds =
    Number(radio.age_seconds);

  const radioIsFresh =
    Number.isFinite(radioAgeSeconds)
      ? radioAgeSeconds <= 900
      : Boolean(radio.timestamp_local);

  const invalidRadioNotes = new Set([
    "RADIO_UNAVAILABLE",
    "SM_NOT_ASSOCIATED",
    "NOT_AVAILABLE",
    "NO_TELEMETRY",
  ]);

  const normalizedRadioNote =
    upper(radio.note, "");

  const radioIsAvailable =
    hasRadioTelemetry &&
    radioIsFresh &&
    !invalidRadioNotes.has(
      normalizedRadioNote
    );

  const radioDownlinkRssi =
    radio.sta_dl_rssi ??
    radio.rssi_c0p ??
    radio.rssi_c0e ??
    null;

  const radioUplinkRssi =
    radio.sta_ul_rssi ??
    radio.rssi_c1p ??
    radio.rssi_c1e ??
    null;

  return {
    ...data,

    local_temp_avg_c: data.temp_avg_C,
    local_temp_min_c: data.temp_min_C,
    local_temp_max_c: data.temp_max_C,

    local_hum_avg_pct: data.hum_avg_pct,
    local_hum_min_pct: data.hum_min_pct,
    local_hum_max_pct: data.hum_max_pct,

    local_press_hpa: data.pres_avg_hPa,
    local_dew_point_c: data.dew_point_C,
    local_vapor_pressure_hpa:
      data.vapor_pressure_hPa,

    local_rain_1min_mm: data.rain_1min_mm,
    local_rain_1h_mm: data.rain_1h_mm,
    /*
     * SJ01: los primeros 24.03 mm se produjeron durante
     * transporte, instalación y manipulación del balancín.
     * Se conservan en la base de datos, pero se excluyen
     * del acumulado científico de campo.
     */
    local_rain_total_mm:
      data.station_id === "SJ01" &&
      number(data.rain_total_mm) !== null
        ? Math.max(
            0,
            number(data.rain_total_mm) - 24.03
          )
        : data.rain_total_mm,

    local_wind_speed_ms: data.wind_speed_ms,
    local_wind_direction_deg:
      data.wind_direction_deg,
    local_wind_gust_ms: data.wind_gust_ms,

    local_bme_ok: data.bme_ok,
    local_rain_ok: data.rain_ok,
    local_wind_ok: data.wind_ok,

    observation_age_label:
      data.observation_age_seconds == null
        ? "—"
        : data.observation_age_seconds < 60
          ? `hace ${data.observation_age_seconds} s`
          : `hace ${(
              data.observation_age_seconds / 60
            ).toFixed(1)} min`,

    scientific_quality: {
      ...(data.scientific_quality ?? {}),

      bme280:
        data.bme_ok === 1 ? "OK" : "ERROR",

      rain_gauge:
        data.rain_ok === 1 ? "OK" : "ERROR",

      anemometer:
        data.wind_ok === 1 ? "OK" : "ERROR",

      era5:
        data.scientific_quality?.era5 ??
        "OK",

      nasa_power:
        data.scientific_quality?.nasa_power ??
        "OK",

      radio_link:
        radioIsAvailable
          ? "OK"
          : (
              data.scientific_quality
                ?.radio_link ??
              "NOT_AVAILABLE"
            ),
    },

    radio_station_id:
      radio.station_id ??
      data.station_id,

    radio_timestamp_local:
      radio.timestamp_local ??
      null,

    radio_role:
      data.radio_role ??
      data.radio_local_role ??
      null,

    radio_local_role:
      data.radio_role ??
      data.radio_local_role ??
      null,

    radio_mcs_dl:
      radio.mcs_dl ??
      null,

    radio_mcs_ul:
      radio.mcs_ul ??
      null,

    radio_snr_dl:
      radio.snr_dl ??
      null,

    radio_snr_ul:
      radio.snr_ul ??
      null,

    radio_rssi_c0p:
      radioDownlinkRssi,

    radio_rssi_c1p:
      radioUplinkRssi,

    radio_sta_dl_rssi:
      radioDownlinkRssi,

    radio_sta_ul_rssi:
      radioUplinkRssi,

    radio_dl_rate:
      radio.dl_rate ??
      null,

    radio_ul_rate:
      radio.ul_rate ??
      null,

    radio_note:
      radioIsAvailable
        ? (
            radio.note ||
            "ok"
          )
        : (
            radio.note ||
            radio.error ||
            "Telemetría RF no disponible"
          ),

    radio_error:
      radio.error ??
      "",
  };
}

function atlStationHistoryAdapter(record) {
  return {
    ...record,

    local_temp_avg_c: record.temp_avg_C,
    local_temp_min_c: record.temp_min_C,
    local_temp_max_c: record.temp_max_C,

    local_hum_avg_pct: record.hum_avg_pct,
    local_hum_min_pct: record.hum_min_pct,
    local_hum_max_pct: record.hum_max_pct,

    local_press_hpa: record.pres_avg_hPa,
    local_dew_point_c: record.dew_point_C,
    local_vapor_pressure_hpa: record.vapor_pressure_hPa,

    local_rain_1min_mm: record.rain_1min_mm,
    local_rain_1h_mm: record.rain_1h_mm,
    local_rain_total_mm: record.rain_total_mm,

    local_wind_speed_ms: record.wind_speed_ms,
    local_wind_direction_deg: record.wind_direction_deg,
    local_wind_gust_ms: record.wind_gust_ms,

    master_timestamp_local:
      record.timestamp_local || record.bucket_minute,

    weather_timestamp_local:
      record.weather_timestamp_local || record.timestamp_local,
  };
}


async function atlFetchJson(url) {
  const response = await fetch(url, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `HTTP ${response.status} al consultar ${url}`
    );
  }

  return response.json();
}


async function atlLoadSelectedStation(selectedStation) {
  const platformPayload = await atlOriginalLoadAll();

  if (selectedStation === "CU01") {
    return platformPayload;
  }

  const stationId = encodeURIComponent(
    selectedStation
  );

  const [latestResponse, historyResponse] =
    await Promise.all([
      atlFetchJson(
        `/api/station/latest?station_id=${stationId}`
      ),
      atlFetchJson(
        `/api/station/history?station_id=${stationId}&limit=1440`
      ),
    ]);

  const latest = atlStationLatestAdapter(
    latestResponse
  );

  const sj01FieldStart = Date.parse(
    "2026-08-31T18:30:00-05:00"
  );

  const history = (
    historyResponse.records || []
  )
    .map(atlStationHistoryAdapter)
    .filter(record => {
      if (selectedStation !== "SJ01") {
        return true;
      }

      const timestamp =
        record.weather_timestamp_local ||
        record.master_timestamp_local ||
        record.timestamp_local ||
        record.bucket_minute;

      if (!timestamp) {
        return false;
      }

      const normalizedTimestamp =
        String(timestamp).includes("T")
          ? String(timestamp)
          : String(timestamp).replace(
              " ",
              "T"
            );

      const recordTime = Date.parse(
        normalizedTimestamp
      );

      return (
        Number.isFinite(recordTime) &&
        recordTime >= sj01FieldStart
      );
    });

  return {
    ...platformPayload,
    latest,
    history,

    health: {
      ...platformPayload.health,
      station_id: latest.station_id,
      station_name: latest.station_name,
      operational_state:
        latest.observation_state || "UNKNOWN",
    },
  };
}


function atlRenderUnavailableSources(latest) {
  setText("corridorStatus", "NO DISPONIBLE");
  setText(
    "corridorSourceLabel",
    "Sin asociación ERA5/NASA para la estación seleccionada"
  );

  setText("corridorApTemp", "—");
  setText("corridorApPressure", "—");
  setText("corridorMidTemp", "—");
  setText("corridorMidPressure", "—");
  setText("corridorSmTemp", "—");
  setText("corridorSmPressure", "—");
  setText("corridorGradient1", "—");
  setText("corridorGradient2", "—");

  const corridorTable =
    document.getElementById("corridorTable");

  if (corridorTable) {
    corridorTable.innerHTML =
      '<div class="atl-chart-empty">' +
      'El modelo atmosférico todavía no está asociado ' +
      'a esta estación.</div>';
  }

  setText("radioStatus", "NO DISPONIBLE");
  setText("radioRole", latest.radio_role || "—");
  setText("radioRssi", "—");
  setText("radioSnr", "—");
  setText("radioMcs", "—");
  setText("radioDl", "—");
  setText("radioUl", "—");
  setText(
    "radioNote",
    "La telemetría Cambium todavía no está asociada a SJ01."
  );
}


function atlRenderFirmwareTraceability(latest) {
  if (latest.station_id === "CU01") {
    return;
  }

  const version =
    latest.firmware_version || "UNKNOWN";

  const build =
    latest.firmware_build || "UNKNOWN";

  const device =
    latest.device_id || "UNKNOWN";

  setText(
    "heroVersion",
    `Firmware ${version} · Build ${build} · ${device}`
  );
}


async function atlLoadStationCatalog() {
  const selector =
    document.getElementById("stationSelector");

  if (!selector) {
    return;
  }

  const wrapper = selector.closest(
    ".atl-station-selector"
  );

  wrapper?.classList.add(
    "atl-station-selector--loading"
  );

  try {
    const payload = await atlFetchJson(
      "/api/stations"
    );

    const stations = payload.stations || [];

    if (stations.length) {
      selector.innerHTML = stations.map(
        station => {
          const id = station.station_id;
          const name =
            station.station_name || id;
          const state =
            station.status || "UNKNOWN";

          return (
            `<option value="${id}">` +
            `${id} · ${name} · ${state}` +
            `</option>`
          );
        }
      ).join("");
    }

    const exists = stations.some(
      station =>
        station.station_id === atlSelectedStation
    );

    if (!exists) {
      atlSelectedStation = "CU01";
    }

    selector.value = atlSelectedStation;

  } catch (error) {
    console.error(
      "No se pudo cargar el catálogo de estaciones:",
      error
    );

  } finally {
    wrapper?.classList.remove(
      "atl-station-selector--loading"
    );
  }
}


/*
 * Sustituye la función refresh original.
 * El setInterval existente utilizará esta versión.
 */
refresh = async function() {
  const generation = ++atlRefreshGeneration;
  const requestedStation = atlSelectedStation;

  const root =
    document.getElementById("proDashboardRoot");

  root?.classList.add("atl-loading");

  try {
    const payload =
      await atlLoadSelectedStation(
        requestedStation
      );

    if (
      generation !== atlRefreshGeneration ||
      requestedStation !== atlSelectedStation
    ) {
      return;
    }

    const responseStation =
      payload.latest?.station_id || "CU01";

    if (responseStation !== requestedStation) {
      console.warn(
        "Respuesta descartada por estación:",
        requestedStation,
        responseStation
      );
      return;
    }

    const isRemote =
      payload.latest.station_id !== "CU01";

    root?.classList.toggle(
      "atl-station-remote",
      isRemote
    );

    atlOriginalRenderTop(payload);
    renderWeather(payload.latest);
    renderHistory(payload.history);


      /* ATMOSLINK_FINAL_RENDER_ORDER_V2 */
      if (
        typeof window.atlRenderHybridCorridor ===
        "function"
      ) {
        await window.atlRenderHybridCorridor(
          payload.core
        );
      } else {
        atlOriginalRenderCorridor(
          payload.core
        );
      }

    atlOriginalRenderRadio(
      payload.latest
    );

    atlOriginalRenderQuality(
      payload.latest
    );

    renderAlerts(payload.core);
    renderEvents(payload.events);
    renderFooter(payload);

    atlRenderFirmwareTraceability(
      payload.latest
    );

  } catch (error) {
    console.error(error);

    setText(
      "connectionState",
      "Error de conexión"
    );

    setText(
      "footerState",
      "ERROR"
    );

  } finally {
    if (generation === atlRefreshGeneration) {
      root?.classList.remove("atl-loading");
    }
  }
};


document.addEventListener(
  "DOMContentLoaded",
  async () => {
    await atlLoadStationCatalog();

    const selector =
      document.getElementById(
        "stationSelector"
      );

    selector?.addEventListener(
      "change",
      async event => {
        atlSelectedStation =
          event.target.value || "CU01";

        localStorage.setItem(
          ATL_STATION_STORAGE_KEY,
          atlSelectedStation
        );

        await refresh();
      }
    );
  }
);

/* =========================================================
   AtmosLink UI v2.4.1
   Operational health and rain-state semantics
   ========================================================= */

const atlV241PreviousRenderWeather = renderWeather;

renderWeather = function(latest) {
  /*
   * Conserva todos los ajustes meteorológicos previamente
   * implementados y corrige únicamente el estado de lluvia.
   */
  atlV241PreviousRenderWeather(latest);

  const rainOk = Number(
    latest.local_rain_ok ??
    latest.rain_ok
  );

  const rain1min = Number(
    latest.local_rain_1min_mm ??
    latest.rain_1min_mm ??
    0
  );

  const rain1h = Number(
    latest.local_rain_1h_mm ??
    latest.rain_1h_mm ??
    0
  );

  let state = "NO DISPONIBLE";

  if (rainOk === 1) {
    state =
      rain1min > 0 || rain1h > 0
        ? "LLUVIA DETECTADA"
        : "SIN LLUVIA";
  } else if (rainOk === 0) {
    state = "SENSOR NO DISPONIBLE";
  }

  setText("rainState", state);
};


renderQuality = function(latest) {
  const quality =
    latest.scientific_quality ?? {};

  const items = [
    ["BME280", quality.bme280],
    ["Pluviómetro", quality.rain_gauge],
    ["Anemómetro", quality.anemometer],
    ["ERA5-Land", quality.era5],
    ["NASA POWER", quality.nasa_power],
    ["Radioenlace", quality.radio_link],
  ];

  const nonInstalledStates = new Set([
    "NOT_INSTALLED",
    "NOT_AVAILABLE",
    "DISABLED",
    "NOT_ENABLED",
    "PENDING",
    "UNASSOCIATED",
  ]);

  const operationalStates = new Set([
    "OK",
    "HEALTHY",
    "FRESH",
    "CURRENT",
    "AVAILABLE",
    "ONLINE",
  ]);

  const normalizedItems = items.map(
    ([label, rawState]) => {
      const state = upper(
        rawState,
        "UNKNOWN"
      );

      const installed =
        !nonInstalledStates.has(state);

      const operational =
        installed &&
        operationalStates.has(state);

      return {
        label,
        state,
        installed,
        operational,
        visual: installed
          ? qualityState(state)
          : {
              score: 0,
              variant: "disabled",
            },
      };
    }
  );

  const installedItems =
    normalizedItems.filter(
      item => item.installed
    );

  const operationalItems =
    installedItems.filter(
      item => item.operational
    );

  const operationalScore =
    installedItems.length
      ? Math.round(
          operationalItems.length /
          installedItems.length *
          100
        )
      : 0;

  const scientificCoverage =
    Math.round(
      installedItems.length /
      normalizedItems.length *
      100
    );

  const statusLabel = state => {
    if (
      nonInstalledStates.has(state)
    ) {
      return "NO ASOCIADO";
    }

    if (
      operationalStates.has(state)
    ) {
      return "OK";
    }

    return state;
  };

  const qualityList =
    document.getElementById(
      "qualityList"
    );

  if (qualityList) {
    qualityList.innerHTML =
      normalizedItems.map(item => `
        <div class="atl-quality-row">
          <span>${item.label}</span>

          <div class="atl-quality-row__track">
            <div
              class="
                atl-quality-row__bar
                atl-quality-row__bar--${item.visual.variant}
              "
              style="width:${item.visual.score}%"
            ></div>
          </div>

          <strong>
            ${statusLabel(item.state)}
          </strong>
        </div>
      `).join("");
  }

  setText(
    "scientificHealthScore",
    `${operationalScore}%`
  );

  const healthBar =
    document.getElementById(
      "scientificHealthBar"
    );

  if (healthBar) {
    healthBar.style.width =
      `${operationalScore}%`;
  }

  setText(
    "scientificHealthLabel",
    installedItems.length
      ? (
          `${operationalItems.length}/` +
          `${installedItems.length} componentes ` +
          `instalados operativos`
        )
      : "Sin componentes evaluables"
  );

  const scoreBox =
    document.querySelector(
      ".atl-health-score"
    );

  if (scoreBox) {
    let coverage =
      scoreBox.querySelector(
        ".atl-scientific-coverage"
      );

    if (!coverage) {
      coverage =
        document.createElement("div");

      coverage.className =
        "atl-scientific-coverage";

      scoreBox.appendChild(
        coverage
      );
    }

    coverage.innerHTML = `
      <span>
        Cobertura científica:
        <strong>
          ${installedItems.length}/
          ${normalizedItems.length}
          módulos
        </strong>
        (${scientificCoverage}%)
      </span>
    `;
  }
};

/* =========================================================
   AtmosLink UI v2.5.0
   Multi-Station Atmospheric Observatory
   ========================================================= */

function atlObservatoryNumber(
  value,
  digits = 2
) {
  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    return null;
  }

  return Number(
    parsed.toFixed(digits)
  );
}


function atlObservatoryMetric(
  station,
  keys
) {
  for (const key of keys) {
    const value = station?.[key];

    if (
      value !== null &&
      value !== undefined &&
      Number.isFinite(Number(value))
    ) {
      return Number(value);
    }
  }

  return null;
}


function atlObservatoryDifference(
  sj01Value,
  cu01Value
) {
  if (
    sj01Value === null ||
    cu01Value === null
  ) {
    return null;
  }

  return sj01Value - cu01Value;
}


function atlObservatoryDifferenceText(
  value,
  unit,
  digits = 2
) {
  if (
    value === null ||
    !Number.isFinite(value)
  ) {
    return "—";
  }

  const sign =
    value > 0
      ? "+"
      : "";

  return (
    `${sign}${fmt(value, digits)} ${unit}`
  );
}


function atlObservatoryStateClass(
  state
) {
  const normalized = upper(
    state,
    "UNKNOWN"
  );

  if (normalized === "ONLINE") {
    return "atl-observatory-state--online";
  }

  if (
    normalized === "DELAYED" ||
    normalized === "STALE"
  ) {
    return "atl-observatory-state--delayed";
  }

  return "atl-observatory-state--offline";
}


function atlObservatoryRenderState(
  elementId,
  state
) {
  const element =
    document.getElementById(
      elementId
    );

  if (!element) {
    return;
  }

  element.textContent = upper(
    state,
    "UNKNOWN"
  );

  element.classList.remove(
    "atl-observatory-state--online",
    "atl-observatory-state--delayed",
    "atl-observatory-state--offline"
  );

  element.classList.add(
    atlObservatoryStateClass(state)
  );
}


function atlObservatoryTimestampMs(
  station
) {
  const value =
    station?.timestamp_local ??
    station?.weather_timestamp_local ??
    station?.bucket_minute;

  if (!value) {
    return null;
  }

  const date = new Date(
    String(value).replace(
      " ",
      "T"
    )
  );

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date.getTime();
}


function atlObservatoryComparableCount(
  cu01,
  sj01
) {
  const variables = [
    [
      ["temp_avg_C", "local_temp_avg_c"],
      ["temp_avg_C", "local_temp_avg_c"],
    ],
    [
      ["hum_avg_pct", "local_hum_avg_pct"],
      ["hum_avg_pct", "local_hum_avg_pct"],
    ],
    [
      ["pres_avg_hPa", "local_press_hpa"],
      ["pres_avg_hPa", "local_press_hpa"],
    ],
    [
      ["dew_point_C", "local_dew_point_c"],
      ["dew_point_C", "local_dew_point_c"],
    ],
    [
      ["rain_1h_mm", "local_rain_1h_mm"],
      ["rain_1h_mm", "local_rain_1h_mm"],
    ],
    [
      ["wind_speed_ms", "local_wind_speed_ms"],
      ["wind_speed_ms", "local_wind_speed_ms"],
    ],
  ];

  return variables.filter(
    ([cuKeys, sjKeys]) => (
      atlObservatoryMetric(
        cu01,
        cuKeys
      ) !== null &&
      atlObservatoryMetric(
        sj01,
        sjKeys
      ) !== null
    )
  ).length;
}


function atlRenderObservatoryStation(
  prefix,
  station
) {
  const temperature =
    atlObservatoryMetric(
      station,
      [
        "temp_avg_C",
        "local_temp_avg_c",
      ]
    );

  const humidity =
    atlObservatoryMetric(
      station,
      [
        "hum_avg_pct",
        "local_hum_avg_pct",
      ]
    );

  const pressure =
    atlObservatoryMetric(
      station,
      [
        "pres_avg_hPa",
        "local_press_hpa",
      ]
    );

  const windSpeed =
    atlObservatoryMetric(
      station,
      [
        "wind_speed_ms",
        "local_wind_speed_ms",
      ]
    );

  const windDirection =
    station?.wind_direction_text ??
    station?.local_wind_direction_text ??
    "—";

  setText(
    `${prefix}Temp`,
    temperature === null
      ? "—"
      : `${fmt(temperature, 1)} °C`
  );

  setText(
    `${prefix}Humidity`,
    humidity === null
      ? "—"
      : `${fmt(humidity, 1)} %`
  );

  setText(
    `${prefix}Pressure`,
    pressure === null
      ? "—"
      : `${fmt(pressure, 1)} hPa`
  );

  setText(
    `${prefix}Wind`,
    windSpeed === null
      ? "No instalado"
      : (
          `${fmt(windSpeed, 1)} m/s ` +
          `${windDirection}`
        )
  );

  setText(
    `${prefix}Timestamp`,
    (
      "Última observación: " +
      dateTime(
        station?.timestamp_local ??
        station?.weather_timestamp_local ??
        station?.bucket_minute
      )
    )
  );

  atlObservatoryRenderState(
    `${prefix}State`,
    station?.observation_state ??
    "UNKNOWN"
  );
}


async function atlLoadObservatory() {
  const statusElement =
    document.getElementById(
      "observatoryStatus"
    );

  if (!statusElement) {
    return;
  }

  statusElement.textContent =
    "ACTUALIZANDO";

  try {
    const [
      cu01,
      sj01,
    ] = await Promise.all([
      atlFetchJson(
        "/api/station/latest?station_id=CU01"
      ),
      atlFetchJson(
        "/api/station/latest?station_id=SJ01"
      ),
    ]);

    atlRenderObservatoryStation(
      "observatoryCu01",
      cu01
    );

    atlRenderObservatoryStation(
      "observatorySj01",
      sj01
    );

    const cuTemp =
      atlObservatoryMetric(
        cu01,
        ["temp_avg_C", "local_temp_avg_c"]
      );

    const sjTemp =
      atlObservatoryMetric(
        sj01,
        ["temp_avg_C", "local_temp_avg_c"]
      );

    const cuHumidity =
      atlObservatoryMetric(
        cu01,
        ["hum_avg_pct", "local_hum_avg_pct"]
      );

    const sjHumidity =
      atlObservatoryMetric(
        sj01,
        ["hum_avg_pct", "local_hum_avg_pct"]
      );

    const cuPressure =
      atlObservatoryMetric(
        cu01,
        ["pres_avg_hPa", "local_press_hpa"]
      );

    const sjPressure =
      atlObservatoryMetric(
        sj01,
        ["pres_avg_hPa", "local_press_hpa"]
      );

    const cuDewPoint =
      atlObservatoryMetric(
        cu01,
        ["dew_point_C", "local_dew_point_c"]
      );

    const sjDewPoint =
      atlObservatoryMetric(
        sj01,
        ["dew_point_C", "local_dew_point_c"]
      );

    const cuRain =
      atlObservatoryMetric(
        cu01,
        ["rain_1h_mm", "local_rain_1h_mm"]
      );

    const sjRain =
      atlObservatoryMetric(
        sj01,
        ["rain_1h_mm", "local_rain_1h_mm"]
      );

    const cuWind =
      atlObservatoryMetric(
        cu01,
        ["wind_speed_ms", "local_wind_speed_ms"]
      );

    const sjWind =
      atlObservatoryMetric(
        sj01,
        ["wind_speed_ms", "local_wind_speed_ms"]
      );

    const deltaTemp =
      atlObservatoryDifference(
        sjTemp,
        cuTemp
      );

    const deltaHumidity =
      atlObservatoryDifference(
        sjHumidity,
        cuHumidity
      );

    const deltaPressure =
      atlObservatoryDifference(
        sjPressure,
        cuPressure
      );

    const deltaDewPoint =
      atlObservatoryDifference(
        sjDewPoint,
        cuDewPoint
      );

    const deltaRain =
      atlObservatoryDifference(
        sjRain,
        cuRain
      );

    const deltaWind =
      atlObservatoryDifference(
        sjWind,
        cuWind
      );

    setText(
      "observatoryDeltaTemp",
      atlObservatoryDifferenceText(
        deltaTemp,
        "°C"
      )
    );

    setText(
      "observatoryDeltaHumidity",
      atlObservatoryDifferenceText(
        deltaHumidity,
        "%"
      )
    );

    setText(
      "observatoryDeltaPressure",
      atlObservatoryDifferenceText(
        deltaPressure,
        "hPa"
      )
    );

    setText(
      "observatoryDeltaDewPoint",
      atlObservatoryDifferenceText(
        deltaDewPoint,
        "°C"
      )
    );

    setText(
      "observatoryDeltaRain",
      atlObservatoryDifferenceText(
        deltaRain,
        "mm"
      )
    );

    setText(
      "observatoryDeltaWind",
      atlObservatoryDifferenceText(
        deltaWind,
        "m/s"
      )
    );

    const cuTimestamp =
      atlObservatoryTimestampMs(cu01);

    const sjTimestamp =
      atlObservatoryTimestampMs(sj01);

    const timeSkewSeconds =
      cuTimestamp !== null &&
      sjTimestamp !== null
        ? Math.abs(
            sjTimestamp -
            cuTimestamp
          ) / 1000
        : null;

    setText(
      "observatoryTimeSkew",
      timeSkewSeconds === null
        ? "—"
        : (
            timeSkewSeconds < 60
              ? `${Math.round(timeSkewSeconds)} s`
              : `${fmt(timeSkewSeconds / 60, 1)} min`
          )
    );

    const comparable =
      atlObservatoryComparableCount(
        cu01,
        sj01
      );

    setText(
      "observatoryComparable",
      `${comparable}/6 variables`
    );

    let interpretation =
      "Comparación disponible";

    if (
      timeSkewSeconds !== null &&
      timeSkewSeconds > 300
    ) {
      interpretation =
        "Desfase temporal elevado";
    } else if (
      comparable < 4
    ) {
      interpretation =
        "Cobertura comparativa parcial";
    } else if (
      deltaTemp !== null &&
      Math.abs(deltaTemp) >= 8
    ) {
      interpretation =
        "Contraste térmico significativo";
    } else if (
      deltaPressure !== null &&
      Math.abs(deltaPressure) >= 100
    ) {
      interpretation =
        "Contraste barométrico asociado al relieve";
    }

    setText(
      "observatoryInterpretation",
      interpretation
    );

    const bothOnline =
      upper(cu01.observation_state) ===
        "ONLINE" &&
      upper(sj01.observation_state) ===
        "ONLINE";

    statusElement.textContent =
      bothOnline
        ? "AMBAS ESTACIONES ONLINE"
        : "DISPONIBILIDAD PARCIAL";

  } catch (error) {
    console.error(
      "Error al cargar el observatorio:",
      error
    );

    statusElement.textContent =
      "ERROR DE CONSULTA";

    setText(
      "observatoryInterpretation",
      "No fue posible comparar las estaciones"
    );
  }
}


document.addEventListener(
  "DOMContentLoaded",
  () => {
    atlLoadObservatory();

    window.setInterval(
      atlLoadObservatory,
      REFRESH_MS
    );
  }
);


/* =========================================================
   ATMOSLINK_SELECTOR_STATUS_REFRESH_V1
   Mantiene actualizados los estados CU01/SJ01 del selector.
   ========================================================= */

(() => {
  "use strict";

  const STATIONS = [
    {
      id: "CU01",
      fallbackName: "Cerro Cuñacales",
    },
    {
      id: "SJ01",
      fallbackName: "Cerro San José",
    },
  ];

  function normalizeState(value) {
    const state = String(
      value || "UNKNOWN"
    ).toUpperCase();

    if (
      [
        "ONLINE",
        "FRESH",
        "CURRENT",
      ].includes(state)
    ) {
      return "ONLINE";
    }

    if (
      [
        "DELAYED",
        "WAITING",
      ].includes(state)
    ) {
      return "DELAYED";
    }

    if (
      [
        "STALE",
        "OFFLINE",
        "CRITICAL",
      ].includes(state)
    ) {
      return "OFFLINE";
    }

    return state;
  }

  function currentSelectorState(stationId) {
    const selector =
      document.getElementById(
        "stationSelector"
      );

    const option =
      Array.from(
        selector?.options || []
      ).find(
        item =>
          item.value === stationId
      );

    if (!option) {
      return "UNKNOWN";
    }

    const parts =
      option.textContent
        .split("·")
        .map(
          value => value.trim()
        );

    return (
      parts[parts.length - 1] ||
      "UNKNOWN"
    ).toUpperCase();
  }

  function waitSelectorRetry(
    milliseconds
  ) {
    return new Promise(
      resolve =>
        window.setTimeout(
          resolve,
          milliseconds
        )
    );
  }

  async function loadStationState(station) {
    let lastError = null;

    for (
      let attempt = 1;
      attempt <= 2;
      attempt += 1
    ) {
      try {
        const response = await fetch(
          `/api/station/latest?station_id=${encodeURIComponent(station.id)}`,
          {
            cache: "no-store",
            headers: {
              Accept: "application/json",
            },
          }
        );

        if (!response.ok) {
          throw new Error(
            `HTTP ${response.status}`
          );
        }

        const data =
          await response.json();

        return {
          id: station.id,
          name:
            data.station_name ||
            station.fallbackName,
          state: normalizeState(
            data.observation_state
          ),
        };

      } catch (error) {
        lastError = error;

        if (attempt === 1) {
          await waitSelectorRetry(
            1500
          );
        }
      }
    }

    console.warn(
      `Estado selector ${station.id}: `
      + "se conserva el último estado "
      + "por fallo transitorio.",
      lastError
    );

    return {
      id: station.id,
      name: station.fallbackName,
      state: currentSelectorState(
        station.id
      ),
    };
  }

  function updateOption(result) {
    const selector =
      document.getElementById(
        "stationSelector"
      );

    if (!selector) {
      return;
    }

    const option =
      Array.from(selector.options)
        .find(
          item =>
            item.value === result.id
        );

    if (!option) {
      return;
    }

    option.textContent =
      `${result.id} · ${result.name} · ${result.state}`;
  }

  async function refreshSelectorStates() {
    const results =
      await Promise.all(
        STATIONS.map(
          loadStationState
        )
      );

    results.forEach(
      updateOption
    );
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      refreshSelectorStates();

      window.setInterval(
        refreshSelectorStates,
        30000
      );
    }
  );

  window.addEventListener(
    "focus",
    refreshSelectorStates
  );
})();


/* =========================================================
   ATMOSLINK_HYBRID_CORRIDOR_V1
   CU01 local -> MID modelado -> SJ01 local
   ========================================================= */

(() => {
  "use strict";

  const HYBRID_MARKER =
    "ATMOSLINK_HYBRID_CORRIDOR_V1";

  function atlHybridNumber(value) {
    const number = Number(value);

    return Number.isFinite(number)
      ? number
      : null;
  }

  const ATMOSLINK_CORRIDOR_LAB_GUARD_V1 =
    "ATMOSLINK_CORRIDOR_LAB_GUARD_V1";

  function atlHybridIsLaboratoryStation(
    station
  ) {
    const values = [
      station?.deployment_mode,
      station?.validation_scope,
      station?.station_phase,
      station?.environment,
      station?.mode,
    ]
      .filter(
        value =>
          value !== null &&
          value !== undefined
      )
      .map(
        value =>
          String(value)
            .trim()
            .toUpperCase()
      );

    return values.some(
      value =>
        value.includes("LAB") ||
        value.includes("PREDESPLIEGUE") ||
        value.includes("PREDEPLOY")
    );
  }


  function atlHybridFormat(
    value,
    digits = 1
  ) {
    const number =
      atlHybridNumber(value);

    if (number === null) {
      return "—";
    }

    return number.toFixed(digits);
  }

  function atlHybridComparisonCell(
    sj01,
    formattedDifference,
    unit
  ) {
    if (
      atlHybridIsLaboratoryStation(
        sj01
      )
    ) {
      return (
        '<span class="atl-hybrid-not-comparable">' +
        '<strong>NO COMPARABLE</strong>' +
        '<small>SJ01 en laboratorio</small>' +
        '</span>'
      );
    }

    if (
      formattedDifference === null ||
      formattedDifference === undefined ||
      formattedDifference === "—"
    ) {
      return "—";
    }

    return (
      `${formattedDifference} ${unit} ` +
      `SJ01 − CU01`
    );
  }


  function atlHybridPick(
    object,
    keys
  ) {
    for (const key of keys) {
      const value = object?.[key];

      if (
        value !== null &&
        value !== undefined &&
        value !== ""
      ) {
        return value;
      }
    }

    return null;
  }

  async function atlHybridFetchStation(
    stationId
  ) {
    const response = await fetch(
      `/api/station/latest?station_id=${encodeURIComponent(stationId)}`,
      {
        cache: "no-store",
        headers: {
          Accept: "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(
        `${stationId}: HTTP ${response.status}`
      );
    }

    return response.json();
  }

  function atlHybridModelSource(core) {
    const sources =
      core?.atmospheric_corridor?.sources ??
      {};

    if (sources.ERA5) {
      return {
        name: "ERA5-Land",
        data: sources.ERA5,
      };
    }

    if (sources.NASA) {
      return {
        name: "NASA POWER",
        data: sources.NASA,
      };
    }

    return {
      name: "No disponible",
      data: null,
    };
  }

  function atlHybridPoint(
    source,
    pointName
  ) {
    return (
      source?.points?.[pointName] ??
      {}
    );
  }

  function atlHybridStationValues(
    station
  ) {
    return {
      temperature: atlHybridPick(
        station,
        [
          "temp_avg_C",
          "local_temp_avg_c",
          "temperature_c",
        ]
      ),

      humidity: atlHybridPick(
        station,
        [
          "hum_avg_pct",
          "local_hum_avg_pct",
          "humidity_pct",
        ]
      ),

      pressure: atlHybridPick(
        station,
        [
          "pres_avg_hPa",
          "local_press_hpa",
          "pressure_hpa",
        ]
      ),

      dewpoint: atlHybridPick(
        station,
        [
          "dew_point_C",
          "local_dew_point_c",
          "dewpoint_c",
        ]
      ),

      precipitation: atlHybridPick(
        station,
        [
          "rain_1h_mm",
          "local_rain_1h_mm",
          "precipitation_mm",
        ]
      ),

      wind: atlHybridPick(
        station,
        [
          "wind_speed_ms",
          "local_wind_speed_ms",
          "wind_ms",
        ]
      ),
    };
  }

  function atlHybridModelValues(
    point
  ) {
    return {
      temperature: atlHybridPick(
        point,
        [
          "temp_c",
          "temperature_c",
        ]
      ),

      humidity: atlHybridPick(
        point,
        [
          "rh_pct",
          "humidity_pct",
        ]
      ),

      pressure: atlHybridPick(
        point,
        [
          "press_hpa",
          "pressure_hpa",
        ]
      ),

      dewpoint: atlHybridPick(
        point,
        [
          "dewpoint_c",
        ]
      ),

      precipitation: atlHybridPick(
        point,
        [
          "precip_mm",
          "precipitation_mm",
        ]
      ),

      wind: atlHybridPick(
        point,
        [
          "wind_ms",
        ]
      ),
    };
  }

  function atlHybridSetText(
    id,
    value
  ) {
    const element =
      document.getElementById(id);

    if (element) {
      element.textContent = value;
    }
  }

  function atlHybridReplaceCardText(
    anchorId,
    replacements
  ) {
    const anchor =
      document.getElementById(anchorId);

    const card =
      anchor?.closest(
        "article, .atl-corridor-node, .atl-card, div"
      );

    if (!card) {
      return;
    }

    const elements =
      card.querySelectorAll(
        "span, small, p, strong"
      );

    elements.forEach(element => {
      const current =
        element.textContent
          .trim()
          .toUpperCase();

      for (
        const [expected, replacement]
        of replacements
      ) {
        if (
          current ===
          expected.toUpperCase()
        ) {
          element.textContent =
            replacement;
        }
      }
    });
  }

  function atlHybridTableRow(
    label,
    unit,
    cu01Value,
    midValue,
    sj01Value,
    digits = 3
  ) {
    const cu =
      atlHybridNumber(cu01Value);

    const mid =
      atlHybridNumber(midValue);

    const sj =
      atlHybridNumber(sj01Value);

    const delta =
      cu !== null && sj !== null
        ? sj - cu
        : null;

    return `
      <tr>
        <td>${label}</td>

        <td>
          ${atlHybridFormat(
            cu,
            digits
          )} ${unit}
          <span class="atl-badge atl-badge--ok">
            OBSERVADO
          </span>
        </td>

        <td>
          ${atlHybridFormat(
            mid,
            digits
          )} ${unit}
          <span class="atl-badge">
            MODELO
          </span>
        </td>

        <td>
          ${atlHybridFormat(
            sj,
            digits
          )} ${unit}
          <span class="atl-badge atl-badge--ok">
            OBSERVADO
          </span>
        </td>

        <td>
          ${
            atlHybridIsLaboratoryStation(sj01)
              ? `
                <span class="atl-hybrid-not-comparable">
                  <strong>NO COMPARABLE</strong>
                  <small>SJ01 en laboratorio</small>
                </span>
              `
              : `
                ${atlHybridFormat(
                  delta,
                  digits
                )} ${unit}
                <span class="atl-badge">
                  SJ01 − CU01
                </span>
              `
          }
        </td>
      </tr>
    `;
  }

  /* ATMOSLINK_STATION_RESPONSE_ISOLATION_V1 */
  let atlHybridRenderGeneration = 0;
  
  async function atlRenderHybridCorridor(
    core
  ) {
    const requestGeneration = ++atlHybridRenderGeneration;
    const source =
      atlHybridModelSource(core);

    if (!source.data) {
      return;
    }

    try {
      const [
        cu01,
        sj01,
      ] = await Promise.all([
        atlHybridFetchStation("CU01"),
        atlHybridFetchStation("SJ01"),
      ]);
      const cu01ResponseStation =
        String(cu01?.station_id || "")
          .trim()
          .toUpperCase();

      const sj01ResponseStation =
        String(sj01?.station_id || "")
          .trim()
          .toUpperCase();

      if (
        requestGeneration !== atlHybridRenderGeneration ||
        cu01ResponseStation !== "CU01" ||
        sj01ResponseStation !== "SJ01"
      ) {
        console.info(
          "Render híbrido descartado:",
          {
            requestGeneration,
            activeGeneration:
              atlHybridRenderGeneration,
            cu01ResponseStation,
            sj01ResponseStation,
          }
        );
        return;
      }


      const cu =
        atlHybridStationValues(cu01);

      const sj =
        atlHybridStationValues(sj01);

      const midPoint =
        atlHybridPoint(
          source.data,
          "MID_LINK"
        );

      const mid =
        atlHybridModelValues(
          midPoint
        );

      /*
       * Tarjetas principales
       */

      atlHybridSetText(
        "corridorApTemp",
        `${atlHybridFormat(
          cu.temperature,
          1
        )} °C`
      );

      atlHybridSetText(
        "corridorApPressure",
        `${atlHybridFormat(
          cu.pressure,
          1
        )} hPa`
      );

      atlHybridSetText(
        "corridorMidTemp",
        `${atlHybridFormat(
          mid.temperature,
          1
        )} °C`
      );

      atlHybridSetText(
        "corridorMidPressure",
        `${atlHybridFormat(
          mid.pressure,
          1
        )} hPa`
      );

      atlHybridSetText(
        "corridorSmTemp",
        `${atlHybridFormat(
          sj.temperature,
          1
        )} °C`
      );

      atlHybridSetText(
        "corridorSmPressure",
        `${atlHybridFormat(
          sj.pressure,
          1
        )} hPa`
      );

      /*
       * Diferencias mostradas en las flechas:
       * extremo real respecto del punto medio modelado.
       */

      const deltaCuMid =
        atlHybridNumber(
          cu.temperature
        ) !== null &&
        atlHybridNumber(
          mid.temperature
        ) !== null
          ? atlHybridNumber(
              mid.temperature
            ) -
            atlHybridNumber(
              cu.temperature
            )
          : null;

      const deltaMidSj =
        atlHybridNumber(
          sj.temperature
        ) !== null &&
        atlHybridNumber(
          mid.temperature
        ) !== null
          ? atlHybridNumber(
              sj.temperature
            ) -
            atlHybridNumber(
              mid.temperature
            )
          : null;

      atlHybridSetText(
        "corridorGradient1",
        `${atlHybridFormat(
          deltaCuMid,
          2
        )} °C`
      );

      atlHybridSetText(
        "corridorGradient2",
        `${atlHybridFormat(
          deltaMidSj,
          2
        )} °C`
      );

      atlHybridSetText(
        "corridorStatus",
        "LOCAL + MODELO + LOCAL"
      );

      atlHybridSetText(
        "corridorSourceLabel",
        `Extremos observados · punto medio ${source.name}`
      );

      /*
       * Cambiar semántica de las tarjetas AP y SM.
       */

      atlHybridReplaceCardText(
        "corridorApTemp",
        [
          [
            "ESTACIÓN LOCAL INSTALADA",
            "Estación meteorológica instalada",
          ],
          [
            "MEDICIÓN LOCAL",
            "MEDICIÓN LOCAL",
          ],
        ]
      );

      atlHybridReplaceCardText(
        "corridorSmTemp",
        [
          [
            "ESTIMACIÓN DEL MODELO",
            "Estación meteorológica instalada",
          ],
          [
            "ERA5-LAND",
            "MEDICIÓN LOCAL",
          ],
          [
            "NASA POWER",
            "MEDICIÓN LOCAL",
          ],
        ]
      );

      /*
       * Descripción e interpretación.
       */

      const section =
        document
          .getElementById(
            "corridorSmTemp"
          )
          ?.closest(
            "section"
          );

      if (section) {
        const paragraphs =
          section.querySelectorAll("p");

        paragraphs.forEach(
          paragraph => {
            const content =
              paragraph.textContent;

            if (
              content.includes(
                "Solo Cuñacales dispone"
              )
            ) {
              paragraph.textContent =
                "Perfil atmosférico híbrido: observaciones físicas en Cuñacales y San José, con estimación modelada en el punto medio.";
            }

            if (
              content.includes(
                "San José corresponde temporalmente a una estación física en laboratorio y todavía no representa"
              )
            ) {
              paragraph.innerHTML =
                "<strong>Interpretación científica:</strong> Cuñacales y San José corresponden a mediciones físicas. El punto medio representa una estimación espacial del modelo y no una estación instalada.";
            }
          }
        );
      }

      /*
       * Tabla híbrida.
       */

      const rows = [
        atlHybridTableRow(
          "Temperatura",
          "°C",
          cu.temperature,
          mid.temperature,
          sj.temperature,
          3
        ),

        atlHybridTableRow(
          "Humedad relativa",
          "%",
          cu.humidity,
          mid.humidity,
          sj.humidity,
          3
        ),

        atlHybridTableRow(
          "Presión",
          "hPa",
          cu.pressure,
          mid.pressure,
          sj.pressure,
          3
        ),

        atlHybridTableRow(
          "Punto de rocío",
          "°C",
          cu.dewpoint,
          mid.dewpoint,
          sj.dewpoint,
          3
        ),

        atlHybridTableRow(
          "Precipitación",
          "mm",
          cu.precipitation,
          mid.precipitation,
          sj.precipitation,
          3
        ),

        atlHybridTableRow(
          "Viento",
          "m/s",
          cu.wind,
          mid.wind,
          sj.wind,
          3
        ),
      ].join("");

      const table =
        document.getElementById(
          "corridorTable"
        );

      if (table) {
        table.innerHTML = `
          <table>
            <thead>
              <tr>
                <th>Variable</th>
                <th>AP Cuñacales · local</th>
                <th>Punto medio · ${source.name}</th>
                <th>SM San José · local</th>
                <th>Comparabilidad espacial</th>
              </tr>
            </thead>

            <tbody>
              ${rows}
            </tbody>
          </table>
        `;
      }

    } catch (error) {
      console.error(
        "AtmosLink Hybrid Corridor:",
        error
      );
    }
  }

  /*
   * Encadenar el parche después del renderer existente.
   */

  const previousRenderCorridor =
    renderCorridor;

  renderCorridor = function(core) {
    previousRenderCorridor(core);

    atlRenderHybridCorridor(core);
  };

  /*
   * El dashboard multiestación conserva una referencia
   * previa al renderer. La sustituimos también.
   */

  /*
   * Exponer el renderizador híbrido para que el ciclo
   * multiestación pueda ejecutarlo después del render original.
   */
  window.atlRenderHybridCorridor =
    atlRenderHybridCorridor;

  console.info(HYBRID_MARKER);
})();


/* =========================================================
   ATMOSLINK_SJ01_LABORATORY_MODE_V1
   Identificación visible de SJ01 durante el predespliegue.
   ========================================================= */

(() => {
  "use strict";

  function applySj01LaboratoryLabel() {
    /*
     * SJ01 ya entrega mediciones físicas desde Cerro San José.
     * Se desactiva el modificador visual heredado de laboratorio.
     */
    return;

    const temperatureElement =
      document.getElementById(
        "corridorSmTemp"
      );

    if (!temperatureElement) {
      return;
    }

    const card =
      temperatureElement.closest(
        "article, .atl-corridor-node, .atl-card"
      ) ||
      temperatureElement.parentElement
        ?.parentElement;

    if (card) {
      const paragraphs =
        card.querySelectorAll(
          "p, small, span"
        );

      paragraphs.forEach(element => {
        const text =
          element.textContent
            .trim()
            .toUpperCase();

        if (
          text ===
          "ESTIMACIÓN DEL MODELO"
        ) {
          element.textContent =
            "Estación física en laboratorio";
        }
      });

      if (
        !card.querySelector(
          ".atl-laboratory-badge"
        )
      ) {
        const badge =
          document.createElement(
            "span"
          );

        badge.className =
          "atl-laboratory-badge";

        badge.textContent =
          "PRUEBA DE LABORATORIO";

        const value =
          card.querySelector(
            "#corridorSmTemp"
          );

        if (value) {
          value.insertAdjacentElement(
            "beforebegin",
            badge
          );
        } else {
          card.appendChild(badge);
        }
      }
    }

    const section =
      temperatureElement.closest(
        "section"
      );

    if (!section) {
      return;
    }

    const paragraphs =
      section.querySelectorAll("p");

    paragraphs.forEach(paragraph => {
      const content =
        paragraph.textContent
          .trim();

      if (
        content.includes(
          "los valores del punto medio y San José"
        ) ||
        content.includes(
          "San José corresponde temporalmente a una estación física en laboratorio y todavía no representa"
        )
      ) {
        paragraph.innerHTML = `
          <strong>
            Estado de despliegue:
          </strong>
          Cuñacales corresponde a una medición de campo.
          San José corresponde temporalmente a pruebas
          funcionales realizadas en laboratorio.
          El punto medio es una estimación ERA5-Land.
          Los datos de SJ01 no deben interpretarse todavía
          como condiciones meteorológicas del Cerro San José.
        `;
      }
    });
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      applySj01LaboratoryLabel();

      const root =
        document.getElementById(
          "proDashboardRoot"
        ) ||
        document.body;

      const observer =
        new MutationObserver(
          applySj01LaboratoryLabel
        );

      observer.observe(
        root,
        {
          childList: true,
          subtree: true,
          characterData: true,
        }
      );
    }
  );
})();


/* =========================================================
   ATMOSLINK_SJ01_FIELD_CALIBRATION_UI_V1
   Reconciliación temporal de módulos científicos antiguos.
   ========================================================= */
(() => {
  "use strict";

  const MARKER =
    "ATMOSLINK_SJ01_FIELD_CALIBRATION_UI_V1";

  let applying = false;

  function selectedStation() {
    return (
      document.getElementById("stationSelector")
        ?.value || ""
    ).toUpperCase();
  }

  function replaceText(root, replacements) {
    const walker =
      document.createTreeWalker(
        root,
        NodeFilter.SHOW_TEXT
      );

    const nodes = [];

    while (walker.nextNode()) {
      nodes.push(walker.currentNode);
    }

    nodes.forEach(node => {
      let value = node.nodeValue;

      replacements.forEach(
        ([before, after]) => {
          value = value
            .split(before)
            .join(after);
        }
      );

      if (value !== node.nodeValue) {
        node.nodeValue = value;
      }
    });
  }

  function setValueAfterLabel(label, value) {
    const elements =
      Array.from(
        document.querySelectorAll(
          "span, small, div, strong"
        )
      );

    const labelElement =
      elements.find(
        element =>
          element.children.length === 0 &&
          element.textContent.trim() === label
      );

    const container =
      labelElement?.parentElement;

    if (!container) {
      return;
    }

    const candidates =
      Array.from(
        container.querySelectorAll(
          "span, strong, small, div"
        )
      ).filter(
        element =>
          element !== labelElement &&
          element.children.length === 0 &&
          element.textContent.trim()
      );

    if (candidates.length) {
      candidates[
        candidates.length - 1
      ].textContent = value;
    }
  }

  function reconcileSj01() {
    if (
      applying ||
      selectedStation() !== "SJ01"
    ) {
      return;
    }

    applying = true;

    try {
      replaceText(document.body, [
        [
          "PREDESPLIEGUE EN LABORATORIO",
          "CALIBRACIÓN DE CAMPO"
        ],
        [
          "Predespliegue en laboratorio",
          "Operación inicial en campo"
        ],
        [
          "SJ01 permanece en laboratorio.",
          "SJ01 está instalada en Cerro San José."
        ],
        [
          "La estación permanece en laboratorio.",
          "La estación está instalada en Cerro San José."
        ],
        [
          "Estación en laboratorio",
          "Operación inicial en campo"
        ],
        [
          "Estación no desplegada",
          "Acumulando pares horarios"
        ],
        [
          "Pendiente de traslado a Cerro San José",
          "Traslado a Cerro San José completado"
        ],
        [
          "Pendiente de instalación física",
          "Instalación física completada"
        ],
        [
          "Pendiente de calibración en campo",
          "Calibración de campo en curso"
        ],
        [
          "Sus datos no se comparan todavía con ERA5-Land ni NASA POWER para Cerro San José.",
          "Acumulando pares horarios de campo antes de habilitar la comparación con ERA5-Land y NASA POWER."
        ],
        [
          "El estado científico global se habilitará después de la instalación física en Cerro San José y de la generación de pares horarios comparables.",
          "La estación acumula pares horarios desde su instalación física; la validación se habilitará cuando exista cobertura suficiente."
        ],
        [
          "Este módulo permanecerá excluido mientras la estación continúe en laboratorio.",
          "Módulo en espera mientras se acumulan pares horarios de calibración de campo."
        ],
        [
          "La interpretación automática se habilitará después del despliegue físico y la generación de pares horarios comparables en Cerro San José.",
          "La interpretación automática se habilitará al alcanzar cobertura horaria suficiente en Cerro San José."
        ]
      ]);

      setValueAfterLabel(
        "Modo",
        "FIELD"
      );

      setValueAfterLabel(
        "Ubicación científica",
        "Cerro San José"
      );

      setValueAfterLabel(
        "Criterio",
        "Operación inicial en campo"
      );

      setValueAfterLabel(
        "Estado estadístico",
        "EN ACUMULACIÓN"
      );

      document
        .querySelectorAll(
          ".atl-campaign-status__summary strong"
        )
        .forEach(
          element => {
            element.textContent =
              "OPERACIÓN INICIAL";
          }
        );

      console.info(MARKER);
    } finally {
      applying = false;
    }
  }

  let timer = null;

  function schedule() {
    window.clearTimeout(timer);
    timer =
      window.setTimeout(
        reconcileSj01,
        80
      );
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      schedule();

      document
        .getElementById("stationSelector")
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
        reconcileSj01,
        5000
      );
    }
  );
})();


/* =========================================================
   ATMOSLINK_SJ01_FIELD_SEMANTICS_V2
   Coherencia del scoreboard y corredor atmosférico.
   ========================================================= */
(() => {
  "use strict";

  let atlSj01SemanticsRunning = false;
  let atlSj01SemanticsTimer = null;

  function atlSj01Selected() {
    return (
      document.getElementById("stationSelector")
        ?.value || ""
    ).toUpperCase() === "SJ01";
  }

  function atlLeafElements(root) {
    return Array.from(
      root.querySelectorAll(
        "div, span, strong, small, p"
      )
    ).filter(
      element =>
        element.children.length === 0
    );
  }

  function atlReplaceExact(
    root,
    before,
    after
  ) {
    atlLeafElements(root).forEach(
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

  function atlFindSmallestContainer(
    start,
    requiredTexts
  ) {
    let current = start;

    while (
      current &&
      current !== document.body
    ) {
      const content =
        current.textContent || "";

      if (
        requiredTexts.every(
          value =>
            content.includes(value)
        )
      ) {
        return current;
      }

      current = current.parentElement;
    }

    return null;
  }

  function atlFindLeaf(text) {
    return atlLeafElements(
      document.body
    ).find(
      element =>
        element.textContent.trim() ===
        text
    );
  }

  function atlCorrectScoreboard() {
    const title =
      atlFindLeaf(
        "ATMOSLINK SCIENTIFIC SCOREBOARD"
      );

    if (!title) {
      return;
    }

    const scoreboard =
      atlFindSmallestContainer(
        title,
        [
          "Madurez estadística",
          "Pares efectivos",
          "Scientific Readiness",
        ]
      );

    if (!scoreboard) {
      return;
    }

    atlReplaceExact(
      scoreboard,
      "EXCLUIDA",
      "OPERACIÓN INICIAL"
    );

    atlReplaceExact(
      scoreboard,
      "LABORATORY",
      "FIELD"
    );

    atlReplaceExact(
      scoreboard,
      "Estación en laboratorio",
      "Operación inicial en campo"
    );

    atlReplaceExact(
      scoreboard,
      "Nivel actual de cobertura",
      "Acumulando cobertura horaria"
    );

    const labels =
      atlLeafElements(scoreboard);

    labels.forEach(
      label => {
        const value =
          label.textContent.trim();

        if (
          value ===
          "Validación de modelos"
        ) {
          const container =
            label.parentElement;

          if (container) {
            atlReplaceExact(
              container,
              "EXCLUIDA",
              "CONDICIONADA A COBERTURA"
            );
          }
        }

        if (
          value ===
          "Madurez estadística"
        ) {
          const container =
            label.parentElement;

          if (container) {
            atlReplaceExact(
              container,
              "EXCLUIDA",
              "EN ACUMULACIÓN"
            );
          }
        }

        if (
          value ===
          "Preparación de publicación"
        ) {
          const container =
            label.parentElement;

          if (container) {
            atlReplaceExact(
              container,
              "0/6",
              "3/6"
            );
          }
        }
      }
    );
  }

  function atlCorrectCorridor() {
    const heading =
      atlFindLeaf(
        "Cuñacales → punto medio → San José"
      );

    if (!heading) {
      return;
    }

    const corridor =
      atlFindSmallestContainer(
        heading,
        [
          "Cuñacales",
          "Punto medio",
          "San José",
          "Interpretación científica",
        ]
      );

    if (!corridor) {
      return;
    }

    const sanJoseTitle =
      atlLeafElements(corridor)
        .find(
          element =>
            element.textContent.trim() ===
            "San José"
        );

    if (sanJoseTitle) {
      const sanJoseCard =
        atlFindSmallestContainer(
          sanJoseTitle,
          [
            "San José",
            "°C",
            "hPa",
          ]
        );

      if (sanJoseCard) {
        atlReplaceExact(
          sanJoseCard,
          "Estimación del modelo",
          "Estación meteorológica instalada"
        );

        atlReplaceExact(
          sanJoseCard,
          "ERA5-LAND",
          "MEDICIÓN LOCAL"
        );

        atlReplaceExact(
          sanJoseCard,
          "NASA POWER",
          "MEDICIÓN LOCAL"
        );

        const hasLocalBadge =
          atlLeafElements(
            sanJoseCard
          ).some(
            element =>
              element.textContent
                .trim() ===
              "MEDICIÓN LOCAL"
          );

        if (!hasLocalBadge) {
          const badge =
            document.createElement(
              "span"
            );

          badge.textContent =
            "MEDICIÓN LOCAL";

          badge.style.display =
            "inline-block";
          badge.style.marginTop =
            "8px";
          badge.style.padding =
            "4px 10px";
          badge.style.borderRadius =
            "999px";
          badge.style.background =
            "#e7f7ef";
          badge.style.color =
            "#087443";
          badge.style.fontWeight =
            "700";
          badge.style.fontSize =
            "11px";

          sanJoseTitle.insertAdjacentElement(
            "afterend",
            badge
          );
        }
      }
    }

    atlLeafElements(corridor)
      .forEach(
        element => {
          const value =
            element.textContent.trim();

          if (
            value.includes(
              "los valores del punto medio y San José no corresponden"
            ) ||
            value.includes(
              "Los valores del punto medio y San José no corresponden"
            )
          ) {
            element.innerHTML =
              "<strong>Interpretación científica:</strong> "
              + "Cuñacales y San José corresponden a "
              + "mediciones físicas locales. Únicamente el "
              + "punto medio representa una estimación "
              + "espacial de ERA5-Land.";
          }
        }
      );
  }

  function atlApplySj01FieldSemantics() {
    if (
      atlSj01SemanticsRunning ||
      !atlSj01Selected()
    ) {
      return;
    }

    atlSj01SemanticsRunning = true;

    try {
      atlCorrectScoreboard();
      atlCorrectCorridor();
    } finally {
      atlSj01SemanticsRunning = false;
    }
  }

  function atlScheduleSj01Semantics() {
    window.clearTimeout(
      atlSj01SemanticsTimer
    );

    atlSj01SemanticsTimer =
      window.setTimeout(
        atlApplySj01FieldSemantics,
        100
      );
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      atlScheduleSj01Semantics();

      document
        .getElementById(
          "stationSelector"
        )
        ?.addEventListener(
          "change",
          atlScheduleSj01Semantics
        );

      const observer =
        new MutationObserver(
          atlScheduleSj01Semantics
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
        atlApplySj01FieldSemantics,
        5000
      );
    }
  );

  console.info(
    "ATMOSLINK_SJ01_FIELD_SEMANTICS_V2"
  );
})();


/* =========================================================
   ATMOSLINK_SJ01_OPERATIONAL_SEMANTICS_V3
   Estado científico: operación inicial y cobertura pendiente.
   ========================================================= */
(() => {
  "use strict";

  let atlV3Running = false;
  let atlV3Timer = null;

  function atlV3IsSj01() {
    return (
      document.getElementById(
        "stationSelector"
      )?.value || ""
    ).toUpperCase() === "SJ01";
  }

  function atlV3Leaves(root) {
    return Array.from(
      root.querySelectorAll(
        "div, span, strong, small, p"
      )
    ).filter(
      element =>
        element.children.length === 0
    );
  }

  function atlV3Replace(
    root,
    before,
    after
  ) {
    atlV3Leaves(root).forEach(
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

  function atlV3FindLeaf(value) {
    return atlV3Leaves(
      document.body
    ).find(
      element =>
        element.textContent.trim() ===
        value
    );
  }

  function atlV3Container(
    start,
    required
  ) {
    let current = start;

    while (
      current &&
      current !== document.body
    ) {
      const content =
        current.textContent || "";

      if (
        required.every(
          value =>
            content.includes(value)
        )
      ) {
        return current;
      }

      current = current.parentElement;
    }

    return null;
  }

  function atlV3Readiness() {
    const title =
      atlV3FindLeaf(
        "SCIENTIFIC READINESS LEVEL"
      );

    if (!title) {
      return;
    }

    const panel =
      atlV3Container(
        title,
        [
          "Laboratorio",
          "Transporte",
          "Instalación",
          "Operación",
          "Validación",
        ]
      );

    if (!panel) {
      return;
    }

    atlV3Replace(
      panel,
      "100%",
      "50%"
    );

    atlV3Replace(
      panel,
      "CALIBRACIÓN DE CAMPO",
      "OPERACIÓN INICIAL EN CAMPO"
    );

    atlV3Replace(
      panel,
      "Calibración",
      "Estabilización"
    );

    atlV3Replace(
      panel,
      "Calibración de campo",
      "Operación inicial en campo"
    );

    atlV3Replace(
      panel,
      "Calibración de campo y acumulación de pares horarios",
      "Estabilización operativa y acumulación de pares horarios"
    );

    const progressBars =
      panel.querySelectorAll(
        '[role="progressbar"], progress'
      );

    progressBars.forEach(
      bar => {
        if (
          bar.tagName.toLowerCase() ===
          "progress"
        ) {
          bar.max = 100;
          bar.value = 50;
        }

        bar.setAttribute(
          "aria-valuenow",
          "50"
        );
      }
    );
  }

  function atlV3Scoreboard() {
    const title =
      atlV3FindLeaf(
        "ATMOSLINK SCIENTIFIC SCOREBOARD"
      );

    if (!title) {
      return;
    }

    const panel =
      atlV3Container(
        title,
        [
          "Madurez estadística",
          "Pares efectivos",
          "Scientific Readiness",
        ]
      );

    if (!panel) {
      return;
    }

    atlV3Replace(
      panel,
      "EN CALIBRACIÓN",
      "OPERACIÓN INICIAL"
    );

    atlV3Replace(
      panel,
      "EXCLUIDA",
      "PENDIENTE DE COBERTURA"
    );

    atlV3Replace(
      panel,
      "EN ACUMULACIÓN",
      "ACUMULANDO COBERTURA"
    );

    atlV3Replace(
      panel,
      "Calibración de campo",
      "Operación inicial en campo"
    );

    atlV3Replace(
      panel,
      "Validación de modelos",
      "Validación científica"
    );
  }

  function atlV3Validation() {
    const title =
      atlV3FindLeaf(
        "SCIENTIFIC VALIDATION STATUS"
      );

    if (!title) {
      return;
    }

    const panel =
      atlV3Container(
        title,
        [
          "ERA5-Land",
          "NASA POWER",
          "Cobertura efectiva",
          "Criterio",
        ]
      );

    if (!panel) {
      return;
    }

    atlV3Replace(
      panel,
      "EXCLUIDA",
      "PENDIENTE DE COBERTURA"
    );

    atlV3Replace(
      panel,
      "Calibración de campo",
      "Operación inicial en campo"
    );

    atlV3Replace(
      panel,
      "Estación no desplegada",
      "Acumulando pares horarios"
    );
  }

  function atlV3Campaign() {
    const title =
      atlV3FindLeaf(
        "SCIENTIFIC CAMPAIGN STATUS"
      );

    if (!title) {
      return;
    }

    const panel =
      atlV3Container(
        title,
        [
          "Scientific Confidence",
          "Pares efectivos",
          "Ubicación científica",
        ]
      );

    if (!panel) {
      return;
    }

    atlV3Replace(
      panel,
      "EXCLUIDA",
      "OPERACIÓN INICIAL"
    );

    atlV3Replace(
      panel,
      "EN CALIBRACIÓN",
      "OPERACIÓN INICIAL"
    );

    atlV3Replace(
      panel,
      "EN ACUMULACIÓN",
      "ACUMULANDO COBERTURA"
    );

    atlV3Replace(
      panel,
      "Calibración de campo",
      "Operación inicial en campo"
    );

    atlV3Leaves(panel).forEach(
      element => {
        const value =
          element.textContent.trim();

        if (
          value.includes(
            "no debe incorporarse todavía"
          )
        ) {
          element.textContent =
            "SJ01 se encuentra en operación inicial. "
            + "La validación científica comenzará "
            + "cuando exista cobertura horaria suficiente.";
        }
      }
    );
  }

  function atlV3Apply() {
    if (
      atlV3Running ||
      !atlV3IsSj01()
    ) {
      return;
    }

    atlV3Running = true;

    try {
      atlV3Readiness();
      atlV3Scoreboard();
      atlV3Validation();
      atlV3Campaign();
    } finally {
      atlV3Running = false;
    }
  }

  function atlV3Schedule() {
    window.clearTimeout(
      atlV3Timer
    );

    atlV3Timer =
      window.setTimeout(
        atlV3Apply,
        120
      );
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      atlV3Schedule();

      document
        .getElementById(
          "stationSelector"
        )
        ?.addEventListener(
          "change",
          atlV3Schedule
        );

      const observer =
        new MutationObserver(
          atlV3Schedule
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
        atlV3Apply,
        3000
      );
    }
  );

  console.info(
    "ATMOSLINK_SJ01_OPERATIONAL_SEMANTICS_V3"
  );
})();


/* =========================================================
   ATMOSLINK_CORRIDOR_TWO_LOCAL_STATIONS_V1
   Cuñacales y San José son estaciones físicas locales.
   ========================================================= */
(() => {
  "use strict";

  let atlCorridorLocalRunning = false;

  function atlCorridorLeaves(root) {
    return Array.from(
      root.querySelectorAll(
        "div, span, strong, small, p"
      )
    ).filter(
      element =>
        element.children.length === 0
    );
  }

  function atlFindCard(element) {
    let current = element;

    while (
      current &&
      current !== document.body
    ) {
      const content =
        current.textContent || "";

      if (
        content.includes("San José") &&
        !content.includes("Punto medio") &&
        !content.includes("Cuñacales")
      ) {
        return current;
      }

      current = current.parentElement;
    }

    return null;
  }

  function atlReplaceExact(
    root,
    before,
    after
  ) {
    atlCorridorLeaves(root).forEach(
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

  function atlApplyCorridorLocalStations() {
    if (atlCorridorLocalRunning) {
      return;
    }

    const selectedStation =
      (
        document.getElementById(
          "stationSelector"
        )?.value || ""
      ).toUpperCase();

    if (selectedStation !== "SJ01") {
      return;
    }

    const smTemperature =
      document.getElementById(
        "corridorSmTemp"
      );

    if (!smTemperature) {
      return;
    }

    atlCorridorLocalRunning = true;

    try {
      const sanJoseCard =
        atlFindCard(
          smTemperature
        );

      if (sanJoseCard) {
        atlReplaceExact(
          sanJoseCard,
          "Estimación del modelo",
          "Estación local instalada"
        );

        atlReplaceExact(
          sanJoseCard,
          "ERA5-LAND",
          "MEDICIÓN LOCAL"
        );

        atlReplaceExact(
          sanJoseCard,
          "NASA POWER",
          "MEDICIÓN LOCAL"
        );

        const hasLocalLabel =
          atlCorridorLeaves(
            sanJoseCard
          ).some(
            element =>
              element.textContent.trim() ===
              "MEDICIÓN LOCAL"
          );

        if (!hasLocalLabel) {
          const stationTitle =
            atlCorridorLeaves(
              sanJoseCard
            ).find(
              element =>
                element.textContent.trim() ===
                "San José"
            );

          if (stationTitle) {
            const label =
              document.createElement(
                "span"
              );

            label.textContent =
              "MEDICIÓN LOCAL";

            label.style.display =
              "table";
            label.style.margin =
              "8px auto 0";
            label.style.padding =
              "4px 10px";
            label.style.borderRadius =
              "999px";
            label.style.background =
              "#e7f7ef";
            label.style.color =
              "#087443";
            label.style.fontSize =
              "11px";
            label.style.fontWeight =
              "700";

            stationTitle.insertAdjacentElement(
              "afterend",
              label
            );
          }
        }
      }

      const section =
        smTemperature.closest(
          "section"
        );

      if (section) {
        atlCorridorLeaves(section)
          .forEach(
            element => {
              const content =
                element.textContent.trim();

              if (
                content.includes(
                  "los valores del punto medio y San José no corresponden"
                ) ||
                content.includes(
                  "Los valores del punto medio y San José no corresponden"
                )
              ) {
                element.innerHTML =
                  "<strong>Interpretación científica:</strong> "
                  + "Cuñacales y San José corresponden "
                  + "a estaciones meteorológicas físicas "
                  + "instaladas. Únicamente el punto medio "
                  + "representa una estimación espacial "
                  + "de ERA5-Land.";
              }
            }
          );
      }
    } finally {
      atlCorridorLocalRunning = false;
    }
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      atlApplyCorridorLocalStations();

      document
        .getElementById(
          "stationSelector"
        )
        ?.addEventListener(
          "change",
          atlApplyCorridorLocalStations
        );

      const observer =
        new MutationObserver(
          () => {
            window.requestAnimationFrame(
              atlApplyCorridorLocalStations
            );
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

      window.setInterval(
        atlApplyCorridorLocalStations,
        2000
      );
    }
  );

  console.info(
    "ATMOSLINK_CORRIDOR_TWO_LOCAL_STATIONS_V1"
  );
})();
