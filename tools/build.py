#!/usr/bin/env python3
"""Pipeline medallón: bronze -> silver -> gold -> docs/ (GitHub Pages).
Uso: python tools/build.py   (falla con código 1 si la validación de silver no pasa)"""
import json, re, hashlib, csv, shutil, sys, unicodedata
from pathlib import Path
R = Path(__file__).resolve().parent.parent
B, S, G, SRC, OUT = R/'bronze', R/'silver', R/'gold', R/'src', R/'docs'
W = lambda p, o: (p.parent.mkdir(parents=True, exist_ok=True), p.write_text(json.dumps(o, ensure_ascii=False, indent=1), 'utf8'))
slug = lambda t: re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFD', t.lower()).encode('ascii', 'ignore').decode()).strip('-')
num = lambda x: re.fullmatch(r'-?\d+(\.\d+)?', str(x).strip()) is not None

# ---------- BRONZE -> SILVER: tipado, normalización, esquema ----------
def silver():
    raw = json.loads((B/'tables_raw.json').read_text('utf8')); c = json.loads((B/'content_raw.json').read_text('utf8'))
    tables = []
    for tid, t in raw.items():
        rows = t['raw_rows'] if 'raw_rows' in t else [list(r) for r in zip(*[x.split(' ') for x in t['raw_columns']])]
        cols = [{'name': n, 'numeric': all(num(r[i]) for r in rows)} for i, n in enumerate(t['columns'])]
        tables.append({'id': tid, 'title': t['title'], 'note': t['note'], 'columns': cols, 'rows': [[x.strip() for x in r] for r in rows]})
    W(S/'tables.json', tables)
    W(S/'heads.json', [{'id': slug(k), 'name': k, 'path': v[0], 'desc': v[1]} for k, v in c['heads'].items()])
    W(S/'tips.json', [{'id': x[0], 'desc': x[1], 'path': x[2]} for x in c['tips']])
    W(S/'steps.json', [{'id': slug(x[0]), 'order': i+1, 'name': x[0], 'desc': x[1]} for i, x in enumerate(c['steps'])])
    W(S/'timeline.json', [{'year': x[0], 'text': x[1]} for x in c['timeline']])
    W(S/'selector.json', [{'id': slug(x[0]), 'name': x[0], 'text': x[1]} for x in c['selector']])
    W(S/'quiz.json', [{'id': f'q{i+1}', 'q': x[0], 'options': x[1], 'answer': x[2], 'explanation': x[3]} for i, x in enumerate(c['quiz'])])
    W(S/'calibres.json', [{'n': int(r[0]), 'mm_catalogo': float(r[1]), 'pulgadas': round(0.06+0.013*int(r[0]), 4)} for r in next(t for t in tables if t['id'] == 'cal')['rows']])

# ---------- VALIDACIÓN (calidad de datos) ----------
def validate():
    err, warn = [], []
    T = {t['id']: t for t in json.loads((S/'tables.json').read_text('utf8'))}
    for t in T.values():
        n = len(t['columns'])
        for i, r in enumerate(t['rows']):
            if len(r) != n: err.append(f"{t['id']} fila {i+1}: {len(r)} celdas, esperadas {n}")
        names = [c['name'] for c in t['columns']]
        for j, nm in enumerate(names):  # pares máx/mín
            if nm.endswith('máx') and nm[:-3]+'mín' in names:
                k = names.index(nm[:-3]+'mín')
                for r in t['rows']:
                    if num(r[j]) and num(r[k]) and float(r[j]) < float(r[k]): err.append(f"{t['id']} {r[0]}: {nm} < mín")
    for r in T['cal']['rows']:
        if abs(float(r[1]) - 25.4*(0.06+0.013*int(r[0]))) > 0.03: err.append(f"calibre {r[0]} se aparta de la fórmula ANSI")
    for tid in ('unc', 'unf'):
        for r in T[tid]['rows']:
            if not (float(r[1]) > float(r[3]) > float(r[5])): err.append(f"{tid} {r[0]}: jerarquía mayor>medio>menor")
    for q in json.loads((S/'quiz.json').read_text('utf8')):
        if not 0 <= q['answer'] < len(q['options']): err.append(f"{q['id']}: respuesta fuera de rango")
    ids = [x['id'] for f in ('heads', 'steps', 'selector', 'quiz') for x in json.loads((S/f'{f}.json').read_text('utf8'))]
    if len(ids) != len(set(ids)): err.append('ids duplicados')
    W(S/'validation_report.json', {'ok': not err, 'errors': err, 'warnings': warn, 'tables': len(T)})
    return err

