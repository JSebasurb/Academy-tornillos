#!/usr/bin/env python3
"""bronze/images/*_raw.png (recortes del catálogo) -> silver/images/*.png (línea clara sobre fondo transparente). Requiere Pillow."""
from PIL import Image
from pathlib import Path
R = Path(__file__).resolve().parent.parent
(R/'silver'/'images').mkdir(exist_ok=True)
for f in sorted((R/'bronze'/'images').glob('*_raw.png')):
    if f.name.startswith('foto_'):  # fotografías: se conservan a color
        im = Image.open(f).convert('RGB'); im = im.resize((im.width*2, im.height*2), Image.LANCZOS)
        im.save(R/'silver'/'images'/f.name.replace('_raw', ''), optimize=True); continue
    im = Image.open(f).convert('RGB'); w, h = im.size; px = im.load(); out = Image.new('RGBA', (w, h)); o = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]; a = min(255, int(max(0, min(r, g) - 40) * 1.7))   # fondo azul oscuro -> transparente
            o[x, y] = (210, 240, 250, a)
    bb = out.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox()
    if bb: out = out.crop((max(bb[0]-6, 0), max(bb[1]-6, 0), min(bb[2]+6, w), min(bb[3]+6, h)))
    out = out.resize((out.width*2//3, out.height*2//3), Image.LANCZOS)
    out.save(R/'silver'/'images'/f.name.replace('_raw', ''), optimize=True); print(f.name, out.size)
