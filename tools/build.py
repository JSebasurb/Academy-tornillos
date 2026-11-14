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
    W(S/'heads.json', [{'id': slug(k), 'name': k, 'path': v[0], 'desc': v[1], 'figura': v[2]} for k, v in c['heads'].items()])
    W(S/'tips.json', [{'id': x[0], 'desc': x[1], 'path': x[2]} for x in c['tips']])
    W(S/'steps.json', [{'id': slug(x[0]), 'order': i+1, 'name': x[0], 'desc': x[1]} for i, x in enumerate(c['steps'])])
    W(S/'timeline.json', [{'year': x[0], 'text': x[1]} for x in c['timeline']])
    W(S/'selector.json', [{'id': slug(x[0]), 'name': x[0], 'text': x[1]} for x in c['selector']])
    CATS = {'mat': 'Materiales y fabricación', 'cab': 'Cabezas y estampas', 'ros': 'Roscas y calibres', 'aut': 'Autorroscantes', 'apl': 'Aplicaciones y empaque', 'cal': 'Medición, torque y calidad', 'rem': 'Remaches y espárragos', 'ope': 'Operación: registros y muestreo', 'est': 'Estampas y accionamientos', 'emp': 'Historia de CATO', 'r2a': 'Resistencia y materiales', 'r2b': 'Torque y precarga', 'r2c': 'Recubrimientos y corrosión', 'r2d': 'Autoperforantes y rosca', 'r2e': 'Diseño de la unión y aflojamiento', 'r3a': 'Roscas y especificación', 'r3b': 'Cabezas y accionamientos', 'r3c': 'Arandelas, tuercas y acabados', 'r3d': 'Resistencia, ajuste y medición', 'r4a': 'Materiales y temperatura', 'r4b': 'Recubrimientos y lubricantes', 'r4c': 'Corrosión e hidrógeno', 'r4d': 'Retención, roscas y fatiga', 'r4e': 'Torque, cargas y remaches', 'r4f': 'Falsificaciones y calidad'}
    qs = []
    for i, l in enumerate(x for x in (B/'quiz_banco.txt').read_text('utf8').splitlines() if x.strip() and not x.startswith('#')):
        cat, lvl, q, ok, *rest = [p.strip() for p in l.split('|')]; wr, exp = rest[:3], rest[3]
        pos = i % 4  # posición de la correcta repartida de forma pareja
        opts = wr[:pos] + [ok] + wr[pos:]
        qs.append({'id': f'q{i+1}', 'ruta': 1, 'cat': cat, 'level': int(lvl), 'q': q, 'options': opts, 'answer': pos, 'explanation': exp})
    for i, l in enumerate(x for x in (B/'quiz_ruta2.txt').read_text('utf8').splitlines() if x.strip() and not x.startswith('#')):
        cat, lvl, q, ok, *rest = [p.strip() for p in l.split('|')]; wr, exp = rest[:3], rest[3]
        pos = i % 4; opts = wr[:pos] + [ok] + wr[pos:]
        qs.append({'id': f'r2q{i+1}', 'ruta': 2, 'cat': cat, 'level': int(lvl), 'q': q, 'options': opts, 'answer': pos, 'explanation': exp})
    for rr in (3, 4):
        for i, l in enumerate(x for x in (B/f'quiz_ruta{rr}.txt').read_text('utf8').splitlines() if x.strip() and not x.startswith('#')):
            cat, lvl, q, ok, *rest = [p.strip() for p in l.split('|')]; wr, exp = rest[:3], rest[3]
            pos = i % 4; opts = wr[:pos] + [ok] + wr[pos:]
            qs.append({'id': f'r{rr}q{i+1}', 'ruta': rr, 'cat': cat, 'level': int(lvl), 'q': q, 'options': opts, 'answer': pos, 'explanation': exp})
    W(S/'quiz.json', qs); W(S/'quizcats.json', CATS)
    lec, fu = [], []
    for rr in (2, 3, 4):
        for i, x in enumerate(c[f'ruta{rr}_lecciones']): lec.append({'ruta': rr, 'id': f'l{i+1}', 'level': x[0], 'title': x[1], 'bullets': x[2], 'formula': x[3], 'checkpoint': x[4]})
        for x in c[f'ruta{rr}_fuentes']: fu.append({'ruta': rr, 'name': x[0], 'covers': x[1]})
    W(S/'lecciones.json', lec); W(S/'fuentes.json', fu)
    W(S/'rutas.json', {'2': {'title': 'Ruta 2 · Ingeniería de la unión roscada', 'intro': 'Investigación externa (ISO/ASTM/SAE y guías técnicas) complementaria al catálogo CATO.', 'levels': ['', 'Fundamentos', 'Especialista', 'Maestro']}, **c['rutas_meta']})
    W(S/'sena.json', [{'id': slug(x[0] + ' ' + x[1]), 'kind': x[0], 'name': x[1], 'desc': x[2], 'source': x[3]} for x in c['sena_items']])
    W(S/'planta.json', [{'id': slug(x[0]), 'name': x[0], 'source': x[1], 'desc': x[2]} for x in c['planta']])
    W(S/'terminos.json', [{'id': slug(x[0]), 'name': x[0], 'source': x[1], 'desc': x[2]} for x in c['terminos']])
    W(S/'heads_extra.json', [{'id': slug(x[0]), 'name': x[0], 'path': x[1], 'desc': x[2], 'uso': x[3], 'norma': x[4], 'estampa': x[5]} for x in c['heads_extra']])
    W(S/'estampas.json', [{'id': slug(x[0]), 'name': x[0], 'd': x[1], 'desc': x[2], 'uso': x[3], 'source': x[4]} for x in c['estampas']])
    W(S/'instrumentos.json', [{'id': slug(x[0]), 'name': x[0], 'source': x[1], 'desc': x[2]} for x in c['instrumentos']])
    W(S/'diagnostico.json', [{'id': f'd{i+1}', 'case': x[0], 'options': x[1], 'answer': x[2], 'explanation': x[3]} for i, x in enumerate(c['diagnostico'])])
    W(S/'figuras.json', [{'id': x[0], 'section': x[1], 'title': x[2], 'caption': x[3], 'image': x[4]} for x in c['figuras']])
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
    for r in T['mst']['rows']:
        if int(r[1]) != int(r[2]) * int(r[3]): err.append(f"mst {r[0]}: registros ≠ idas × registros por ida")
    for r in T['par']['rows']:  # el torque crece con el calibre
        v = [float(x) for x in r[1:] if num(x)]
        if v != sorted(v): warn.append(f"par {r[0]}: el catálogo muestra un torque no creciente (calibre 7 = 40 > calibre 8 = 39); transcrito tal cual, verificar con CATO")
    for r in T['pls']['rows']:
        if float(r[2]) < float(r[3]): err.append(f"pls {r[0]}: perforación fenólica menor que la de celulosa")
    for r in T['cal']['rows']:
        if abs(float(r[1]) - 25.4*(0.06+0.013*int(r[0]))) > 0.03: err.append(f"calibre {r[0]} se aparta de la fórmula ANSI")
    for tid in ('unc', 'unf'):
        for r in T[tid]['rows']:
            if not (float(r[1]) > float(r[3]) > float(r[5])): err.append(f"{tid} {r[0]}: jerarquía mayor>medio>menor")
    Q = json.loads((S/'quiz.json').read_text('utf8')); CT = json.loads((S/'quizcats.json').read_text('utf8'))
    for q in Q:
        if not 0 <= q['answer'] < len(q['options']): err.append(f"{q['id']}: respuesta fuera de rango")
        if len(q['options']) != 4 or len(set(q['options'])) != 4: err.append(f"{q['id']}: debe tener 4 opciones distintas")
        if q['cat'] not in CT or q['level'] not in (1, 2, 3): err.append(f"{q['id']}: categoría o nivel inválido")
    if len({q['q'] for q in Q}) != len(Q): err.append('preguntas duplicadas')
    longer = sum(len(q['options'][q['answer']]) > max(len(o) for i, o in enumerate(q['options']) if i != q['answer']) for q in Q)
    if longer / len(Q) > .50: warn.append(f'sesgo de longitud: la correcta es la más larga en {longer}/{len(Q)} preguntas')
    LEC = json.loads((S/'lecciones.json').read_text('utf8'))
    for rr, mn in ((2, 15), (3, 12), (4, 12)):
        for lv in (1, 2, 3):
            if sum(q['ruta'] == rr and q['level'] == lv for q in Q) < mn: err.append(f'Ruta {rr} nivel {lv}: menos de {mn} preguntas')
            if sum(l['ruta'] == rr and l['level'] == lv for l in LEC) < 3: err.append(f'Ruta {rr} nivel {lv}: menos de 3 lecciones')
    for r in T['metpaso']['rows']:
        if abs(float(r[2]) - (float(r[0][1:]) - float(r[1]))) > 0.16: err.append(f"metpaso {r[0]}: broca lejos de d − paso")
    for tid in ('uncb', 'unfb'):
        for r in T[tid]['rows']:
            if not (0 < float(r[3]) < float(r[2])) or abs(float(r[3]) - (float(r[2]) - 25.4 / float(r[1]))) > 0.16: err.append(f"{tid} {r[0]}: broca incoherente")
    for r in T['clsmet']['rows']:
        if not (float(r[2]) <= float(r[3]) <= float(r[4])): err.append(f"clsmet {r[0]}: prueba ≤ elástica ≤ tracción")
    for r in T['sae']['rows']:
        if not (float(r[2]) <= float(r[3]) <= float(r[4])): err.append(f"sae {r[0]}: prueba ≤ elástica ≤ tracción")
    for x in json.loads((S/'sena.json').read_text('utf8')):
        if not x['source'].startswith('SENA'): err.append(f"sena/{x['id']}: fuente inválida")
    tor = T['tor']['rows']
    if [float(r[1]) for r in tor] != sorted(float(r[1]) for r in tor): err.append('tor: torque no creciente con el diámetro')
    for c in CT:
        if sum(q['cat'] == c for q in Q) < 5: warn.append(f'categoría {c} con menos de 5 preguntas')
    for x in json.loads((S/'figuras.json').read_text('utf8')) + json.loads((S/'heads.json').read_text('utf8')):
        im = x.get('image') or x.get('figura')
        if not (S/'images'/f'{im}.png').exists(): err.append(f"falta imagen {im}")
    for x in json.loads((S/'tips.json').read_text('utf8')):
        if not (S/'images'/f"punta_{x['id']}.png").exists(): err.append(f"falta imagen de la punta {x['id']}")
    for d in json.loads((S/'diagnostico.json').read_text('utf8')):
        if not 0 <= d['answer'] < len(d['options']): err.append(f"{d['id']}: respuesta fuera de rango")
    for f in ('planta', 'instrumentos', 'estampas'):
        for x in json.loads((S/f'{f}.json').read_text('utf8')):
            if not x['source'].startswith(('Catálogo', 'General')): err.append(f"{f}/{x['id']}: fuente inválida")
    ids = [x['id'] for f in ('heads', 'steps', 'selector', 'quiz', 'planta', 'instrumentos', 'diagnostico', 'heads_extra', 'estampas', 'sena') for x in json.loads((S/f'{f}.json').read_text('utf8'))]
    if len(ids) != len(set(ids)): err.append('ids duplicados')
    W(S/'validation_report.json', {'ok': not err, 'errors': err, 'warnings': warn, 'tables': len(T)})
    return err

