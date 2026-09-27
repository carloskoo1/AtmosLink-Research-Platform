#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess,sys
from datetime import datetime,timedelta

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
DEFAULT=ROOT/"scientific_discovery/v24_start_manifest_TEMPLATE.json"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def git(args):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def _inside(root,path):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False

def validate(path,require_active=False):
    path=Path(path)
    m=json.loads(path.read_text())
    errors=[]

    if m.get("experiment_id")!="DISCOVERY-001-V24": errors.append("experiment_id")
    if m.get("timezone")!="America/Lima": errors.append("timezone")
    if m.get("status") not in {"DRAFT_TEMPLATE","FROZEN_ACTIVE","CLOSED"}: errors.append("status")

    rc=m.get("radio_configuration",{})
    for k,v in {"frequency_mhz":7000,"bandwidth_mhz":20,"ap_tx_power_dbm":10,"sm_tx_power_dbm":3}.items():
        if rc.get(k)!=v: errors.append(f"radio_configuration.{k}")

    st=m.get("statistics",{})
    expected={"family_size":12,"operating_cutoff":0.04,"calibration_ceiling":0.05,
              "a1_schedules":2500,"a2_schedules":2500,"b_test_schedules":5000,"proposal_cap":1000000}
    for k,v in expected.items():
        if st.get(k)!=v: errors.append(f"statistics.{k}")

    el=m.get("eligibility",{})
    if el.get("calendar_days")!=60: errors.append("eligibility.calendar_days")
    if el.get("min_good_bins_per_day")!=274: errors.append("eligibility.min_good_bins_per_day")
    if el.get("exact_5min_grid") is not True: errors.append("eligibility.exact_5min_grid")
    if el.get("immutable_window") is not True: errors.append("eligibility.immutable_window")

    pr=m.get("prohibitions",{})
    if pr.get("d_validation") is not True: errors.append("prohibitions.d_validation")
    if pr.get("historical_integrated_csv") is not True: errors.append("prohibitions.historical_integrated_csv")
    if m.get("prospective_source",{}).get("prospective_only") is not True:
        errors.append("prospective_source.prospective_only")

    active=require_active or m.get("status")=="FROZEN_ACTIVE"
    if active:
        if m.get("status")!="FROZEN_ACTIVE": errors.append("manifest_not_active")
        if m.get("inferential_execution_enabled") is not True:
            errors.append("inferential_execution_not_enabled")
        for key in ["calibration_start_utc","calibration_end_utc","freeze_commit"]:
            if not m.get(key): errors.append(f"missing_{key}")

        for refname in ["schema","protocol","module","unit_test","concordance_audit","validator","runner"]:
            ref=m.get(refname,{})
            rel=ref.get("path","")
            p=ROOT/rel
            if not rel or not _inside(ROOT,p): errors.append(f"{refname}_path_invalid")
            elif not p.exists(): errors.append(f"{refname}_path_missing")
            elif sha256(p)!=ref.get("sha256"): errors.append(f"{refname}_sha256")

        freeze=m.get("freeze_commit")
        if freeze:
            try:
                subprocess.check_call(["git","cat-file","-e",f"{freeze}^{{commit}}"],cwd=ROOT,
                                      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                subprocess.check_call(["git","merge-base","--is-ancestor",freeze,"HEAD"],cwd=ROOT,
                                      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                errors.append("freeze_commit_not_ancestor")

        if git(["status","--porcelain"]):
            errors.append("git_tree_not_clean")

        try:
            start=datetime.fromisoformat(m["calibration_start_utc"].replace("Z","+00:00"))
            end=datetime.fromisoformat(m["calibration_end_utc"].replace("Z","+00:00"))
            if end-start!=timedelta(days=60): errors.append("calibration_window_not_60_days")
            rel_manifest=str(path.resolve().relative_to(ROOT.resolve()))
            commit_time=git(["log","-1","--format=%cI","--",rel_manifest])
            if not commit_time:
                errors.append("active_manifest_not_committed")
            else:
                mt=datetime.fromisoformat(commit_time)
                if start<=mt:
                    errors.append("calibration_start_not_after_manifest_commit")
        except Exception:
            errors.append("calibration_time_validation")

        source_rel=m.get("prospective_source",{}).get("path")
        if not source_rel:
            errors.append("prospective_source_missing")
        else:
            sp=Path(source_rel)
            if sp.is_absolute() or ".." in sp.parts:
                errors.append("prospective_source_path_invalid")
            source=ROOT/sp
            allowed_root=ROOT/"Data/exports"
            if not _inside(allowed_root,source):
                errors.append("prospective_source_outside_exports")
            low=source_rel.lower()
            forbidden=["scientific_campaign_6g_integrated.csv","prevalidation_7000_20.csv","d_validation"]
            if any(x in low for x in forbidden):
                errors.append("prospective_source_forbidden")

    return errors,m

if __name__=="__main__":
    args=[x for x in sys.argv[1:] if x!="--require-active"]
    path=Path(args[0]) if args else DEFAULT
    require_active="--require-active" in sys.argv[1:]
    errors,m=validate(path,require_active=require_active)
    result={"manifest":str(path),"status":"PASS" if not errors else "FAIL",
            "manifest_status":m.get("status"),
            "prospective_execution_authorized":not errors and m.get("status")=="FROZEN_ACTIVE" and m.get("inferential_execution_enabled") is True,
            "errors":errors}
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if not errors else 1)
