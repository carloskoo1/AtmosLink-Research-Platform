#!/usr/bin/env python3
"""FEDU: observador temporal conservador, sin control RF ni pruebas activas.

Por defecto NO sondea permanentemente. init omite registros antiguos;
poll registra por primera vez filas nuevas en base PRIVADA independiente.
La hora first_seen es cota superior de disponibilidad, NO ingested_at real.
"""
import argparse, json, os, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

VERSION="0.1.0"
SOURCES={
    "active_throughput_6g": "timestamp_end_utc",
    "radio_link_config_telemetry": "timestamp_utc",
}
def utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
def connect_source(p):
    if not p.is_file(): raise ValueError("Source database not found")
    con=sqlite3.connect(p.resolve().as_uri()+"?mode=ro",uri=True,timeout=2)
    con.execute("PRAGMA query_only=ON")
    con.execute("PRAGMA busy_timeout=2000")
    return con
def cols(con,t):
    return {x[1] for x in con.execute('PRAGMA table_info("'+t+'")')}
def setup(state):
    state.execute("""CREATE TABLE IF NOT EXISTS cursor_state(
        source_table TEXT PRIMARY KEY, last_id INTEGER NOT NULL,
        initialized_at_utc TEXT NOT NULL)""")
    state.execute("""CREATE TABLE IF NOT EXISTS first_seen(
        source_table TEXT NOT NULL, source_id INTEGER NOT NULL,
        observed_at_utc TEXT, first_seen_at_utc TEXT NOT NULL,
        observer_version TEXT NOT NULL,
        PRIMARY KEY(source_table,source_id))""")
    state.execute("""CREATE TABLE IF NOT EXISTS polls(
        id INTEGER PRIMARY KEY, polled_at_utc TEXT NOT NULL,
        source_table TEXT NOT NULL, rows_discovered INTEGER NOT NULL,
        status TEXT NOT NULL)""")
def run(source_file,state_file,mode,batch_size):
    if source_file.resolve()==state_file.resolve():
        raise ValueError("Output and source databases must be distinct")
    if source_file.parent.resolve()==state_file.parent.resolve():
        raise ValueError("State DB must not be next to production source")
    if batch_size<1 or batch_size>1000:
        raise ValueError("batch-size outside safe range")
    os.umask(0o077)
    source=connect_source(source_file)
    try:
        for table,observed_col in SOURCES.items():
            fields=cols(source,table)
            if not {"id",observed_col}.issubset(fields):
                raise RuntimeError("Missing expected source columns: "+table)
        state_file.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        state=sqlite3.connect(state_file)
        try:
            state.execute("PRAGMA busy_timeout=2000")
            setup(state)
            results=[]
            for table, observed_col in SOURCES.items():
                cur=state.execute("SELECT last_id FROM cursor_state WHERE source_table=?",(table,))
                row=cur.fetchone()
                if row is None:
                    if mode!="init":
                        raise RuntimeError("First run must be 'init', never backfill implicitly")
                    max_id=source.execute('SELECT COALESCE(MAX(id),0) FROM "'+table+'"').fetchone()[0]
                    state.execute("INSERT INTO cursor_state VALUES(?,?,?)",(table,max_id,utc()))
                    results.append({"table":table,"initial_cursor":max_id,"captured_history":0})
                    continue
                if mode=="init":
                    results.append({"table":table,"already_initialized":True,"last_id":row[0]})
                    continue
                last=row[0]
                rows=source.execute(
                    'SELECT id,"'+observed_col+'" FROM "'+table+'" WHERE id>? ORDER BY id LIMIT ?',
                    (last,batch_size)).fetchall()
                # Timestamp each batch AFTER rows are readable: conservative.
                discovery=utc()
                for source_id, observed_at in rows:
                    state.execute("""INSERT OR IGNORE INTO first_seen
                        (source_table,source_id,observed_at_utc,first_seen_at_utc,observer_version)
                        VALUES(?,?,?,?,?)""",
                        (table,source_id,observed_at,discovery,VERSION))
                if rows:
                    state.execute("UPDATE cursor_state SET last_id=? WHERE source_table=?",(rows[-1][0],table))
                state.execute("INSERT INTO polls(polled_at_utc,source_table,rows_discovered,status) VALUES(?,?,?,?)",
                    (discovery,table,len(rows),"ok"))
                results.append({"table":table,"rows_discovered":len(rows),
                                "last_id":rows[-1][0] if rows else last,
                                "has_more":len(rows)==batch_size})
            state.commit()
            return {"mode":mode,"observer_version":VERSION,"status":"ok",
                    "operational_available_at_proven":False,"sources":results}
        finally:state.close()
    finally:source.close()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("init","poll"))
    p.add_argument("--source-db",type=Path,required=True)
    p.add_argument("--state-db",type=Path,required=True)
    p.add_argument("--batch-size",type=int,default=250)
    a=p.parse_args()
    try: print(json.dumps(run(a.source_db,a.state_db,a.mode,a.batch_size),ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status":"error","kind":type(e).__name__,"error":str(e)}),file=sys.stderr)
        sys.exit(2)
if __name__=="__main__":main()
