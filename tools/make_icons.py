#!/usr/bin/env python3
"""Genera el ícono de Academia Tornillo (SVG + PNG). Requiere Pillow. Uso: python tools/make_icons.py"""
from PIL import Image, ImageDraw
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / 'src' / 'pwa'
SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><defs><linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a2a2c"/><stop offset="1" stop-color="#000000"/></linearGradient><linearGradient id="h" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff4d3f"/><stop offset="1" stop-color="#d82518"/></linearGradient><linearGradient id="s" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#90a4ae"/><stop offset=".5" stop-color="#eceff1"/><stop offset="1" stop-color="#90a4ae"/></linearGradient></defs><rect width="512" height="512" rx="112" fill="url(#b)"/><rect x="136" y="96" width="240" height="100" rx="40" fill="url(#h)"/><rect x="232" y="96" width="48" height="44" fill="#6f0f08"/><rect x="150" y="104" width="212" height="14" rx="7" fill="#fff" opacity=".22"/><path d="M214 196h84v224l-42 48-42-48z" fill="url(#s)"/><g stroke="#d82518" stroke-width="12" stroke-linecap="round"><path d="M214 226l84 22M214 262l84 22M214 298l84 22M214 334l84 22M214 370l84 22"/></g></svg>'''
(OUT / 'icon.svg').write_text(SVG, 'utf8')
S = 4  # supersampling

def vgrad(w, h, c1, c2):
    g = Image.new('RGB', (w, h)); d = ImageDraw.Draw(g)
    for y in range(h):
        t = y / max(h - 1, 1); d.line([(0, y), (w, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    return g

def hgrad(w, h):
    g = Image.new('RGB', (w, h)); d = ImageDraw.Draw(g)
    for x in range(w):
        t = abs(x / max(w - 1, 1) - .5) * 2; c = int(236 - (236 - 144) * t)
        d.line([(x, 0), (x, h)], fill=(c, min(255, c + 12), min(255, c + 17)))
    return g

def render(size, maskable=False):
    W = 512 * S; img = vgrad(W, W, (42, 42, 44), (0, 0, 0)).convert('RGBA')
    k = S
    if not maskable:
        m = Image.new('L', (W, W), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, W - 1], 112 * k, fill=255)
        bg = Image.new('RGBA', (W, W), (0, 0, 0, 0)); bg.paste(img, (0, 0), m); img = bg
    def paste_grad(box, grad, radius=0, mask_poly=None):
        x0, y0, x1, y1 = [v * k for v in box]; w, h = x1 - x0, y1 - y0
        mk = Image.new('L', (w, h), 0); dd = ImageDraw.Draw(mk)
        if mask_poly: dd.polygon([((px - box[0]) * k, (py - box[1]) * k) for px, py in mask_poly], fill=255)
        else: dd.rounded_rectangle([0, 0, w - 1, h - 1], radius * k, fill=255)
        img.paste(grad(w, h), (x0, y0), mk)
    paste_grad((136, 96, 376, 196), lambda w, h: vgrad(w, h, (255, 77, 63), (216, 37, 24)), 40)
    d = ImageDraw.Draw(img)
    d.rectangle([232 * k, 96 * k, 280 * k, 140 * k], fill=(111, 15, 8, 255))
    hl = Image.new('RGBA', (W, W), (0, 0, 0, 0)); ImageDraw.Draw(hl).rounded_rectangle([150 * k, 104 * k, 362 * k, 118 * k], 7 * k, fill=(255, 255, 255, 56)); img = Image.alpha_composite(img, hl)
    paste_grad((214, 196, 298, 468), hgrad, mask_poly=[(214, 196), (298, 196), (298, 420), (256, 468), (214, 420)])
    d = ImageDraw.Draw(img)
    for y in (226, 262, 298, 334, 370):
        d.line([(214 * k, y * k), (298 * k, (y + 22) * k)], fill=(216, 37, 24, 255), width=12 * k)
        for x, yy in ((214, y), (298, y + 22)): d.ellipse([(x - 6) * k, (yy - 6) * k, (x + 6) * k, (yy + 6) * k], fill=(216, 37, 24, 255))
    return img.resize((size, size), Image.LANCZOS)

for name, size, mk in (('icon-512.png', 512, False), ('icon-192.png', 192, False), ('icon-180.png', 180, False), ('favicon-32.png', 32, False), ('icon-maskable-512.png', 512, True)):
    render(size, mk).save(OUT / name, optimize=True); print(name)
