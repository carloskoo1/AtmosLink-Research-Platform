#!/usr/bin/env python3
"""FEDU: criba de incidentes, SIN establecer etiquetas científicas positivas.

Cruza SOLO fuentes de lectura: snapshots, cronograma, bitácora y telemetría RF.
Señala episodios CANDIDATOS y razones para revisión. Nunca declara "fallo RF".
"""
import argparse,bisect,csv,json,sqlite3
from collections import Counter
from datetime import datetime,timedelta
from pathlib import Path

def parse(x):
    return datetime.fromisoformat(x) if x else None
def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--db",type=Path,required=True)
    a.add_argument("--schedule",type=Path,required=True)
    a.add_argument("--events",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--gap-min",type=int,default=35)
    a.add_argument("--transition-guard-min",type=int,default=90)
    o=a.parse_args()
    if o.gap_min<=0 or o.transition_guard_min<0: a.error("invalid gap/guard")
    out=o.output.resolve();out.mkdir(parents=True,exist_ok=True,mode=0o700)
    out.chmod(0o700)
    c=sqlite3.connect(o.db.resolve().as_uri()+"?mode=ro",uri=True,timeout=3)
    c.execute("PRAGMA query_only=ON")
    tests=c.execute("""SELECT timestamp_start_local,direction,status,
        ping_status,ping_loss_pct,route_verified,operating_frequency_mhz,
        channel_bandwidth_mhz,error,measured_throughput_mbps
        FROM active_throughput_6g WHERE status='ERROR' ORDER BY timestamp_start_local""").fetchall()
    rf=c.execute("""SELECT timestamp_local,collection_status,dl_rssi_dbm,
        ul_rssi_dbm,dl_snr_db,ul_snr_db
        FROM radio_link_config_telemetry ORDER BY timestamp_local""").fetchall()
    c.close()
    with o.schedule.open(newline='',encoding='utf-8') as h:plan=list(csv.DictReader(h))
    transitions=[]
    for r in plan[1:]:
        if parse(r.get("start_local")):transitions.append(parse(r["start_local"]))
    with o.events.open(encoding='utf-8') as h:
        for line in h:
            try:ev=json.loads(line)
            except:continue
            if ev.get("event") in ("SWITCH_START","SWITCH_FAILED","SWITCH_COMMITTED",
                  "ROLLBACK_START","ROLLBACK_FAILED","ROLLBACK_COMMITTED"):
                if parse(ev.get("timestamp_utc")):transitions.append(parse(ev["timestamp_utc"]))
    transitions.sort()
    rf_times=[parse(r[0]) for r in rf]
    clusters=[]
    for test in tests:
        tm=parse(test[0])
        if tm is None:continue
        if not clusters or (tm-clusters[-1]["last"]).total_seconds()>o.gap_min*60:
            clusters.append({"first":tm,"last":tm,"tests":[]})
        cl=clusters[-1];cl["last"]=tm;cl["tests"].append(test)
    details=[]
    for i,cl in enumerate(clusters,1):
        start,end=cl["first"],cl["last"]
        guard=timedelta(minutes=o.transition_guard_min)
        t0=bisect.bisect_left(transitions,start-guard)
        near=bool(t0<len(transitions) and transitions[t0]<=end+guard)
        r0=bisect.bisect_left(rf_times,start-timedelta(minutes=10))
        r1=bisect.bisect_right(rf_times,end+timedelta(minutes=10))
        samples=rf[r0:r1]
        good=[x for x in samples if x[1] and str(x[1]).startswith("LINK_OPERATIONAL")
          and x[2] is not None and x[3] is not None and x[2]<0 and x[3]<0]
        bad=[x for x in samples if x[1] and str(x[1]).startswith("COLLECTION_ERROR")]
        suspect_zero=[x for x in samples if (x[2]==0 or x[3]==0)]
        directions={x[1] for x in cl["tests"]}
        ping_fail=sum(x[3] not in ("OK","SUCCESS") for x in cl["tests"])
        route_bad=sum(x[5]!=1 for x in cl["tests"])
        error_cat=Counter()
        for x in cl["tests"]:
            txt=str(x[8] or "").lower()
            if "unable to connect" in txt:error_cat["tcp_cannot_connect"]+=1
            elif "control socket" in txt:error_cat["iperf_control_socket"]+=1
            else:error_cat["other_iperf_error"]+=1
        # Review groups do NOT correspond to ground truth event labels
        if near:classif="REVISAR_TRANSICION_PROGRAMADA"
        elif len(cl["tests"])>=3 and directions=={"DL","UL"}:
            classif="CANDIDATO_BIDIRECCIONAL_NO_VERIFICADO"
        else:classif="FALLO_DE_PRUEBA_NO_VERIFICADO"
        details.append({
            "candidate_id":"C%03d"%i,
            "first_local":start.isoformat(),"last_local":end.isoformat(),
            "duration_min":round((end-start).total_seconds()/60,2),
            "failed_tests":len(cl["tests"]),
            "directions":"+".join(sorted(directions)),
            "near_planned_or_logged_transition":int(near),
            "ping_non_ok_tests":ping_fail,"route_not_verified":route_bad,
            "nearest_rf_operational_samples":len(good),
            "nearby_rf_collection_errors":len(bad),
            "rf_zero_suspect":len(suspect_zero),
            "dominant_iperf_error":error_cat.most_common(1)[0][0],
            "triage":classif,
            "event_verified":0,
        })
    fields=list(details[0]) if details else []
    with (out/"candidate_review_private.csv").open("w",newline="",encoding="utf-8") as h:
        if fields:
            w=csv.DictWriter(h,fieldnames=fields)
            w.writeheader();w.writerows(details)
    ctr=Counter(z["triage"] for z in details)
    total=Counter()
    for x in details:
        for flag in ("near_planned_or_logged_transition","nearby_rf_collection_errors","rf_zero_suspect"):
            if x[flag]:total["groups_with_"+flag]+=1
        if x["directions"]=="DL+UL": total["bidirectional_groups"]+=1
        if x["ping_non_ok_tests"]: total["groups_with_non_ok_ping"]+=1
        if x["nearest_rf_operational_samples"]:total["groups_with_operational_rf"]+=1
    # split campaign period vs other periods for scientific provenance
    campaign_start=parse(plan[1]["start_local"])
    campaign_end=parse(plan[-1]["end_local"])
    cmp=Counter()
    for x in details:
        t=parse(x["first_local"])
        cmp["experiment" if campaign_start<=t<campaign_end else "outside_experiment"]+=1
    summary={
        "type":"CANDIDATE_EVENT_SCREENING_NOT_GROUND_TRUTH",
        "candidate_count":len(details),"failed_tests":len(tests),
        "independent_rf_degradations_confirmed":0,
        "rule_gap_minutes":o.gap_min,"guard_minutes":o.transition_guard_min,
        "categories":dict(ctr),"flags":dict(total),"periods":dict(cmp),
        "sources":"snapshot_SQLite, campaign_schedule, campaign_events",
        "next_steps":["Confirm ping/routing independently of iperf status",
            "Check electricity, equipment restarts, logs and regime changes",
            "Apply pre-registered RF/service event criterion blind to ML outputs",
            "Document start/end uncertainty and reviewer decision"],
        "privacy":"Private CSV with timestamps and flags; only summary suitable for public GitHub"
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    for p in out.iterdir():p.chmod(0o600)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("TOP_GROUPS",json.dumps(sorted([{
        "id":x["candidate_id"],"first":x["first_local"],
        "errors":x["failed_tests"],"near_transition":x["near_planned_or_logged_transition"],
        "rf_errors":x["nearby_rf_collection_errors"],"ping_non_ok":x["ping_non_ok_tests"],
        "triage":x["triage"]} for x in details],
        key=lambda y:y["errors"],reverse=True)[:12],ensure_ascii=False))
if __name__=="__main__":main()
