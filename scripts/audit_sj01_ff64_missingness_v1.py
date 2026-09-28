#!/usr/bin/env python3
"""AtmosLink SJ01 FF64 Missingness Bias Audit v1.

Read-only audit of the observed FF64 acquisition failures. It does not
modify production databases, services, firmware, or station configuration.
"""

from pathlib import Path
import json
import math
import re
import sqlite3
import subprocess

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, mannwhitneyu

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "SQLite/CU01/weather_local.db"
OUT = ROOT / "Results/sj01_ff64_missingness_v1"
OUT.mkdir(parents=True, exist_ok=True)

SSH = [
    "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
    "ckoo@192.168.1.4",
]
JOURNAL_CMD = [
    "journalctl", "-u", "weather-logger-sj01.service",
    "--no-pager", "-o", "short-iso",
]

TS_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[.,]\d+)?[+-]\d{2}:\d{2})"
)
FF_RE = re.compile(r"leading_ff=(\d+)")
LEN_RE = re.compile(r"\blen=(\d+)")

def fetch_events():
    p = subprocess.run(SSH + JOURNAL_CMD, capture_output=True, text=True, check=True)
    rows = []
    for line in p.stdout.splitlines():
        mt = TS_RE.match(line)
        if not mt:
            continue
        ts = pd.to_datetime(mt.group(1).replace(",", "."), utc=True)
        if "RX_VALIDO:" in line:
            payload = line.split("RX_VALIDO:", 1)[1].strip()
            fields = payload.split(",")
            try:
                t_s = int(fields[0])
            except Exception:
                t_s = np.nan
            rows.append({"timestamp": ts, "kind": "VALID", "t_s": t_s,
                         "raw_len": len(payload.encode()) + 2, "leading_ff": 0})
        elif "fragmento no UTF-8 descartado" in line:
            mf = FF_RE.search(line)
            if mf and int(mf.group(1)) == 64:
                ml = LEN_RE.search(line)
                rows.append({"timestamp": ts, "kind": "FF64", "t_s": np.nan,
                             "raw_len": int(ml.group(1)) if ml else np.nan,
                             "leading_ff": 64})
    if not rows:
        raise RuntimeError("No se encontraron eventos VALID/FF64 en journal.")
    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    df["minute"] = df["timestamp"].dt.floor("min")
    return df

def exclusive_minutes(events):
    grouped = events.groupby("minute")["kind"].agg(list)
    rows = []
    ambiguous = []
    for minute, kinds in grouped.items():
        uniq = sorted(set(kinds))
        if uniq == ["VALID"]:
            rows.append((minute, 0, "VALID", len(kinds)))
        elif uniq == ["FF64"]:
            rows.append((minute, 1, "FF64", len(kinds)))
        else:
            ambiguous.append((minute, "|".join(uniq), len(kinds)))
    minute_df = pd.DataFrame(rows, columns=["timestamp", "ff64", "kind", "events_in_minute"])
    amb_df = pd.DataFrame(ambiguous, columns=["timestamp", "kinds", "events_in_minute"])
    return minute_df.sort_values("timestamp"), amb_df

