from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt 
import plotly.express as px
import plotly.io as pio
import io 
import base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from flask import send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', "pechugadepollo")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

def ruta_segura(ruta):
    ruta_abs = os.path.realpath(os.path.join(BASE_DIR, ruta))
    upload_abs = os.path.realpath(UPLOADS_DIR)
    static_abs = os.path.realpath(os.path.join(BASE_DIR, 'static'))
    if not (ruta_abs.startswith(upload_abs + os.sep) or ruta_abs.startswith(static_abs + os.sep)):
        raise ValueError(f"Ruta no permitida: {ruta}")
    return ruta_abs

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/app')
def index():
    return render_template('index.html')

@app.route('/demo')
def demo():
    ruta = os.path.join(BASE_DIR, 'static', 'demo_ventas.csv')
    df = pd.read_csv(ruta)
    columnas = list(df.columns)
    ruta_rel = 'static/demo_ventas.csv'
    return render_template('mapeo.html', columnas = columnas, ruta = ruta_rel)

@app.route('/upload', methods=['POST'])
def upload():
    archivo = request.files['archivo']

    filename = archivo.filename

    if filename == '':
        return render_template('index.html', error = 'Por favor selecciona un archivo antes de continuar')

    if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
        return render_template('index.html', error = 'Solo se admiten archivos CSV o Excel')

    try:
        filename = secure_filename(filename)
        ruta = 'uploads/' +filename
        archivo.save(ruta)

        if filename.endswith('.csv'):
            df = pd.read_csv(ruta)
        else:
            df = pd.read_excel(ruta)

        columnas = list(df.columns)
        return render_template('mapeo.html', columnas = columnas, ruta = ruta)

    except Exception as e:
        return render_template('index.html', error = f'Error: {str(e)}')


