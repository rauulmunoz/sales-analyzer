# Sales Analyzer

Herramienta web para analizar datos de ventas a partir de un archivo Excel o CSV. Genera métricas clave, gráficas interactivas y un informe PDF descargable en menos de 60 segundos.

🔗 **[Ver demo en vivo](https://sales-analyzer-pov5.onrender.com)**

---


## Funcionalidades

- Sube tu archivo Excel (.xlsx) o CSV — sin formato especial
- Mapeo flexible de columnas: tú decides qué columna es fecha, precio y producto
- Limpieza automática de datos: elimina duplicados y filas vacías
- Dashboard interactivo con filtros por trimestre y mes
- Métricas clave: total ventas, ticket medio, variación mes a mes
- Gráficas de ventas por mes, producto, día de la semana, top 5 y peores 5
- Tabla de detalle mensual con variación y producto top por mes
- Exportación a PDF con diseño profesional
- Datos de demo precargados para probar sin necesidad de subir un archivo

---

## Stack

- **Backend:** Python, Flask, pandas, NumPy
- **Gráficas web:** Plotly.js
- **Generación PDF:** ReportLab, Matplotlib
- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript
- **Deploy:** Render

---

## Instalación local

```bash
git clone https://github.com/rauulmunoz/sales-analyzer.git
cd sales-analyzer
pip install -r requirements.txt
python app.py
```

La app estará disponible en `http://localhost:5000`.

---

## Uso

1. Sube tu archivo Excel o CSV con datos de ventas
2. Asigna las columnas (fecha, producto, precio)
3. Explora el dashboard con filtros interactivos
4. Descarga el informe PDF

También puedes pulsar **"Probar con datos de ejemplo"** para ver la app funcionando sin necesidad de tener un archivo.

---

## Seguridad

- Validación de rutas con protección contra path traversal
- Los archivos subidos se eliminan del servidor tras el análisis
- Secret key gestionada mediante variables de entorno

---

## Autor

**Raúl Muñoz** — [LinkedIn](https://linkedin.com/in/raúl-muñoz-garcía) · [GitHub](https://github.com/rauulmunoz) 


