#!/usr/bin/env python3
"""AtmosLink Scientific Agent v0.2.

Read-only analytical interface over the validated AtmosLink SQLite store.
No command in this module may modify scientific source data.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_DB = Path(
    "/home/carlos/Proyectos/EstacionMeteorologica/SQLite/CU01/weather_local.db"
)
VERSION = "0.4.0"


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


def scalar(conn: sqlite3.Connection, sql: str, params=()):
    row = conn.execute(sql, params).fetchone()
    return None if row is None else row[0]


def latest_status(conn: sqlite3.Connection) -> dict:
    stations = {}
    for station_id in ("CU01", "SJ01"):
        row = conn.execute(
            """
            SELECT station_id, station_name, weather_timestamp_local,
                   local_temp_avg_c, local_hum_avg_pct, local_press_hpa,
                   local_wind_speed_ms, local_wind_gust_ms
            FROM master_observations_multistation
            WHERE station_id = ? AND weather_timestamp_local IS NOT NULL
            ORDER BY weather_timestamp_utc DESC LIMIT 1
            """,
            (station_id,),
        ).fetchone()
        stations[station_id] = dict(row) if row else None

    rf = conn.execute(
        """
        SELECT timestamp_local, mcs_dl, mcs_ul, snr_dl, snr_ul,
               rssi_c0p, rssi_c1p, dl_rate, ul_rate
        FROM radio_link_local
        WHERE error IS NULL OR error = ''
        ORDER BY timestamp_utc DESC LIMIT 1
        """
    ).fetchone()
    throughput = conn.execute(
        """
        SELECT timestamp_start_local, direction, status,
               measured_throughput_mbps, ping_rtt_avg_ms,
               retransmits, operating_frequency_mhz,
               channel_bandwidth_mhz, campaign_id
        FROM active_throughput_6g
        ORDER BY timestamp_start_utc DESC LIMIT 1
        """
    ).fetchone()

    return {
        "agent_version": VERSION,
        "database": "read-only",
        "stations": stations,
        "latest_rf": dict(rf) if rf else None,
        "latest_active_throughput": dict(throughput) if throughput else None,
        "counts": {
            "master_observations_multistation": scalar(
                conn, "SELECT COUNT(*) FROM master_observations_multistation"
            ),
            "radio_link_local": scalar(conn, "SELECT COUNT(*) FROM radio_link_local"),
            "active_throughput_6g": scalar(conn, "SELECT COUNT(*) FROM active_throughput_6g"),
            "scientific_hourly_6g_general": scalar(
                conn, "SELECT COUNT(*) FROM scientific_hourly_6g_general"
            ),
        },
    }


def _mean(values):
    clean = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    return statistics.fmean(clean) if clean else None


def _corr(xs, ys):
    pairs = [(float(x), float(y)) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    xvals, yvals = zip(*pairs)
    mx, my = statistics.fmean(xvals), statistics.fmean(yvals)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    denx = math.sqrt(sum((x - mx) ** 2 for x in xvals))
    deny = math.sqrt(sum((y - my) ** 2 for y in yvals))
    if denx == 0 or deny == 0:
        return None
    return num / (denx * deny)


def analyze_window(conn: sqlite3.Connection, hours: int) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = conn.execute(
        """
        SELECT * FROM scientific_hourly_6g_general
        WHERE hour_utc >= ?
        ORDER BY hour_utc
        """,
        (cutoff.isoformat(),),
    ).fetchall()
    data = [dict(r) for r in rows]

    metrics = [
        "dl_snr_mean_db", "ul_snr_mean_db", "dl_rssi_mean_dbm",
        "ul_rssi_mean_dbm", "dl_active_measured_throughput_mbps_mean",
        "ul_active_measured_throughput_mbps_mean", "dl_active_ping_rtt_avg_ms_mean",
    ]
    weather = [
        "cu01_temp_mean_c", "cu01_rh_mean_pct", "cu01_press_median_hpa",
        "cu01_wind_mean_ms", "sj01_temp_mean_c", "sj01_rh_mean_pct",
        "sj01_press_median_hpa", "sj01_wind_mean_ms",
    ]
    summary = {m: _mean([r.get(m) for r in data]) for m in metrics + weather}
    correlations = {}
    for metric in metrics:
        for meteo in weather:
            value = _corr([r.get(metric) for r in data], [r.get(meteo) for r in data])
            if value is not None:
                correlations[f"{metric}__vs__{meteo}"] = round(value, 4)

    strongest = sorted(
        correlations.items(), key=lambda kv: abs(kv[1]), reverse=True
    )[:12]

    return {
        "window_hours_requested": hours,
        "hourly_rows": len(data),
        "first_hour_utc": data[0]["hour_utc"] if data else None,
        "last_hour_utc": data[-1]["hour_utc"] if data else None,
        "means": summary,
        "strongest_correlations": dict(strongest),
        "warning": "Correlations are exploratory and do not imply causality.",
    }


def campaign_summary(conn: sqlite3.Connection, campaign_id: str) -> dict:
    rows = conn.execute(
        """
        SELECT direction, status, operating_frequency_mhz, channel_bandwidth_mhz,
               measured_throughput_mbps, ping_rtt_avg_ms, retransmits,
               dl_snr_db, ul_snr_db, dl_rssi_dbm, ul_rssi_dbm
        FROM active_throughput_6g
        WHERE campaign_id = ?
        ORDER BY timestamp_start_utc
        """,
        (campaign_id,),
    ).fetchall()
    groups = defaultdict(list)
    for row in rows:
        key = (
            row["direction"], row["operating_frequency_mhz"],
            row["channel_bandwidth_mhz"], row["status"]
        )
        groups[key].append(dict(row))
    result = []
    for key, items in groups.items():
        direction, freq, bw, status = key
        result.append({
            "direction": direction,
            "frequency_mhz": freq,
            "bandwidth_mhz": bw,
            "status": status,
            "n": len(items),
            "throughput_mean_mbps": _mean([x["measured_throughput_mbps"] for x in items]),
            "rtt_mean_ms": _mean([x["ping_rtt_avg_ms"] for x in items]),
            "retransmits_mean": _mean([x["retransmits"] for x in items]),
            "dl_snr_mean_db": _mean([x["dl_snr_db"] for x in items]),
            "ul_snr_mean_db": _mean([x["ul_snr_db"] for x in items]),
            "dl_rssi_mean_dbm": _mean([x["dl_rssi_dbm"] for x in items]),
            "ul_rssi_mean_dbm": _mean([x["ul_rssi_dbm"] for x in items]),
        })
    return {
        "campaign_id": campaign_id,
        "rows": len(rows),
        "groups": result,
    }


def quality_summary(conn: sqlite3.Connection, hours: int) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = conn.execute(
        """
        SELECT hour_utc, rf_validity_pct, rf_temporal_coverage_pct,
               rf_coverage_pct, configuration_mixed,
               dl_active_measured_throughput_mbps_count,
               ul_active_measured_throughput_mbps_count
        FROM scientific_hourly_6g_general
        WHERE hour_utc >= ? ORDER BY hour_utc
        """,
        (cutoff.isoformat(),),
    ).fetchall()
    data = [dict(r) for r in rows]
    return {
        "window_hours_requested": hours,
        "hours_available": len(data),
        "rf_validity_pct_mean": _mean([r["rf_validity_pct"] for r in data]),
        "rf_temporal_coverage_pct_mean": _mean([r["rf_temporal_coverage_pct"] for r in data]),
        "rf_coverage_pct_mean": _mean([r["rf_coverage_pct"] for r in data]),
        "mixed_configuration_hours": sum(int(r["configuration_mixed"] or 0) for r in data),
        "dl_active_test_count": sum(float(r["dl_active_measured_throughput_mbps_count"] or 0) for r in data),
        "ul_active_test_count": sum(float(r["ul_active_measured_throughput_mbps_count"] or 0) for r in data),
    }



def answer_question(conn: sqlite3.Connection, question: str) -> dict:
    q = question.strip().lower()
    import re
    match = re.search(r"(\d+)\s*(?:h|hora|horas)", q)
    hours = int(match.group(1)) if match else 24

    if any(word in q for word in ("calidad", "cobertura", "validez", "qc")):
        return {"intent": "quality", "question": question, "result": quality_summary(conn, hours)}

    if any(word in q for word in ("campaña", "campaign", "3x2", "3×2")):
        row = conn.execute(
            "SELECT campaign_id FROM active_throughput_6g "
            "WHERE campaign_id IS NOT NULL AND campaign_id <> '' "
            "ORDER BY timestamp_start_utc DESC LIMIT 1"
        ).fetchone()
        campaign_id = row[0] if row else None
        if not campaign_id:
            return {"intent": "campaign", "question": question, "error": "No campaign found"}
        return {"intent": "campaign", "question": question, "result": campaign_summary(conn, campaign_id)}

    analytical_terms = (
        "snr", "rssi", "goodput", "throughput", "rtt", "retrans",
        "temperatura", "humedad", "presión", "presion", "viento",
        "meteorolog", "correl", "relación", "relacion", "compara", "analiza"
    )
    if any(term in q for term in analytical_terms):
        result = analyze_window(conn, hours)
        result["interpretation"] = (
            "Exploratory association only; correlations do not establish causality."
        )
        return {"intent": "window", "question": question, "result": result}

    return {"intent": "status", "question": question, "result": latest_status(conn)}


def _fmt(value, digits=2, suffix=""):
    if value is None:
        return "no disponible"
    return f"{float(value):.{digits}f}{suffix}"


def _human_metric(name: str) -> str:
    labels = {
        "dl_snr_mean_db": "SNR DL",
        "ul_snr_mean_db": "SNR UL",
        "dl_rssi_mean_dbm": "RSSI DL",
        "ul_rssi_mean_dbm": "RSSI UL",
        "dl_active_measured_throughput_mbps_mean": "goodput DL",
        "ul_active_measured_throughput_mbps_mean": "goodput UL",
        "dl_active_ping_rtt_avg_ms_mean": "RTT DL",
        "cu01_temp_mean_c": "temperatura CU01",
        "cu01_rh_mean_pct": "humedad CU01",
        "cu01_press_median_hpa": "presión CU01",
        "cu01_wind_mean_ms": "viento CU01",
        "sj01_temp_mean_c": "temperatura SJ01",
        "sj01_rh_mean_pct": "humedad SJ01",
        "sj01_press_median_hpa": "presión SJ01",
        "sj01_wind_mean_ms": "viento SJ01",
    }
    return labels.get(name, name)


def render_scientific_narrative(payload: dict) -> str:
    intent = payload.get("intent")
    result = payload.get("result") or {}

    if intent == "window":
        means = result.get("means", {})
        hours = result.get("window_hours_requested")
        rows = result.get("hourly_rows", 0)
        lines = [
            f"Análisis exploratorio de las últimas {hours} horas ({rows} horas científicas disponibles).",
            (
                "El radioenlace presentó un SNR medio de "
                f"{_fmt(means.get('dl_snr_mean_db'))} dB en DL y "
                f"{_fmt(means.get('ul_snr_mean_db'))} dB en UL. "
                f"El RSSI medio fue {_fmt(means.get('dl_rssi_mean_dbm'))} dBm en DL y "
                f"{_fmt(means.get('ul_rssi_mean_dbm'))} dBm en UL."
            ),
            (
                "Las pruebas activas registraron un goodput medio de "
                f"{_fmt(means.get('dl_active_measured_throughput_mbps_mean'))} Mbps en DL y "
                f"{_fmt(means.get('ul_active_measured_throughput_mbps_mean'))} Mbps en UL, "
                f"con RTT DL medio de {_fmt(means.get('dl_active_ping_rtt_avg_ms_mean'))} ms."
            ),
        ]
        strongest = result.get("strongest_correlations") or {}
        if strongest:
            pair, value = next(iter(strongest.items()))
            left, right = pair.split("__vs__", 1)
            direction = "positiva" if value > 0 else "negativa"
            lines.append(
                "La asociación exploratoria de mayor magnitud fue entre "
                f"{_human_metric(left)} y {_human_metric(right)} "
                f"(r = {value:.2f}, {direction})."
            )
        lines.append(
            "Interpretación metodológica: estas asociaciones son exploratorias; no demuestran causalidad. "
            "Para inferencia científica deben considerarse autocorrelación temporal, cobertura, configuración del radioenlace y posibles variables de confusión."
        )
        return "\n\n".join(lines)

    if intent == "quality":
        return (
            f"Calidad de datos para las últimas {result.get('window_hours_requested')} horas: "
            f"{result.get('hours_available', 0)} horas disponibles, validez RF media de "
            f"{_fmt(result.get('rf_validity_pct_mean'))} %, cobertura temporal RF de "
            f"{_fmt(result.get('rf_temporal_coverage_pct_mean'))} % y cobertura RF de "
            f"{_fmt(result.get('rf_coverage_pct_mean'))} %. "
            f"Se detectaron {result.get('mixed_configuration_hours', 0)} horas con configuración mezclada. "
            f"Pruebas activas registradas: DL={int(result.get('dl_active_test_count') or 0)} y "
            f"UL={int(result.get('ul_active_test_count') or 0)}."
        )

    if intent == "campaign":
        groups = result.get("groups") or []
        ok = [g for g in groups if g.get("status") == "OK" and g.get("frequency_mhz") is not None]
        lines = [
            f"Resumen de campaña {result.get('campaign_id')}: {result.get('rows', 0)} registros de pruebas activas."
        ]
        for g in ok[:6]:
            lines.append(
                f"{g.get('direction')} @ {g.get('frequency_mhz'):.0f} MHz / {g.get('bandwidth_mhz'):.0f} MHz: "
                f"n={g.get('n')}, goodput medio={_fmt(g.get('throughput_mean_mbps'))} Mbps, "
                f"RTT={_fmt(g.get('rtt_mean_ms'))} ms, retransmisiones medias={_fmt(g.get('retransmits_mean'))}."
            )
        lines.append("Los resultados deben interpretarse separando escenario, dirección, periodo experimental y condiciones meteorológicas.")
        return "\n".join(lines)

    status = result
    stations = status.get("stations", {})
    rf = status.get("latest_rf") or {}
    tp = status.get("latest_active_throughput") or {}
    return (
        "Estado científico reciente de AtmosLink. "
        f"CU01: {stations.get('CU01', {}).get('weather_timestamp_local', 'sin dato')}; "
        f"SJ01: {stations.get('SJ01', {}).get('weather_timestamp_local', 'sin dato')}. "
        f"Última telemetría RF: SNR DL={_fmt(rf.get('snr_dl'))} dB, SNR UL={_fmt(rf.get('snr_ul'))} dB, "
        f"MCS DL={_fmt(rf.get('mcs_dl'), 0)}, MCS UL={_fmt(rf.get('mcs_ul'), 0)}. "
        f"Última prueba activa: {tp.get('direction', 'N/D')} { _fmt(tp.get('measured_throughput_mbps')) } Mbps, "
        f"estado={tp.get('status', 'N/D')}."
    )


def generate_reproducible_report(conn: sqlite3.Connection, hours: int, output_dir: Path) -> dict:
    """Generate a read-only scientific report bundle (Markdown + PNG + JSON metadata)."""
    import subprocess
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    df = pd.read_sql_query(
        "SELECT * FROM scientific_hourly_6g_general WHERE hour_utc >= ? ORDER BY hour_utc",
        conn, params=(cutoff.isoformat(),),
    )
    if df.empty:
        raise RuntimeError("No scientific hourly data available for requested window")

    df["hour_utc"] = pd.to_datetime(df["hour_utc"], utc=True, errors="coerce")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prefix = f"atmoslink_scientific_report_{hours}h_{stamp}"
    report_path = output_dir / f"{prefix}.md"
    metadata_path = output_dir / f"{prefix}.json"

    figures = []
    fig1 = output_dir / f"{prefix}_snr.png"
    ax = df.plot(x="hour_utc", y=["dl_snr_mean_db", "ul_snr_mean_db"], figsize=(10, 5))
    ax.set_title(f"AtmosLink — SNR horario ({hours} h)")
    ax.set_xlabel("Hora UTC")
    ax.set_ylabel("SNR (dB)")
    ax.grid(True, alpha=0.25)
    ax.figure.tight_layout(); ax.figure.savefig(fig1, dpi=160); plt.close(ax.figure)
    figures.append(fig1)

    fig2 = output_dir / f"{prefix}_goodput.png"
    ax = df.plot(x="hour_utc", y=["dl_active_measured_throughput_mbps_mean", "ul_active_measured_throughput_mbps_mean"], figsize=(10, 5))
    ax.set_title(f"AtmosLink — Goodput activo horario ({hours} h)")
    ax.set_xlabel("Hora UTC")
    ax.set_ylabel("Goodput (Mbps)")
    ax.grid(True, alpha=0.25)
    ax.figure.tight_layout(); ax.figure.savefig(fig2, dpi=160); plt.close(ax.figure)
    figures.append(fig2)

    fig3 = output_dir / f"{prefix}_snr_vs_humidity_cu01.png"
    pair = df[["cu01_rh_mean_pct", "dl_snr_mean_db"]].dropna()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(pair["cu01_rh_mean_pct"], pair["dl_snr_mean_db"], alpha=0.75)
    ax.set_title("SNR DL vs humedad relativa CU01")
    ax.set_xlabel("Humedad relativa CU01 (%)")
    ax.set_ylabel("SNR DL (dB)")
    ax.grid(True, alpha=0.25)
    fig.tight_layout(); fig.savefig(fig3, dpi=160); plt.close(fig)
    figures.append(fig3)

    analysis = analyze_window(conn, hours)
    quality = quality_summary(conn, hours)
    payload = {"intent": "window", "question": f"Reporte científico reproducible de {hours} horas", "result": analysis}
    narrative = render_scientific_narrative(payload)
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        git_commit = None
    metadata = {
        "agent_version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_mode": "read-only", "window_hours": hours, "hourly_rows": int(len(df)),
        "first_hour_utc": str(df["hour_utc"].min()), "last_hour_utc": str(df["hour_utc"].max()),
        "git_commit": git_commit, "quality": quality,
        "figures": [x.name for x in figures],
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, default=str) + "\n")
    report = [
        f"# AtmosLink Scientific Agent v{VERSION} — reporte reproducible", "",
        f"Ventana solicitada: **{hours} horas**",
        f"Generado UTC: **{metadata['generated_at_utc']}**",
        f"Git commit: **{git_commit or 'N/D'}**",
        "Base científica: **SQLite en modo solo lectura**", "",
        "## Interpretación científica", "", narrative, "",
        "## Calidad y cobertura", "",
        f"- Horas disponibles: {quality['hours_available']}",
        f"- Validez RF media: {_fmt(quality['rf_validity_pct_mean'])} %",
        f"- Cobertura temporal RF media: {_fmt(quality['rf_temporal_coverage_pct_mean'])} %",
        f"- Horas con configuración mezclada: {quality['mixed_configuration_hours']}", "",
        "## Figuras", "",
        f"![SNR]({fig1.name})", "", f"![Goodput]({fig2.name})", "",
        f"![SNR vs humedad CU01]({fig3.name})", "",
        "## Nota metodológica", "",
        "Las asociaciones son exploratorias y no implican causalidad. Los datos científicos originales no fueron modificados.",
    ]
    report_path.write_text("\n".join(report) + "\n")
    return {
        "report": str(report_path), "metadata": str(metadata_path),
        "figures": [str(x) for x in figures], "hourly_rows": int(len(df)),
        "read_only": True,
    }

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AtmosLink Scientific Agent v0.4 (read-only)"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Latest CU01/SJ01, RF and throughput state")

    window = sub.add_parser("window", help="Exploratory hourly RF-weather analysis")
    window.add_argument("--hours", type=int, default=24)

    quality = sub.add_parser("quality", help="Hourly scientific data coverage summary")
    quality.add_argument("--hours", type=int, default=24)

    campaign = sub.add_parser("campaign", help="Active-throughput campaign summary")
    campaign.add_argument("--campaign-id", required=True)

    ask = sub.add_parser("ask", help="Controlled natural-language scientific question")
    ask.add_argument("question", nargs="+", help="Question in Spanish or English")
    ask.add_argument("--format", choices=("json", "narrative"), default="narrative")

    report = sub.add_parser("report", help="Generate reproducible Markdown + PNG scientific report")
    report.add_argument("--hours", type=int, default=24)
    report.add_argument("--output-dir", type=Path, default=Path("Data/exports/scientific_agent_reports"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.db.exists():
        raise SystemExit(f"Database not found: {args.db}")

    with connect_readonly(args.db) as conn:
        if args.command == "status":
            result = latest_status(conn)
        elif args.command == "window":
            result = analyze_window(conn, args.hours)
        elif args.command == "quality":
            result = quality_summary(conn, args.hours)
        elif args.command == "campaign":
            result = campaign_summary(conn, args.campaign_id)
        elif args.command == "ask":
            result = answer_question(conn, " ".join(args.question))
        elif args.command == "report":
            result = generate_reproducible_report(conn, args.hours, args.output_dir)
        else:
            raise SystemExit("Unsupported command")

    if args.command == "ask" and args.format == "narrative":
        print(render_scientific_narrative(result))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