@app.route('/analizar', methods=['POST'])
def analizar():
    ruta_form = request.form['ruta']
    try:
        ruta_abs = ruta_segura(ruta_form)
    except ValueError:
        return render_template('index.html', error='Ruta de archivo no válida.')

    if not os.path.exists(ruta_abs):
        return render_template('index.html', error='El archivo ya no existe. Por favor sube el archivo de nuevo.')

    if ruta_abs.endswith('.csv'):
        df = pd.read_csv(ruta_abs)
    else:
        df = pd.read_excel(ruta_abs)

    mapeo = {}
    for columna in df.columns:
        mapeo[columna] = request.form[columna]

    #Renombrar columnas según el mapeo
    columnas_utiles = {col: mapeo[col] for col in mapeo if mapeo[col] != 'ignorar'}

    campos_requeridos = ['fecha', 'precio', 'producto']
    campos_asignados = list(columnas_utiles.values())
    
    for campo in campos_requeridos:
        if campo not in campos_asignados:
            return render_template('mapeo.html', 
                columnas=list(df.columns), 
                ruta=ruta_form, 
                error=f'Debes asignar al menos una columna como "{campo}"')
                
    df = df[list(columnas_utiles.keys())].rename(columns = columnas_utiles)

    #Limpieza de datos
    filas_antes = len(df)

    #Eliminar filas completamente vacías
    df = df.dropna(how='all')
    filas_vacias = filas_antes - len(df)

    #Eliminar filas duplicadas
    filas_antes_duplicados = len(df)
    df = df.drop_duplicates()
    duplicados = filas_antes_duplicados - len(df)

    #Quitar espacios en blanco en columnas de texto
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()

    df['precio'] = pd.to_numeric(df['precio'], errors='coerce')

    #convertir fecha y agrupar por mes
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['mes'] = df['fecha'].dt.to_period('M')
    ventas_mes = df.groupby('mes')['precio'].sum()

    #Gráfica ventas por mes con Plotly (interactiva)
    df_mes = ventas_mes.reset_index()
    df_mes.columns = ['mes', 'total']
    df_mes['mes'] = df_mes['mes'].astype(str)
    

    #Guardar PNG para PDF con matplotlib
    buf_mes = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.bar(df_mes['mes'], df_mes['total'], color='#1E40AF')
    plt.title('Ventas por mes')
    plt.xlabel('Mes')
    plt.ylabel('Total ventas')
    plt.tight_layout()
    plt.savefig(buf_mes, format='png', dpi=150)
    plt.close()
    buf_mes.seek(0)
    img_mes_b64 = base64.b64encode(buf_mes.read()).decode('utf-8')


    #Grafica ventas por producto con Plotly (interactiva)
    ventas_producto = df.groupby('producto')['precio'].sum().sort_values(ascending=False)
    df_producto = ventas_producto.reset_index()
    df_producto.columns = ['producto', 'total']

    #Guardar PNG para PDF con matplotlib
    buf_prod = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.bar(df_producto['producto'], df_producto['total'], color='#1E40AF')
    plt.title('Ventas por producto')
    plt.xlabel('Producto')
    plt.ylabel('Total ventas')
    plt.tight_layout()
    plt.savefig(buf_prod, format='png', dpi=150)
    plt.close()
    buf_prod.seek(0)
    img_prod_b64 = base64.b64encode(buf_prod.read()).decode('utf-8')

    #Resumen
    total_ventas = df['precio'].sum()
    mejor_mes = ventas_mes.idxmax()
    mejor_producto = ventas_producto.idxmax()
    peor_mes = ventas_mes.idxmin()
    peor_producto = ventas_producto.idxmin()

    meses_es = {
    'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
    'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
    'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
    'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
    }
    mejor_mes_dt = datetime.strptime(str(mejor_mes), "%Y-%m")
    peor_mes_dt = datetime.strptime(str(peor_mes), "%Y-%m")
    mejor_mes_fmt = meses_es[mejor_mes_dt.strftime("%B")] + ' ' + mejor_mes_dt.strftime("%Y")
    peor_mes_fmt = meses_es[peor_mes_dt.strftime("%B")] + ' ' + peor_mes_dt.strftime("%Y")
    #Ticket medio
    ticket_medio = round(float(df['precio'].mean()), 2)

    #Mejor y peor día de la semana
    dias_es = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    df['dia_semana'] = df['fecha'].dt.day_name().map(dias_es)
    
    ventas_dia = df.groupby('dia_semana')['precio'].sum()
    mejor_dia = ventas_dia.idxmax()
    peor_dia = ventas_dia.idxmin()

    #Top 5 y Peores 5 productos
    top5 = ventas_producto.head(5).reset_index()
    top5.columns = ['producto', 'total']
    bottom5 = ventas_producto.tail(5).reset_index()
    bottom5.columns = ['producto', 'total']

    top5_json = json.dumps(top5.to_dict(orient='records'))
    bottom5_json = json.dumps(bottom5.to_dict(orient='records'))

    #Comparativa mes anterior
    if len(ventas_mes) >= 2:
        ultimo_mes = ventas_mes.iloc[-1]
        mes_anterior = ventas_mes.iloc[-2]
        variacion = ((ultimo_mes -mes_anterior) / mes_anterior) * 100 
        variacion = round(variacion, 1)

    else:
        variacion = None

    total_ventas = float(total_ventas)

    ventas_mes_json = json.dumps(df_mes.to_dict(orient='records'))
    ventas_prod_json = json.dumps(df_producto.to_dict(orient='records'))
    ventas_dia_json = json.dumps(df.groupby('dia_semana')['precio'].sum().reset_index().rename(columns={'precio': 'total'}).to_dict(orient='records'))
    top_producto_mes = df.groupby(['mes', 'producto'])['precio'].sum().reset_index()
    top_producto_mes['mes'] = top_producto_mes['mes'].astype(str)
    top_producto_mes = top_producto_mes.loc[top_producto_mes.groupby('mes')['precio'].idxmax()]
    top_prod_mes_json = json.dumps(top_producto_mes[['mes', 'producto']].to_dict(orient='records'))

    # Resumen ejecutivo
    if variacion is not None:
        tendencia_texto = "bajista" if variacion < 0 else "alcista"
        variacion_abs = abs(variacion)
        variacion_texto = f"con una variacion del {variacion_abs}% respecto al último mes."
    else:
        tendencia_texto = "estable"
        variacion_abs = 0
        variacion_texto = "con datos de un único mes."

    resumen = (
        f"En el periodo analizado, las ventas totales alcanzaron {total_ventas:,.2f}€ "
        f"con un ticket medio de {ticket_medio:,.2f}€. "
        f"El mejor mes fue {mejor_mes_fmt}, impulsado principalmente por {mejor_producto}, "
        f"que fue el producto más vendido. "
        f"Por otro lado, {peor_mes_fmt} fue el mes con peores resultados y {peor_producto} "
        f"el producto con menor rendimiento. "
        f"El {mejor_dia.lower()} es el mejor día para vender, "
        f"mientras que el {peor_dia.lower()} registra las ventas más bajas. "
        f"La tendencia general de ventas es {tendencia_texto}, {variacion_texto}"
    )

    #Borra archivo subido por privacidad
    try:
        if 'uploads' in ruta:
            os.remove(ruta)
    except:
        pass


    return render_template('resultado.html',
        total_ventas = total_ventas,
        mejor_mes = mejor_mes,
        mejor_mes_fmt = mejor_mes_fmt,
        mejor_producto = mejor_producto,
        peor_mes = peor_mes,
        peor_mes_fmt = peor_mes_fmt,
        peor_producto = peor_producto,
        variacion = variacion,
        filas_vacias = filas_vacias,
        duplicados = duplicados,
        top5_json = top5_json,
        bottom5_json = bottom5_json,
        ticket_medio = ticket_medio,
        mejor_dia = mejor_dia,
        peor_dia = peor_dia,
        img_mes_b64 = img_mes_b64,
        img_prod_b64 = img_prod_b64,
        ventas_mes_json = ventas_mes_json,
        ventas_prod_json = ventas_prod_json,
        ventas_dia_json = ventas_dia_json,
        top_prod_mes_json = top_prod_mes_json,
        resumen = resumen)

