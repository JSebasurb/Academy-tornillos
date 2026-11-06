#!/usr/bin/env python3
"""Cruza cada celda numérica de silver con los números del texto del catálogo (bronze). Marca los valores que no aparecen."""
import json, re, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent
txt = (R/'bronze'/'catalogo_cato_texto.txt').read_text('utf8')
toks = set(re.findall(r'\d+(?:[.,]\d+)?', txt.replace(',', '.')))
miss = {}
for t in json.loads((R/'silver'/'tables.json').read_text('utf8')):
    for r in t['rows']:
        for c in r:
            for n in re.findall(r'\d+(?:\.\d+)?', c):
                if n not in toks and n.lstrip('0') not in toks: miss.setdefault(t['id'], set()).add(n)
print('Valores sin respaldo textual en el catálogo:', {k: sorted(v) for k, v in miss.items()} or 'ninguno')
