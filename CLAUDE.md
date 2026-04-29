# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
python app.py
```

The app starts on `http://localhost:5000` in debug mode. The `SECRET_KEY` env var overrides the default.

## Dependencies

Install with pip: `flask pandas matplotlib reportlab openpyxl werkzeug`

No `requirements.txt` exists yet — consider creating one.

## Architecture

Single-file Flask app (`app.py`) with no database. All logic lives in route handlers.

**User flow:**
1. `/` — marketing landing page
2. `/app` — file upload form (`index.html`)
3. `POST /upload` — saves file to `uploads/`, passes column list to column-mapping page (`mapeo.html`)
4. `POST /analizar` — reads the saved file, renames columns per user mapping, generates two matplotlib charts (sales by month, sales by product), saves PNG files to `uploads/`, returns results page with base64-embedded charts (`resultado.html`)
5. `POST /exportar` — reads the already-saved PNGs and summary values posted from the form, builds a PDF with reportlab, returns it as a download

**State between requests is passed via:**
- The file path stored in `uploads/` (passed as a hidden form field `ruta`)
- Chart PNGs saved to `uploads/grafica_mes.png` and `uploads/grafica_producto.png` (read again at export time)
- Summary values embedded as hidden fields in `resultado.html` and re-posted to `/exportar`

**Required column mappings** (validated in `/analizar`): `fecha`, `precio`, `producto`. The `cantidad` field exists in the mapping UI but is not currently used in analysis.

## Templates

Jinja2 templates under `templates/`, styled with Bootstrap 5 (CDN). No JavaScript beyond Bootstrap.