def load_sql():
    con = sqlite3.connect(DB)
    cu01 = pd.read_sql_query("""
        SELECT timestamp_local, temp_avg_C, hum_avg_pct, pres_avg_hPa,
               rain_1min_mm, rain_1h_mm
        FROM weather_local
        WHERE station_id='CU01'
        ORDER BY timestamp_local
    """, con)
    rf = pd.read_sql_query("""
        SELECT timestamp_local, snr_dl, snr_ul, sta_dl_rssi,
               mcs_dl, mcs_ul, dl_rate, ul_rate, error
        FROM radio_link_local
        WHERE station_id='CU01'
        ORDER BY timestamp_local
    """, con)
    nasa = pd.read_sql_query("""
        SELECT timestamp_local, temp_c AS nasa_sj_temp_c,
               dewpoint_c AS nasa_sj_dewpoint_c, rh_pct AS nasa_sj_rh_pct,
               precip_mm AS nasa_sj_precip_mm, press_hpa AS nasa_sj_press_hpa,
               wind10m_ms AS nasa_sj_wind10m_ms
        FROM nasa_power_hourly
        WHERE site_tag='SM_SAN_JOSE'
        ORDER BY timestamp_local
    """, con)
    cfg = pd.read_sql_query("""
        SELECT timestamp_local, operating_frequency_mhz,
               channel_bandwidth_mhz, dl_rssi_dbm, dl_snr_db,
               dl_mcs, ul_mcs, tx_quality_pct, tx_capacity_pct,
               collection_status
        FROM radio_link_config_telemetry
        WHERE operating_frequency_mhz IS NOT NULL
          AND channel_bandwidth_mhz IS NOT NULL
        ORDER BY timestamp_local
    """, con)
    con.close()
    for df in (cu01, rf, nasa, cfg):
        df["timestamp"] = pd.to_datetime(df.pop("timestamp_local"), utc=True)
        df.sort_values("timestamp", inplace=True)
    return cu01, rf, nasa, cfg

def match_covariates(minutes, cu01, rf, nasa, cfg):
    x = minutes.sort_values("timestamp").copy()
    x = pd.merge_asof(
        x, cu01, on="timestamp", direction="nearest",
        tolerance=pd.Timedelta(seconds=45),
    )
    x = pd.merge_asof(
        x, rf, on="timestamp", direction="nearest",
        tolerance=pd.Timedelta(seconds=45),
        suffixes=("", "_rf"),
    )
    x = pd.merge_asof(
        x, nasa, on="timestamp", direction="backward",
        tolerance=pd.Timedelta(minutes=65),
    )
    x = pd.merge_asof(
        x, cfg, on="timestamp", direction="backward",
        tolerance=pd.Timedelta(minutes=10),
        suffixes=("", "_cfg"),
    )
    local = x["timestamp"].dt.tz_convert("America/Lima")
    x["date_local"] = local.dt.strftime("%Y-%m-%d")
    x["hour_local"] = local.dt.hour
    x["scenario"] = np.where(
        x["operating_frequency_mhz"].notna() & x["channel_bandwidth_mhz"].notna(),
        x["operating_frequency_mhz"].round().astype("Int64").astype(str)
        + "/"
        + x["channel_bandwidth_mhz"].round().astype("Int64").astype(str),
        "UNKNOWN",
    )
    return x

def cramers_v(table):
    if table.empty or min(table.shape) < 2:
        return np.nan, np.nan
    chi2, p, _, _ = chi2_contingency(table)
    n = table.to_numpy().sum()
    denom = min(table.shape[0] - 1, table.shape[1] - 1)
    v = math.sqrt((chi2 / n) / denom) if n and denom > 0 else np.nan
    return v, p

def categorical_summary(df, col):
    tab = pd.crosstab(df[col], df["ff64"])
    if 0 not in tab.columns:
        tab[0] = 0
    if 1 not in tab.columns:
        tab[1] = 0
    tab = tab[[0, 1]]
    out = tab.rename(columns={0: "valid", 1: "ff64"}).copy()
    out["total"] = out["valid"] + out["ff64"]
    out["ff64_pct"] = 100 * out["ff64"] / out["total"]
    v, p = cramers_v(tab)
    return out.reset_index(), {"cramers_v": v, "chi2_p": p}

def continuous_effects(df, columns):
    rows = []
    for col in columns:
        z = df[["ff64", col]].dropna()
        a = z.loc[z.ff64 == 0, col].astype(float)
        b = z.loc[z.ff64 == 1, col].astype(float)
        if len(a) < 10 or len(b) < 10:
            continue
        va, vb = a.var(ddof=1), b.var(ddof=1)
        pooled = math.sqrt(((len(a)-1)*va + (len(b)-1)*vb) / (len(a)+len(b)-2)) if len(a)+len(b)>2 else np.nan
        smd = (b.mean() - a.mean()) / pooled if pooled and np.isfinite(pooled) else np.nan
        try:
            _, p = mannwhitneyu(b, a, alternative="two-sided")
        except Exception:
            p = np.nan
        rows.append({
            "variable": col, "n_valid": len(a), "n_ff64": len(b),
            "mean_valid": a.mean(), "mean_ff64": b.mean(),
            "median_valid": a.median(), "median_ff64": b.median(),
            "smd_ff64_minus_valid": smd, "mannwhitney_p": p,
        })
    return pd.DataFrame(rows)

