# Sales Analyzer 📊

**Herramienta web gratuita para analizar datos de ventas desde Excel o CSV y generar informes automáticos con gráficas interactivas y PDF descargable.**

🔗 **[Ver demo en vivo](https://sales-analyzer-pov5.onrender.com)**

---

## ¿Qué hace?

Sube tu archivo Excel o CSV con datos de ventas, asigna las columnas y obtén en segundos:

- Gráficas interactivas de ventas por mes y por producto
- Métricas clave: total de ventas, ticket medio, variación respecto al mes anterior
- Mejor y peor mes, producto y día de la semana
- Línea de tendencia automática
- Resumen ejecutivo generado automáticamente
- Informe PDF descargable
- Limpieza automática de datos (duplicados y filas vacías)

## Tecnologías

- **Backend:** Python, Flask
- **Análisis de datos:** pandas, numpy
- **Gráficas:** Plotly (interactivas), matplotlib (PDF)
- **PDF:** ReportLab
- **Frontend:** HTML, CSS, Bootstrap 5
- **Deploy:** Render

## Cómo ejecutarlo en local

```bash
git clone https://github.com/rauulmunoz/sales-analyzer.git
cd sales-analyzer
pip install -r requirements.txt
python app.py
```

Entra a `http://localhost:5000`

## Autor

Raúl Muñoz — [LinkedIn](https://linkedin.com/in/raúl-muñoz-garcía) · [GitHub](https://github.com/rauulmunoz)
