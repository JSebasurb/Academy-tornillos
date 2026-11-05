# Academia CATO · Tornillería industrial

Academia interactiva (PWA, funciona sin conexión) basada en el catálogo de Industrias CATO S.A.
Organizada con **arquitectura medallón** y lista para **GitHub Pages**.

## Capas de datos

| Capa | Carpeta | Contenido | Regla |
|---|---|---|---|
| 🥉 Bronze | `bronze/` | Extracción cruda: texto del catálogo (`catalogo_cato_texto.txt`), columnas tal como salen del PDF (`tables_raw.json`) y contenido didáctico sin tipar (`content_raw.json`) | Nunca se edita a mano salvo para corregir una transcripción |
| 🥈 Silver | `silver/` | Datos normalizados y tipados: tablas con esquema (columna numérica o no), cabezas, puntas, procesos, cronología, selector, retos, calibres. `validation_report.json` | Se regenera y **se valida** en cada build |
| 🥇 Gold | `gold/` | Consumo: `cato.json` (todo), `search_index.json`, `csv/*.csv` | Lo único que lee la app |

`python tools/build.py` ejecuta bronze → silver → validación → gold → `docs/`.

Validaciones: filas con el mismo número de celdas que columnas; máx ≥ mín; calibres vs fórmula ANSI (d = 0,060 + 0,013·N″); jerarquía mayor > medio > menor en UNC/UNF; respuestas de retos dentro de rango; ids únicos. Si falla, el build termina con error y no se publica.

## Publicar en GitHub Pages
1. Sube este repositorio a GitHub (rama `main`).
2. *Settings → Pages → Source: GitHub Actions*. El workflow `.github/workflows/pages.yml` construye y despliega `docs/`.
   (Alternativa sin Actions: Source = *Deploy from a branch*, carpeta `/docs`.)
3. Rutas relativas: funciona en `usuario.github.io/repo/` sin cambios.

## Estructura
```
bronze/  silver/  gold/        capas medallón
src/base.html                  interfaz (HTML+CSS+JS base de la academia)
src/js/taller.js               Taller CATO+: tablas, calculadoras, diagramas, retos
src/pwa/                       service worker, manifest, icono, 404
tools/build.py                 pipeline
docs/                          sitio generado (Pages)
dist/Academia_CATO_standalone.html   un solo archivo, sin servidor
```
## Cómo añadir o corregir datos
Edita `bronze/tables_raw.json` (o `content_raw.json`), ejecuta `python tools/build.py` y revisa `silver/validation_report.json`.
El PDF original del catálogo (≈54 MB) no se incluye por tamaño; colócalo en `bronze/source/` si usas Git LFS.

> Los valores se transcriben del catálogo CATO; para fabricación o liberación prevalecen plano, norma y ficha vigentes.
