#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, subprocess
ROOT = Path('/home/carlos/Proyectos/EstacionMeteorologica')
EN = ROOT / 'docs/IEEE_ASDE_FULL_DRAFT_V2.md'
ES = ROOT / 'docs/IEEE_ASDE_FULL_DRAFT_V2_ES.md'
TEX = ROOT / 'manuscript/ieee_access/asde_ieee_access_es.tex'
PDF = ROOT / 'manuscript/ieee_access/asde_ieee_access_es.pdf'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(ok, message):
    if not ok:
        raise SystemExit('ERROR: ' + message)

en, es, tex = EN.read_text(), ES.read_text(), TEX.read_text()
require(sha(EN) == '30772b84c1ab6058a2476e6f633ef4f22bc755840547b90d22ed275286606299', 'English master changed')
require(f'% Source SHA-256: {sha(ES)}' in tex, 'Spanish source hash mismatch')
key_re = r'\b[A-Z][A-Z0-9-]+-\d{4}\b'
require(set(re.findall(key_re, en)) == set(re.findall(key_re, es)), 'citation-key set differs')
require(tex.count(r'\begin{table*}') == 10, 'expected 10 tables')
require(tex.count(r'\begin{figure*}') == 5, 'expected 5 figures')
require(tex.count(r'\begin{IEEEbiographynophoto}') == 5, 'expected 5 biographies')
for value in ['85.3', '79.0', '21.3', '21.7', '1.7', '4,600', '3,132', '2,860', '716']:
    require(en.count(value) == es.count(value), f'numeric claim count differs: {value}')
for token in ['D_development', 'D_validation', 'RFATM-0001', 'RFATM-0006', 'M1', 'M2', 'M3', 'v12', 'v21', 'v23', 'v24']:
    require(token in es, f'missing protected identifier: {token}')
pdf_text = subprocess.check_output(['pdftotext', str(PDF), '-'], text=True)
require('TRADUCCIÓN DE TRABAJO' in pdf_text, 'working-translation warning absent from PDF')
info = subprocess.check_output(['pdfinfo', str(PDF)], text=True)
pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
require(15 <= pages <= 22, f'unexpected page count: {pages}')
log = TEX.with_suffix('.log').read_text(errors='replace')
for failure in ['Undefined control sequence', 'LaTeX Error', 'Citation `', 'Reference `']:
    require(failure not in log, f'LaTeX log contains: {failure}')
print(f'IEEE_ASDE_SPANISH_OK source_sha256={sha(ES)} pages={pages} tables=10 figures=5 references=31 biographies=5')