# ---------- SILVER -> GOLD: consumo ----------
def gold():
    L = lambda f: json.loads((S/f'{f}.json').read_text('utf8'))
    tabs = {t['id']: {'t': t['title'], 'n': t['note'], 'c': [c['name'] for c in t['columns']], 'r': t['rows']} for t in L('tables')}
    rutas = {str(r): dict(m, lecciones=[x for x in L('lecciones') if x['ruta'] == int(r)], fuentes=[x for x in L('fuentes') if x['ruta'] == int(r)]) for r, m in json.loads((S/'rutas.json').read_text('utf8')).items()}
    cato = {'version': 1, 'heads': L('heads'), 'tips': L('tips'), 'steps': L('steps'), 'timeline': L('timeline'),
            'selector': L('selector'), 'quiz': L('quiz'), 'quizcats': json.loads((S/'quizcats.json').read_text('utf8')), 'rutas': rutas, 'sena': L('sena'), 'planta': L('planta'), 'instrumentos': L('instrumentos'), 'terminos': L('terminos'), 'heads_extra': L('heads_extra'), 'estampas': L('estampas'), 'diagnostico': L('diagnostico'), 'tables': tabs, 'calibres': L('calibres')}
    idx = [{'type': 'tabla', 'id': k, 'title': v['t'], 'text': v['n']} for k, v in tabs.items()]
    for k, f in (('cabeza', 'heads'), ('proceso', 'steps'), ('selector', 'selector'), ('planta', 'planta'), ('instrumento', 'instrumentos')):
        idx += [{'type': k, 'id': x['id'], 'title': x['name'], 'text': x.get('desc') or x.get('text')} for x in L(f)]
    idx += [{'type': 'punta', 'id': x['id'], 'title': 'Tipo ' + x['id'], 'text': x['desc']} for x in L('tips')]
    import base64
    img = lambda n: ('data:image/png;base64,' + base64.b64encode((S/'images'/f'{n}.png').read_bytes()).decode()) if (S/'images'/f'{n}.png').exists() else None
    for x in cato['tips']: x['img'] = img('punta_' + x['id'])
    cato['figuras'] = [dict(f, img=img(f['image'])) for f in L('figuras')]
    for x in cato['heads']: x['img'] = img(x['figura'])
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
    for f in ('manifest.webmanifest', 'icon.svg', '404.html', 'icon-192.png', 'icon-512.png', 'icon-180.png', 'icon-maskable-512.png', 'favicon-32.png'): shutil.copy(SRC/'pwa'/f, OUT/f)
    files = ['./', 'index.html', 'data/gold.js', 'data/search_index.json', 'manifest.webmanifest', 'icon.svg', 'icon-192.png', 'icon-512.png', 'icon-180.png', 'favicon-32.png']
    (OUT/'sw.js').write_text((SRC/'pwa'/'sw.js').read_text('utf8').replace('@@VERSION@@', ver).replace('@@FILES@@', json.dumps(files)), 'utf8')
    (OUT/'.nojekyll').write_text('')
    (R/'dist').mkdir(exist_ok=True)  # versión de un solo archivo (sin servidor)
    (R/'dist'/'Academia_Tornillo_standalone.html').write_text(html.replace('<script src="data/gold.js"></script>', '<script>' + gjs + '</script>'), 'utf8')
    print('build', ver, '·', len(html)//1024, 'KB')

if __name__ == '__main__':
    silver(); e = validate()
    if e: print('VALIDACIÓN FALLIDA:\n - ' + '\n - '.join(e)); sys.exit(1)
    site(gold()); print('OK · silver validado · gold generado · docs/ listo')
