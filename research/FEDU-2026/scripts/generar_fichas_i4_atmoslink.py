#!/usr/bin/env python3
"""FEDU I4: hojas de revisión verificables, NO etiquetado automático.

Solo lee snapshot SQLite 3×2 y la tabla privada de candidatos.
Crea fichas JSON + CSV privados con ventanas de salud, calidad, periodos
y evidencias pendientes. NO declara ningún episodio RF positivo.
"""
import argparse,csv,json,sqlite3
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter
def parse(s):return datetime.fromisoformat(s)
def js(x):
 if isinstance(x,datetime):return x.isoformat()
 return x
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--snapshot',type=Path,required=True)
 ap.add_argument('--candidates',type=Path,required=True)
 ap.add_argument('--output',type=Path,required=True)
 a=ap.parse_args()
 a.output.mkdir(parents=True,exist_ok=True,mode=0o700)
 a.output.chmod(0o700)
 raw=list(csv.DictReader(a.candidates.open()))
 cands=[r for r in raw if r['triage']=='CANDIDATO_BIDIRECCIONAL_NO_VERIFICADO']
 assert len(cands)==8,len(cands)
 c=sqlite3.connect(a.snapshot.resolve().as_uri()+"?mode=ro",uri=True,timeout=3)
 c.execute('PRAGMA query_only=ON')
 report=[]
 for r in cands:
  t0,t1=parse(r['first_local']),parse(r['last_local'])
  before=t0-timedelta(hours=2);after=t1+timedelta(hours=2)
  rec=c.execute("""SELECT timestamp_start_local,direction,status,ping_status,
     route_verified,ping_loss_pct,operating_frequency_mhz,channel_bandwidth_mhz
     FROM active_throughput_6g WHERE timestamp_start_local >= ? AND
     timestamp_start_local <= ? ORDER BY timestamp_start_local""",
     (before.isoformat(),after.isoformat())).fetchall()
  during=[x for x in rec if t0<=parse(x[0])<=t1]
  prev=[x for x in rec if parse(x[0])<t0 and x[2]=='OK']
  following=[x for x in rec if parse(x[0])>t1 and x[2]=='OK']
  rf=c.execute("""SELECT timestamp_local,collection_status,
     operating_frequency_mhz,channel_bandwidth_mhz,
     dl_rssi_dbm,ul_rssi_dbm,dl_snr_db,ul_snr_db
     FROM radio_link_config_telemetry WHERE timestamp_local >= ? AND
     timestamp_local <= ? ORDER BY timestamp_local""",
     ((t0-timedelta(minutes=15)).isoformat(),(t1+timedelta(minutes=15)).isoformat())).fetchall()
  errors=[x for x in rf if x[1]=='COLLECTION_ERROR']
  operational=[x for x in rf if str(x[1]).startswith('LINK_OPERATIONAL') and
    x[4] is not None and x[5] is not None and x[4]<0 and x[5]<0]
  invalid=[x for x in rf if x[4]==0 or x[5]==0]
  per={}
  for direction in ('DL','UL'):
   earlier=[x[0] for x in prev if x[1]==direction]
   later=[x[0] for x in following if x[1]==direction]
   per[direction]={
       'last_previous_test_OK_local':max(earlier) if earlier else None,
       'first_following_test_OK_local':min(later) if later else None,
       'failed_tests_in_interval':sum(x[1]==direction and x[2]=='ERROR' for x in during),
       'OK_tests_in_interval':sum(x[1]==direction and x[2]=='OK' for x in during),
       'ping_not_ok_in_interval':sum(x[1]==direction and x[3] not in ('OK','SUCCESS') for x in during),
       'route_not_verified_in_interval':sum(x[1]==direction and x[4]!=1 for x in during)}
  status=Counter(x[1] for x in rf)
  freq=Counter('%s/%s'%(x[2],x[3]) for x in operational)
  note='No hay prueba de causa RF; la comparación de RF y pruebas de red utiliza fuentes operativas potencialmente dependientes.'
  if r['candidate_id'] in ('C001','C002','C003'):
   note+=' Fuera del periodo factorial 3x2; bitácora de cambios factorial no aplica.'
  if r['candidate_id'] in ('C020','C022','C024'):
   note+=' Incidencia del 21-Oct: revisar recuperación de configuración, energía y canal de monitorización.'
  if not operational:
   note+=' Sin muestras RF operativas utilizables cercanas: no inferir desvanecimiento.'
  evid={
    'candidate_id':r['candidate_id'],
    'case_state':'INDETERMINADO_PENDIENTE_VERDAD_TERRENO',
    'verified_rf_event':False,
    'test_error_window_start_local':t0.isoformat(),
    'test_error_window_end_local':t1.isoformat(),
    'first_last_mean_only_observed_tests':True,
    'n_failed_tests':int(r['failed_tests']),
    'near_transition_flag':bool(int(r['near_planned_or_logged_transition'])),
    'per_direction':per,
    'rf_observations_with_margin_min':15,
    'rf_total':len(rf),
    'rf_collection_errors':len(errors),
    'rf_operational_valid_rssi':len(operational),
    'rf_zero_suspect':len(invalid),
    'rf_configuration_if_valid':dict(freq),
    'rf_sample_status':dict(status),
    'quality_notes':note,
    'external_sources_scope':'EXCLUIDAS: fuentes ajenas a AtmosLink no utilizadas ni necesarias para la clasificación',
    'network_independent_logs':'NO_CORROBORADO: ping en prueba iperf no es observador independiente',
    'admissible_source_tables':['active_throughput_6g','radio_link_config_telemetry'],
    'link_maintenance_logs':'NO_CORROBORADO: solo se admitirán bitácoras propias de equipos y servicios AtmosLink',
    'human_review_required':True,
    'reviewer_decision':'PENDIENTE',
    'classification_options':['RF_CONFIRMADO','RED_TRANSPORTE','COLECTOR','TRANSICION','INDETERMINADO'],
    'uncertainty':'Inicio y fin del fallo físico no identificables a partir de errores iperf; última prueba sana y primera posterior definen límites de disponibilidad de pruebas, no del RF.'
  }
  report.append(evid)
 c.close()
 for e in report:
  f=a.output/(e['candidate_id']+'_I4.json')
  f.write_text(json.dumps(e,ensure_ascii=False,indent=2,default=js)+'\n')
  f.chmod(0o600)
 summ={
   'source':'snapshot SQLite íntegro y cribado FEDU candidatos; ninguna fuente ML',
   'n_cases':len(report),'case_ids':[x['candidate_id'] for x in report],
   'verified_rf_events':sum(e['verified_rf_event'] for e in report),
   'cases_without_valid_rf':sum(not x['rf_operational_valid_rssi'] for x in report),
   'counts':[{k:e[k] for k in ('candidate_id','test_error_window_start_local','n_failed_tests','rf_total','rf_collection_errors','rf_operational_valid_rssi','rf_zero_suspect','case_state')} for e in report],
   'limitations':'Los registros RF y ping del mismo sistema son evidencias operativas, pero no prueba causal RF independiente; fuentes ajenas a AtmosLink excluidas'
 }
 f=a.output/'I4_review_manifest.json'
 f.write_text(json.dumps(summ,ensure_ascii=False,indent=2)+'\n');f.chmod(0o600)
 print(json.dumps(summ,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