@app.route('/exportar', methods=['POST'])
def exportar():
    from datetime import datetime
    from textwrap import wrap

    total_ventas = float(request.form['total_ventas'])
    mejor_mes = request.form['mejor_mes']
    mejor_producto = request.form['mejor_producto']
    peor_mes = request.form['peor_mes']
    peor_producto = request.form['peor_producto']
    ticket_medio = float(request.form['ticket_medio'])
    variacion = request.form['variacion']
    mejor_dia = request.form['mejor_dia']
    peor_dia = request.form['peor_dia']
    resumen = request.form['resumen']
    img_mes_b64 = request.form['img_mes_b64']
    img_prod_b64 = request.form['img_prod_b64']
    buf_mes = io.BytesIO(base64.b64decode(img_mes_b64)) if img_mes_b64 else None
    buf_prod = io.BytesIO(base64.b64decode(img_prod_b64)) if img_prod_b64 else None

    ruta_pdf = os.path.join(UPLOADS_DIR, f'informe_{uuid.uuid4().hex}.pdf')
    c = canvas.Canvas(ruta_pdf, pagesize=A4)
    ancho, alto = A4

    # Colores
    AZUL_OSC = (0.118, 0.227, 0.373)   # #1e3a5f
    AZUL_MED = (0.118, 0.251, 0.686)   # #1e40af
    AZUL_CLR = (0.576, 0.773, 1.0)     # #93c5fd
    VERDE    = (0.051, 0.431, 0.247)   # #0d6e3f
    ROJO     = (0.753, 0.224, 0.169)   # #c0392b
    GRIS     = (0.533, 0.533, 0.533)
    NEGRO    = (0.067, 0.067, 0.067)

    # ── CABECERA AZUL OSCURO ──────────────────────────────────
    c.setFillColorRGB(*AZUL_OSC)
    c.rect(0, alto - 80, ancho, 80, fill=1, stroke=0)

    # Título y subtítulo
    c.setFillColorRGB(1, 1, 1)
    c.setFont('Helvetica-Bold', 20)
    c.drawString(40, alto - 38, 'Informe de ventas')
    c.setFont('Helvetica', 9)
    c.setFillColorRGB(*AZUL_CLR)
    c.drawString(40, alto - 54, f'Generado el {datetime.now().strftime("%d/%m/%Y %H:%M")}  ·  Sales Analyzer')

    # Pastilla total ventas (esquina derecha)
    pastilla_x = ancho - 160
    c.setFillColorRGB(0.2, 0.45, 0.65)
    c.roundRect(pastilla_x, alto - 62, 120, 34, 6, fill=1, stroke=0)
    c.setFillColorRGB(*AZUL_CLR)
    c.setFont('Helvetica', 8)
    c.drawCentredString(pastilla_x + 60, alto - 36, 'Total ventas')
    c.setFillColorRGB(1, 1, 1)
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(pastilla_x + 60, alto - 52, f'{total_ventas:,.2f} EUR')

    # ── FILA KPIs ─────────────────────────────────────────────
    kpi_y = alto - 155
    kpis = [
        ('Ticket medio',     f'{ticket_medio:,.2f} EUR', AZUL_MED, (0.875, 0.929, 1.0)),
        ('Mejor mes',        mejor_mes,                  VERDE,     (0.875, 0.961, 0.925)),
        ('Variación',        f'▲ {variacion}%' if variacion and float(variacion) >= 0 else f'▼ {variacion}%',
                             VERDE if variacion and float(variacion) >= 0 else ROJO,
                             (0.875, 0.961, 0.925) if variacion and float(variacion) >= 0 else (0.992, 0.910, 0.910)),
    ]
    kpi_w = (ancho - 80) / 3
    for i, (label, valor, color_val, color_bg) in enumerate(kpis):
        x = 40 + i * (kpi_w + 10)
        c.setFillColorRGB(*color_bg)
        c.roundRect(x, kpi_y, kpi_w - 10, 48, 5, fill=1, stroke=0)
        c.setFillColorRGB(*GRIS)
        c.setFont('Helvetica', 8)
        c.drawString(x + 10, kpi_y + 34, label)
        c.setFillColorRGB(*color_val)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(x + 10, kpi_y + 16, valor)

    # ── FILA MEJOR / PEOR ─────────────────────────────────────
    fila2_y = kpi_y - 65
    fila2 = [
        ('Mejor producto', mejor_producto, VERDE,  (0.875, 0.961, 0.925)),
        ('Peor producto',  peor_producto,  ROJO,   (0.992, 0.910, 0.910)),
        ('Mejor día',      mejor_dia,      VERDE,  (0.875, 0.961, 0.925)),
        ('Peor día',       peor_dia,       ROJO,   (0.992, 0.910, 0.910)),
    ]
    kpi_w2 = (ancho - 80) / 4
    for i, (label, valor, color_val, color_bg) in enumerate(fila2):
        x = 40 + i * (kpi_w2 + 6)
        c.setFillColorRGB(*color_bg)
        c.roundRect(x, fila2_y, kpi_w2 - 6, 44, 5, fill=1, stroke=0)
        c.setFillColorRGB(*GRIS)
        c.setFont('Helvetica', 8)
        c.drawString(x + 8, fila2_y + 30, label)
        c.setFillColorRGB(*color_val)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(x + 8, fila2_y + 14, valor[:18])

    # ── LÍNEA SEPARADORA ──────────────────────────────────────
    sep_y = fila2_y - 18
    c.setStrokeColorRGB(0.878, 0.878, 0.878)
    c.setLineWidth(0.5)
    c.line(40, sep_y, ancho - 40, sep_y)

    # ── RESUMEN EJECUTIVO ─────────────────────────────────────
    c.setFillColorRGB(*AZUL_OSC)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(40, sep_y - 18, '¿Qué nos dicen los datos?')

    c.setFont('Helvetica', 9)
    c.setFillColorRGB(*NEGRO)
    lineas = wrap(resumen, width=100)
    y_texto = sep_y - 34
    for linea in lineas:
        if y_texto < 40:
            break
        c.drawString(40, y_texto, linea)
        y_texto -= 13

    # ── PÁGINA 2: GRÁFICAS ────────────────────────────────────
    c.showPage()

    c.setFillColorRGB(*AZUL_OSC)
    c.rect(0, alto - 50, ancho, 50, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(40, alto - 32, 'Análisis gráfico')
    c.setFont('Helvetica', 9)
    c.setFillColorRGB(*AZUL_CLR)
    c.drawString(40, alto - 44, 'Sales Analyzer')

    c.setFillColorRGB(*AZUL_OSC)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(40, alto - 75, 'Ventas por mes')
    if buf_mes:
        c.drawImage(ImageReader(buf_mes), 40, alto - 340, width=ancho - 80, height=260)

    c.setFont('Helvetica-Bold', 11)
    c.drawString(40, alto - 360, 'Ventas por producto')
    if buf_prod:
        c.drawImage(ImageReader(buf_prod), 40, alto - 640, width=ancho - 80, height=260)

    c.save()
    response = send_file(ruta_pdf, as_attachment=True, download_name='informe_ventas.pdf')

    @response.call_on_close
    def limpiar():
        try:
            os.remove(ruta_pdf)
        except:
            pass

    return response

if __name__=='__main__':
    app.run(debug=True)