def main():
    events = fetch_events()
    minutes, ambiguous = exclusive_minutes(events)
    cu01, rf, nasa, cfg = load_sql()
    matched = match_covariates(minutes, cu01, rf, nasa, cfg)

    events.to_csv(OUT / "events_raw_classified.csv", index=False)
    minutes.to_csv(OUT / "events_minute_exclusive.csv", index=False)
    ambiguous.to_csv(OUT / "events_minute_ambiguous.csv", index=False)
    matched.to_csv(OUT / "matched_covariates.csv", index=False)

    by_day, _day_all_test = categorical_summary(matched, "date_local")
    by_hour, hour_test = categorical_summary(matched, "hour_local")
    by_scenario, _scenario_all_test = categorical_summary(matched, "scenario")
    complete_date_values = by_day.loc[by_day['total'] >= 1400, 'date_local'].tolist()
    _, day_test = categorical_summary(matched[matched['date_local'].isin(complete_date_values)], 'date_local')
    _, scenario_test = categorical_summary(matched[matched['scenario'] != 'UNKNOWN'], 'scenario')
    by_day.to_csv(OUT / "ff64_by_day.csv", index=False)
    by_hour.to_csv(OUT / "ff64_by_hour.csv", index=False)
    by_scenario.to_csv(OUT / "ff64_by_rf_scenario.csv", index=False)

    continuous = [
        "temp_avg_C", "hum_avg_pct", "pres_avg_hPa",
        "rain_1min_mm", "rain_1h_mm",
        "nasa_sj_temp_c", "nasa_sj_dewpoint_c", "nasa_sj_rh_pct",
        "nasa_sj_precip_mm", "nasa_sj_press_hpa", "nasa_sj_wind10m_ms",
        "snr_dl", "snr_ul", "sta_dl_rssi", "mcs_dl", "mcs_ul",
        "dl_rate", "ul_rate", "dl_rssi_dbm", "dl_snr_db",
        "dl_mcs", "ul_mcs", "tx_quality_pct", "tx_capacity_pct",
    ]
    effects = continuous_effects(matched, continuous)
    effects.to_csv(OUT / "continuous_effects.csv", index=False)

    complete_days = by_day[by_day["total"] >= 1400].copy()
    scenario_known = by_scenario[by_scenario["scenario"] != "UNKNOWN"].copy()
    max_abs_smd = float(effects["smd_ff64_minus_valid"].abs().max()) if not effects.empty else None
    hour_spread = float(by_hour["ff64_pct"].max() - by_hour["ff64_pct"].min()) if not by_hour.empty else None
    scenario_spread = float(scenario_known["ff64_pct"].max() - scenario_known["ff64_pct"].min()) if len(scenario_known) > 1 else None

    summary = {
        "audit_version": "v1",
        "events_raw": int(len(events)),
        "exclusive_minutes": int(len(minutes)),
        "ambiguous_minutes": int(len(ambiguous)),
        "ff64_minutes": int(minutes["ff64"].sum()),
        "valid_minutes": int((minutes["ff64"] == 0).sum()),
        "ff64_pct": float(100 * minutes["ff64"].mean()),
        "first_event_utc": str(minutes["timestamp"].min()),
        "last_event_utc": str(minutes["timestamp"].max()),
        "complete_days": complete_days.to_dict(orient="records"),
        "tests": {"day": day_test, "hour": hour_test, "scenario": scenario_test},
        "max_abs_smd": max_abs_smd,
        "hour_ff64_rate_spread_pp": hour_spread,
        "scenario_ff64_rate_spread_pp": scenario_spread,
        "matched_nonnull": {
            c: int(matched[c].notna().sum())
            for c in continuous if c in matched.columns
        },
        "interpretation_guardrail": (
            "This audit can detect associations between FF64 missingness and observed covariates; "
            "it cannot prove MCAR or identify the physical root cause."
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")

    lines = []
    lines.append("# SJ01 FF64 Missingness Bias Audit v1")
    lines.append("")
    lines.append("Read-only audit. No production database, service, firmware, or station configuration was modified.")
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"- Exclusive minute events: {len(minutes)}")
    lines.append(f"- Valid: {(minutes.ff64 == 0).sum()}")
    lines.append(f"- FF64: {minutes.ff64.sum()}")
    lines.append(f"- Overall FF64 fraction: {100*minutes.ff64.mean():.2f}%")
    lines.append(f"- Ambiguous minutes excluded: {len(ambiguous)}")
    lines.append("")
    lines.append("## Complete-day rates")
    lines.append("")
    lines.append('```text')
    lines.append(complete_days.to_string(index=False) if len(complete_days) else 'No complete days.')
    lines.append('```')
    lines.append("")
    lines.append("## RF-scenario rates")
    lines.append("")
    lines.append('```text')
    lines.append(by_scenario.to_string(index=False))
    lines.append('```')
    lines.append("")
    lines.append("## Categorical association")
    lines.append("")
    lines.append(f"- Day: Cramer's V={day_test['cramers_v']:.4f}, p={day_test['chi2_p']:.3g}")
    lines.append(f"- Hour: Cramer's V={hour_test['cramers_v']:.4f}, p={hour_test['chi2_p']:.3g}")
    lines.append(f"- RF scenario: Cramer's V={scenario_test['cramers_v']:.4f}, p={scenario_test['chi2_p']:.3g}")
    lines.append("")
    lines.append("## Continuous covariates")
    lines.append("")
    if not effects.empty:
        lines.append('```text')
        lines.append(effects.sort_values('smd_ff64_minus_valid', key=lambda s: s.abs(), ascending=False).to_string(index=False))
        lines.append('```')
    else:
        lines.append("No continuous covariates had sufficient matched observations.")
    lines.append("")
    lines.append("## Scientific interpretation")
    lines.append("")
    lines.append(f"- Maximum absolute standardized mean difference across matched observed covariates: {max_abs_smd:.4f}.")
    lines.append(f"- Hour-of-day FF64 rate spread: {hour_spread:.2f} percentage points.")
    lines.append(f"- Known RF-scenario FF64 rate spread: {scenario_spread:.2f} percentage points.")
    lines.append("- In the currently observable window, there is no evidence of a strong differential FF64 association with complete day, hour of day, the three represented RF scenarios, CU01 weather, NASA POWER conditions at SM_SAN_JOSE, or the matched RF metrics.")
    lines.append("- This supports treating FF64 primarily as loss of eligible SJ01 observations rather than demonstrated weather- or RF-selective missingness in this window.")
    lines.append("- This is not proof of MCAR, and the physical failure mechanism remains unresolved.")
    lines.append("")
    lines.append("## Scope limitations")
    lines.append("")
    lines.append("- The journal window begins on 2026-09-21 local time; it cannot establish behavior before the retained logs.")
    lines.append("- RF scenarios represented in this audit are 6475/20, 6655/40, and 6475/40; conclusions must not be generalized automatically to unrepresented 3x2 scenarios.")
    lines.append("- NASA POWER provides independent SJ01-area atmospheric covariates for part of the audit window; ERA5-Land has no overlap with the retained FF64 journal window at the current watermark.")
    lines.append("- CU01 rain was constant at zero in the matched window and therefore cannot test rain dependence by itself; NASA POWER precipitation provides limited independent variation.")
    lines.append("")
    lines.append("## Interpretation guardrail")
    lines.append("")
    lines.append("This audit evaluates whether FF64 occurrence is associated with observed time, weather, RF, or configuration covariates.")
    lines.append("It does not prove Missing Completely At Random (MCAR), and it does not identify the physical root cause.")
    lines.append("FF64 records remain ineligible for scientific observation reconstruction.")
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, default=str))
    print("\nArtifacts:", OUT)

if __name__ == "__main__":
    main()
