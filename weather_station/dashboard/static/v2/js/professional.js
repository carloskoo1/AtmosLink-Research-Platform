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
function renderWeather(l){setText("temperatureValue",fmt(l.local_temp_avg_c??l.temp_avg_C));setText("humidityValue",fmt(l.local_hum_avg_pct??l.hum_avg_pct));setText("pressureValue",fmt(l.local_press_hpa??l.pres_avg_hPa));setText("dewPointValue",fmt(l.local_dew_point_c??l.dew_point_C));setText("rainHourValue",fmt(l.local_rain_1h_mm??l.rain_1h_mm,2));setText("rainTotalValue",fmt(l.local_rain_total_mm??l.rain_total_mm,2));setText("rainState",upper(l.rain_state));setText("weatherTimestamp",dateTime(l.weather_timestamp_local??l.timestamp_local))}
function historyRows(h){if(Array.isArray(h))return h;if(Array.isArray(h?.history))return h.history;if(Array.isArray(h?.data))return h.data;if(Array.isArray(h?.rows))return h.rows;return[]}
function choose(row,keys){for(const key of keys){const v=row?.[key];if(v!==null&&v!==undefined&&Number.isFinite(Number(v)))return Number(v)}return null}
function renderSparkline(containerId,values,unit,trendId){const container=$(containerId);if(!container)return;const clean=values.filter(v=>Number.isFinite(v));if(clean.length<2){container.innerHTML='<div class="atl-chart-empty">Datos históricos insuficientes</div>';setText(trendId,"—");return}const width=720,height=220,padX=18,padY=18,min=Math.min(...clean),max=Math.max(...clean),range=max-min||1;const points=clean.map((value,index)=>{const x=padX+index*((width-padX*2)/(clean.length-1));const y=height-padY-((value-min)/range)*(height-padY*2);return`${x.toFixed(2)},${y.toFixed(2)}`}).join(" ");const delta=clean.at(-1)-clean[0];setText(trendId,`${delta>=0?"+":""}${fmt(delta,2)} ${unit}`);container.innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img"><defs><linearGradient id="fill-${containerId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1774c6" stop-opacity=".22"/><stop offset="100%" stop-color="#1774c6" stop-opacity="0"/></linearGradient></defs><polygon points="${padX},${height-padY} ${points} ${width-padX},${height-padY}" fill="url(#fill-${containerId})"/><polyline points="${points}" fill="none" stroke="#0f6cbd" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><text x="${padX}" y="16" fill="#60738c" font-size="12">máx ${fmt(max,2)} ${unit}</text><text x="${padX}" y="${height-4}" fill="#60738c" font-size="12">mín ${fmt(min,2)} ${unit}</text></svg>`}
function renderHistory(h){const rows=historyRows(h).slice(-1440);renderSparkline("temperatureChart",rows.map(r=>choose(r,["local_temp_avg_c","temp_avg_C","temperature_c","temp_c"])),"°C","temperatureTrend");renderSparkline("humidityChart",rows.map(r=>choose(r,["local_hum_avg_pct","hum_avg_pct","humidity_pct","rh_pct"])),"%","humidityTrend");renderSparkline("pressureChart",rows.map(r=>choose(r,["local_press_hpa","pres_avg_hPa","pressure_hpa","press_hpa"])),"hPa","pressureTrend");renderSparkline("rainChart",rows.map(r=>choose(r,["local_rain_1h_mm","rain_1h_mm","precip_mm","rain_mm"])),"mm","rainTrend")}
function source(core){const s=core?.atmospheric_corridor?.sources??{};return s.ERA5??s.NASA??null}
function point(s,n){return s?.points?.[n]??{}}
function renderCorridor(core){const s=source(core);setText("corridorStatus",core?.atmospheric_corridor?.message?"AVAILABLE":"NO DATA");if(!s){$("corridorTable").innerHTML='<div class="atl-chart-empty">Sin corredor atmosférico disponible</div>';return}const ap=point(s,"AP_CUNACALES"),mid=point(s,"MID_LINK"),sm=point(s,"SM_SAN_JOSE");setText("corridorApTemp",`${fmt(ap.temp_c)} °C`);setText("corridorMidTemp",`${fmt(mid.temp_c)} °C`);setText("corridorSmTemp",`${fmt(sm.temp_c)} °C`);setText("corridorApPressure",`${fmt(ap.press_hpa)} hPa`);setText("corridorMidPressure",`${fmt(mid.press_hpa)} hPa`);setText("corridorSmPressure",`${fmt(sm.press_hpa)} hPa`);setText("corridorGradient1",`${fmt(number(mid.temp_c)-number(ap.temp_c),2)} °C`);setText("corridorGradient2",`${fmt(number(sm.temp_c)-number(mid.temp_c),2)} °C`);const rows=(Array.isArray(s.gradients)?s.gradients:[]).map(i=>`<tr><td>${i.label??i.variable??"—"}</td><td>${fmt(i.ap_value,3)} ${i.unit??""}</td><td>${fmt(i.mid_value,3)} ${i.unit??""}</td><td>${fmt(i.sm_value,3)} ${i.unit??""}</td><td>${fmt(i.gradient_ap_to_sm,3)} ${i.unit??""}</td></tr>`).join("");$("corridorTable").innerHTML=`<table><thead><tr><th>Variable</th><th>AP Cuñacales</th><th>Punto medio</th><th>SM San José</th><th>Gradiente AP→SM</th></tr></thead><tbody>${rows}</tbody></table>`}
function renderQuality(latest){const q=latest.scientific_quality??{};const items=[["BME280",q.bme280],["Pluviómetro",q.rain_gauge],["Anemómetro",q.anemometer],["ERA5-Land",q.era5],["NASA POWER",q.nasa_power],["Radioenlace",q.radio_link]];$("qualityList").innerHTML=items.map(([label,state])=>{const x=qualityState(state);return`<div class="atl-quality-row"><span>${label}</span><div class="atl-quality-row__track"><div class="atl-quality-row__bar atl-quality-row__bar--${x.variant}" style="width:${x.score}%"></div></div><strong>${upper(state)}</strong></div>`}).join("");const c=items.map(([,s])=>qualityState(s)).filter(i=>i.variant!=="disabled");const score=c.length?Math.round(c.reduce((sum,i)=>sum+i.score,0)/c.length):0;setText("scientificHealthScore",`${score}%`);$("scientificHealthBar").style.width=`${score}%`;setText("scientificHealthLabel",score>=90?"Condición científica óptima":score>=70?"Condición científica aceptable":"Requiere revisión")}
function renderRadio(l){const q=l.scientific_quality??{};setText("radioStatus",upper(q.radio_link));setText("radioRole",l.radio_role??l.radio_local_role);setText("radioRssi",l.radio_sta_dl_rssi??l.radio_rssi_c0p??l.radio_rssi_c0e??"—");setText("radioSnr",l.radio_snr_dl);setText("radioMcs",l.radio_mcs_dl);setText("radioDl",l.radio_dl_rate);setText("radioUl",l.radio_ul_rate);setText("radioNote",l.radio_note??l.radio_error??"Sin observaciones")}
function renderAlerts(core){const a=Array.isArray(core?.alerts?.alerts)?core.alerts.alerts:[];setText("alertCount",a.length);$("alertList").innerHTML=a.length?a.map(x=>`<article class="atl-alert-item ${["DANGER","CRITICAL"].includes(upper(x.severity))?"atl-alert-item--danger":""}"><strong>${x.title??"Alerta"}</strong><p>${x.message??"Sin descripción"}</p></article>`).join(""):'<div class="atl-chart-empty">No existen alertas activas</div>'}
function eventRows(e){if(Array.isArray(e))return e;if(Array.isArray(e?.events))return e.events;if(Array.isArray(e?.data))return e.data;return[]}
function renderEvents(e){const rows=eventRows(e).slice(0,8);$("eventList").innerHTML=rows.length?rows.map(x=>`<article class="atl-event-item"><time>${dateTime(x.timestamp??x.created_at??x.event_time??x.datetime)}</time><div><strong>${x.title??x.category??"Evento"}</strong><p>${x.description??x.message??x.severity??"—"}</p></div></article>`).join(""):'<div class="atl-chart-empty">No hay eventos recientes</div>'}
function renderFooter(p){setText("lastObservation",dateTime(p.health.latest_observation??p.latest.timestamp_local));setText("lastRefresh",dateTime(new Date().toISOString()));setText("footerState",p.errors.length?"DATOS PARCIALES":"EN LÍNEA");setText("connectionState",p.errors.length?"Datos parciales":"Plataforma conectada");const n=$("partialDataNotice");if(p.errors.length){n.hidden=false;n.textContent=`Carga parcial. Endpoints no disponibles: ${p.errors.join(", ")}`}else{n.hidden=true;n.textContent=""}}
async function refresh(){const root=$("proDashboardRoot");root?.classList.add("atl-loading");try{const p=await loadAll();renderTop(p);renderWeather(p.latest);renderHistory(p.history);renderCorridor(p.core);renderQuality(p.latest);renderRadio(p.latest);renderAlerts(p.core);renderEvents(p.events);renderFooter(p)}catch(error){console.error(error);setText("connectionState","Error de conexión");setText("footerState","ERROR")}finally{root?.classList.remove("atl-loading")}}
document.addEventListener("DOMContentLoaded",()=>{refresh();window.setInterval(refresh,REFRESH_MS)});

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
