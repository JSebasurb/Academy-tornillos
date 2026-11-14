#!/usr/bin/env python3
"""Migración única: convierte los colores fijos del CSS heredado (azul/negro) en variables de tema.
Uso: python tools/theme_migrate.py  (idempotente: no hace nada si ya está migrado)"""
import re, colorsys
from pathlib import Path
P = Path(__file__).resolve().parent.parent / 'src' / 'base.html'
s = P.read_text('utf8')
a = s.index('<style>'); b = s.index('</style>', a); css = s[a + 7:b]
if '/*THEME-MIGRATED*/' in css: raise SystemExit('ya migrado')

def parse(h):
    h = h.lstrip('#')
    if len(h) in (3, 4): h = ''.join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), (int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)

def classify(h):
    r, g, bl, al = parse(h); l = (.299 * r + .587 * g + .114 * bl) / 255
    hh, ll, ss = colorsys.rgb_to_hls(r / 255, g / 255, bl / 255); hue = hh * 360; sat = (max(r, g, bl) - min(r, g, bl)) / 255
    return r, g, bl, al, l, hue, sat

def wrap(expr, al): return expr if al >= .995 else f'color-mix(in srgb,{expr} {round(al * 100)}%,transparent)'
def mix(var, pct, base='var(--panel)'): return f'color-mix(in srgb,{var} {pct}%,{base})'

def conv(h, prop, accent_rule):
    r, g, bl, al, l, hue, sat = classify(h)
    if prop in ('box-shadow', 'text-shadow', 'filter'): return h, False
    border = prop.startswith('border') or prop == 'outline'
    # blanco / casi blanco
    if l >= .8 and sat < .2:
        if prop == 'color' and not accent_rule: return wrap('var(--ink)', al), False
        if prop == 'color': return h, False
        return wrap('var(--ink)', al) if prop.startswith('background') and al < 1 else h, False
    if sat < .45 and l < .36 or (sat < .6 and l < .30 and 180 <= hue <= 260):   # superficies azul-gris oscuras
        if border: return wrap('var(--line)', al), False
        if prop == 'color': return wrap('var(--muted)', al), False
        base = 'var(--bg)' if l < .07 else 'var(--panel)' if l < .115 else 'var(--panel2)'
        return wrap(base, al), False
    if l >= .5 and sat < .45:   # grises/azules claros de texto
        return wrap('var(--ink)' if l >= .8 else 'var(--muted)', al), False
    # saturados
    fam = 'red' if (hue < 25 or hue > 335) else 'amber' if hue < 70 else 'green' if hue < 170 else 'cyan' if hue < 270 else 'other'
    col = {'red': 'var(--red)', 'amber': 'var(--amber)', 'green': 'var(--green)', 'cyan': 'var(--cyan)', 'other': 'var(--cyan)'}[fam]
    if l < .36:   # tonos oscuros semánticos
        return wrap(mix(col, max(14, round(l * 100 * 1.6))), al), prop.startswith('background') or border and False
    if prop == 'color':
        if fam == 'red' and l > .55: return wrap('var(--acc)', al), False
        if l > .62: return wrap(mix(col, 72, 'var(--ink)'), al), False
        return wrap(col, al), False
    if border: return wrap(col, al), False
    return wrap(col if l <= .62 else mix(col, 78, 'var(--ink)'), al), True

DECL = re.compile(r'(?<=[{;])(\s*)([a-z-]+)(\s*:\s*)([^;{}]+)(?=[;}])')
def fix_body(body):
    accent = False; items = []
    for m in DECL.finditer(body):
        prop, val = m.group(2), m.group(4)
        if prop.startswith('background') and re.search(r'var\(--(red|cyan|green|amber)\)|#e53935|#26c6da|#39d98a|#ffca3a|#ff5a52', val) and 'color-mix' not in val: accent = True
    def rep_decl(m):
        prop, val = m.group(2), m.group(4)
        def rep(c):
            out, _ = conv(c.group(0), prop, accent); return out
        return m.group(1) + prop + m.group(3) + re.sub(r'#[0-9a-fA-F]{3,8}\b', rep, val)
    return DECL.sub(rep_decl, body + ';' if not body.rstrip().endswith((';','}')) else body)

def fix(css):
    return re.sub(r'(\{)([^{}]*)(\})', lambda m: m.group(1) + fix_body('{' + m.group(2))[1:] + m.group(3), css)

root = re.search(r':root\{[^}]*\}', css).group(0)
new_css = fix(css.replace(root, '/*THEME-MIGRATED*/'))
P.write_text(s[:a + 7] + new_css + s[b:], 'utf8')
print('migrado:', len(re.findall(r'color-mix', new_css)), 'mezclas;', len(re.findall(r'#[0-9a-fA-F]{3,8}\b', new_css)), 'literales restantes')
