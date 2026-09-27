#!/usr/bin/env python3
from pathlib import Path
import ast,hashlib,json,subprocess,sys

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
import scientific_discovery.v24_calibration as v24

PROTOCOL=ROOT/"docs/ASDE_REVIEWER_A_V24_PROSPECTIVE_CALIBRATION_PROTOCOL_DRAFT.md"
MODULE=ROOT/"scientific_discovery/v24_calibration.py"
TEST=ROOT/"scripts/test_asde_v24_calibration.py"
SCHEMA=ROOT/"scientific_discovery/schemas/v24_calibration_start.schema.json"
TEMPLATE=ROOT/"scientific_discovery/v24_start_manifest_TEMPLATE.json"
VALIDATOR=ROOT/"scripts/validate_asde_v24_start_manifest.py"
RUNNER=ROOT/"scripts/run_asde_v24_prospective.py"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_a_v24_code_concordance.json"

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()

errors=[];warnings=[]

# Every artifact used by the pre-freeze PASS must be present in the Git index.
for tracked in [PROTOCOL,MODULE,TEST,SCHEMA,TEMPLATE,VALIDATOR,RUNNER,Path(__file__)]:
 rel=str(tracked.resolve().relative_to(ROOT.resolve()))
 q=subprocess.run(["git","ls-files","--error-unmatch",rel],cwd=ROOT,
                  text=True,capture_output=True)
 if q.returncode!=0:
  errors.append(f"required artifact not tracked by Git: {rel}")

text=PROTOCOL.read_text()

if v24.OPERATING_ALPHA != 0.04:
 errors.append(f"OPERATING_ALPHA changed: {v24.OPERATING_ALPHA}")
if v24.CALIBRATION_CEILING != 0.05:
 errors.append(f"CALIBRATION_CEILING changed: {v24.CALIBRATION_CEILING}")

# Protocol constants that must match implementation.
required_tokens=[
 str(v24.RF_DROP_THRESHOLD),
 "2026092601","2026092602","2026092603",
 "2026092604","2026092605","2026092606",
 "A1 = 2500","A2 = 2500","B-test = 5000",
 "1,000,000 permutation proposals",
 "224/5000 = 0.0448",
 "60 consecutive local calendar days",
 "joint daily-profile permutation",
 "7000 MHz center frequency / 20 MHz channel bandwidth",
 "p_FWER,j <= **0.04**",
 "external conditional-calibration ceiling remains 0.05",
 "support-eligible A1 sham scores",
 "If m_j = 0",
 "the 60 calendar days are immutable",
]
for token in required_tokens:
 if token not in text:
  errors.append(f"protocol missing required token: {token}")

for name,spec in v24.DRIVER_SPECS.items():
 for key in ("diff15_median","diff15_scale","z_threshold"):
  token=str(spec[key])
  if token not in text:
   errors.append(f"protocol missing {name} {key}={token}")

for x in list(v24.RF_MEDIAN)+list(v24.RF_SCALE):
 if str(float(x)) not in text:
  errors.append(f"protocol missing RF constant {float(x)}")

# Module must remain pure: reject file/network/database access calls.
tree=ast.parse(MODULE.read_text())
for node in ast.walk(tree):
 if isinstance(node,ast.Call):
  name=""
  if isinstance(node.func,ast.Name):
   name=node.func.id
  elif isinstance(node.func,ast.Attribute):
   name=node.func.attr
  if name in {"open","read_csv","read_json","read_sql","read_text","write_text",
              "connect","urlopen","request","requests","sqlite3"}:
   errors.append(f"module contains prohibited I/O-like call: {name} line {getattr(node,'lineno','?')}")

# Test may read only the exact historical prevalidation CSV.
test_text=TEST.read_text()
test_tree=ast.parse(test_text)
csv_literals={
 node.value for node in ast.walk(test_tree)
 if isinstance(node,ast.Constant) and isinstance(node.value,str)
 and node.value.lower().endswith(".csv")
}
allowed_csv={"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"}
if csv_literals != allowed_csv:
 errors.append(f"unexpected CSV literals in test: {sorted(csv_literals)}")
for forbidden in ["scientific_campaign_6g_integrated.csv","D_validation"]:
 if forbidden in test_text:
  errors.append(f"test contains forbidden source token: {forbidden}")

# Execute unit/integration tests.
r=subprocess.run([sys.executable,str(TEST)],cwd=ROOT,text=True,capture_output=True)
if r.returncode!=0:
 errors.append("v24 tests failed")
 warnings.append(r.stdout+r.stderr)

# Template must validate without authorizing execution.
rv=subprocess.run([sys.executable,str(VALIDATOR),str(TEMPLATE)],cwd=ROOT,text=True,capture_output=True)
if rv.returncode!=0:
 errors.append("v24 template validation failed")
else:
 try:
  obj=json.loads(rv.stdout)
  if obj.get("prospective_execution_authorized") is not False:
   errors.append("draft template unexpectedly authorizes execution")
 except Exception:
  errors.append("validator output not JSON")

# Prospective runner must refuse the inactive template before any source read.
rr=subprocess.run([sys.executable,str(RUNNER),str(TEMPLATE)],cwd=ROOT,text=True,capture_output=True)
if rr.returncode!=2:
 errors.append(f"runner did not refuse inactive template; exit={rr.returncode}")
else:
 try:
  obj=json.loads(rr.stdout)
  if obj.get("status")!="REFUSED":
   errors.append("runner refusal output malformed")
 except Exception:
  errors.append("runner refusal output not JSON")

result={
 "status":"PASS" if not errors else "FAIL",
 "protocol_sha256":sha(PROTOCOL),
 "module_sha256":sha(MODULE),
 "test_sha256":sha(TEST),
 "schema_sha256":sha(SCHEMA),
 "template_sha256":sha(TEMPLATE),
 "validator_sha256":sha(VALIDATOR),
 "runner_sha256":sha(RUNNER),
 "template_validator_stdout":rv.stdout.strip(),
 "runner_refusal_stdout":rr.stdout.strip(),
 "cell_family_size":len(v24.CELL_ORDER),
 "rf_drop_threshold":v24.RF_DROP_THRESHOLD,
 "driver_specs":v24.DRIVER_SPECS,
 "test_stdout":r.stdout.strip(),
 "errors":errors,
 "warnings":warnings,
 "calibration_start_utc":None,
 "prospective_execution_authorized":False,
}
OUT.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not errors else 1)