# ---------- SILVER -> GOLD: consumo ----------
def gold():
    L = lambda f: json.loads((S/f'{f}.json').read_text('utf8'))
    tabs = {t['id']: {'t': t['title'], 'n': t['note'], 'c': [c['name'] for c in t['columns']], 'r': t['rows']} for t in L('tables')}
    cato = {'version': 1, 'heads': L('heads'), 'tips': L('tips'), 'steps': L('steps'), 'timeline': L('timeline'),
            'selector': L('selector'), 'quiz': L('quiz'), 'tables': tabs, 'calibres': L('calibres')}
    idx = [{'type': 'tabla', 'id': k, 'title': v['t'], 'text': v['n']} for k, v in tabs.items()]
    for k, f in (('cabeza', 'heads'), ('proceso', 'steps'), ('selector', 'selector')):
        idx += [{'type': k, 'id': x['id'], 'title': x['name'], 'text': x.get('desc') or x.get('text')} for x in L(f)]
    idx += [{'type': 'punta', 'id': x['id'], 'title': 'Tipo ' + x['id'], 'text': x['desc']} for x in L('tips')]
    G.mkdir(exist_ok=True); W(G/'cato.json', cato); W(G/'search_index.json', idx)
    for k, v in tabs.items():
        p = G/'csv'/f'{k}.csv'; p.parent.mkdir(exist_ok=True)
        with p.open('w', newline='', encoding='utf-8-sig') as f: w = csv.writer(f, delimiter=';'); w.writerow(v['c']); w.writerows(v['r'])
    return cato

# ---------- ENSAMBLE: docs/ para GitHub Pages ----------
def site(cato):
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT/'data').mkdir(parents=True)
    gjs = 'window.CATO=' + json.dumps(cato, ensure_ascii=False, separators=(',', ':')) + ';'
    ver = hashlib.sha1((gjs + (SRC/'js'/'taller.js').read_text('utf8') + (SRC/'base.html').read_text('utf8')).encode()).hexdigest()[:10]
    html = (SRC/'base.html').read_text('utf8').replace('/*@@TALLER_JS@@*/', (SRC/'js'/'taller.js').read_text('utf8')).replace('@@BUILD@@', ver)
    (OUT/'index.html').write_text(html, 'utf8'); (OUT/'data'/'gold.js').write_text(gjs, 'utf8')
    shutil.copy(G/'cato.json', OUT/'data'/'cato.json'); shutil.copy(G/'search_index.json', OUT/'data'/'search_index.json'); shutil.copytree(G/'csv', OUT/'data'/'csv')
    for f in ('manifest.webmanifest', 'icon.svg', '404.html'): shutil.copy(SRC/'pwa'/f, OUT/f)
    files = ['./', 'index.html', 'data/gold.js', 'data/search_index.json', 'manifest.webmanifest', 'icon.svg']
    (OUT/'sw.js').write_text((SRC/'pwa'/'sw.js').read_text('utf8').replace('@@VERSION@@', ver).replace('@@FILES@@', json.dumps(files)), 'utf8')
    (OUT/'.nojekyll').write_text('')
    (R/'dist').mkdir(exist_ok=True)  # versión de un solo archivo (sin servidor)
    (R/'dist'/'Academia_CATO_standalone.html').write_text(html.replace('<script src="data/gold.js"></script>', '<script>' + gjs + '</script>'), 'utf8')
    print('build', ver, '·', len(html)//1024, 'KB')

if __name__ == '__main__':
    silver(); e = validate()
    if e: print('VALIDACIÓN FALLIDA:\n - ' + '\n - '.join(e)); sys.exit(1)
    site(gold()); print('OK · silver validado · gold generado · docs/ listo')
