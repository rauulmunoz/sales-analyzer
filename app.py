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
from flask import send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', "pechugadepollo")

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/app')
def index():
    return render_template('index.html')

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
    ruta = request.form['ruta']

    if ruta.endswith('.csv'):
        df = pd.read_csv(ruta)
    else:
        df = pd.read_excel(ruta)

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
                ruta=ruta, 
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
    fig_mes = px.bar(df_mes, x = "mes", y = "total", title = 'Ventas por mes', labels = {'total': 'Total ventas', 'mes': 'Mes'})
    fig_mes.update_traces(marker_color='#1E40AF')

    #Línea de tendencia
    z = np.polyfit(range(len(df_mes)), df_mes['total'], 1)
    p = np.poly1d(z)
    fig_mes.add_scatter(x=df_mes['mes'], y=p(range(len(df_mes))), mode='lines', name='Tendencia', line=dict(color='red', dash='dash'))
    grafica = pio.to_html(fig_mes, full_html=False, include_plotlyjs='cdn')

    #Guardar PNG para PDF con matplotlib
    plt.figure(figsize=(10, 5))
    plt.bar(df_mes['mes'], df_mes['total'])
    plt.title('Ventas por mes')
    plt.xlabel('Mes')
    plt.ylabel('Total ventas')
    plt.tight_layout()
    plt.savefig('uploads/grafica_mes.png')
    plt.close()


    #Grafica ventas por producto con Plotly (interactiva)
    ventas_producto = df.groupby('producto')['precio'].sum().sort_values(ascending=False)
    df_producto = ventas_producto.reset_index()
    df_producto.columns = ['producto', 'total']
    fig_producto = px.bar(df_producto, x='producto', y='total', title='Ventas por producto', labels={'total': 'Total ventas', 'producto': 'Producto'})
    fig_producto.update_traces(marker_color='#1E40AF')
    grafica2 = pio.to_html(fig_producto, full_html=False, include_plotlyjs='cdn')

    #Guardar PNG para PDF con matplotlib
    plt.figure(figsize=(10, 5))
    plt.bar(df_producto['producto'], df_producto['total'])
    plt.title('Ventas por producto')
    plt.xlabel('Producto')
    plt.ylabel('Total ventas')
    plt.tight_layout()
    plt.savefig('uploads/grafica_producto.png')
    plt.close()

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

    fig_top5 = px.bar(top5, x='producto', y='total', title='Mejores 5 productos', labels={'total': 'Total ventas', 'producto': 'Producto'}, color_discrete_sequence=['#2ecc71'])
    grafica_top5 = pio.to_html(fig_top5, full_html=False, include_plotlyjs='False')

    fig_bottom5 = px.bar(bottom5, x='producto', y='total', title='Peores 5 productos', labels={'total': 'Total ventas', 'producto': 'Producto'}, color_discrete_sequence=['#e74c3c'])
    grafica_bottom5 = pio.to_html(fig_bottom5, full_html=False, include_plotlyjs='False')

    #Comparativa mes anterior
    if len(ventas_mes) >= 2:
        ultimo_mes = ventas_mes.iloc[-1]
        mes_anterior = ventas_mes.iloc[-2]
        variacion = ((ultimo_mes -mes_anterior) / mes_anterior) * 100 
        variacion = round(variacion, 1)

    else:
        variacion = None

    total_ventas = float(total_ventas)

    # Resumen ejecutivo
    tendencia_texto = "bajista" if variacion and float(str(variacion)) < 0 else "alcista"
    variacion_abs = abs(float(str(variacion))) if variacion else 0

    resumen = (
        f"En el periodo analizado, las ventas totales alcanzaron {total_ventas:,.2f}€ "
        f"con un ticket medio de {ticket_medio:,.2f}€. "
        f"El mejor mes fue {mejor_mes}, impulsado principalmente por {mejor_producto}, "
        f"que fue el producto más vendido. "
        f"Por otro lado, {peor_mes} fue el mes con peores resultados y {peor_producto} "
        f"el producto con menor rendimiento. "
        f"El {mejor_dia.lower()} es el mejor día para vender, "
        f"mientras que el {peor_dia.lower()} registra las ventas más bajas. "
        f"La tendencia general de ventas es {tendencia_texto}, "
        f"con una variación del {variacion_abs}% respecto al último mes."
    )

    #Borra archjivo subido por privacidad
    try:
        os.remove(ruta)
    except:
        pass


    return render_template('resultado.html',
        grafica = grafica,
        grafica2 = grafica2,
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
        grafica_top5 = grafica_top5,
        grafica_bottom5 = grafica_bottom5,
        ticket_medio = ticket_medio,
        mejor_dia = mejor_dia,
        peor_dia = peor_dia,
        resumen = resumen)

@app.route('/exportar', methods=['POST'])
def exportar():
    from datetime import datetime

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

    ruta_pdf = 'uploads/informe.pdf'
    c = canvas.Canvas(ruta_pdf, pagesize=A4)
    ancho, alto = A4

    COLOR_AZUL = (0.24, 0.57, 0.87)
    COLOR_VERDE = (0.18, 0.80, 0.44)
    COLOR_ROJO = (0.91, 0.30, 0.24)

    def dibujar_tarjeta(cx, y, anch, alt, titulo, valor, accent):
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.roundRect(cx, y, anch, alt, 5, fill=1, stroke=0)
        c.setFillColorRGB(*accent)
        c.rect(cx, y, 5, alt, fill=1, stroke=0)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont('Helvetica', 8)
        c.drawCentredString(cx + anch / 2, y + alt - 15, titulo)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(cx + anch / 2, y + alt / 2 - 5, valor)

    # --- PÁGINA 1: Métricas ---

    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(50, alto - 60, 'Informe de ventas')
    c.setFont('Helvetica', 11)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, alto - 80, 'Resultados generados automaticamente')
    c.setFont('Helvetica', 9)
    c.drawString(50, alto - 100, f'Generado el: {datetime.now().strftime("%d/%m/%Y %H:%M")}')

    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.setLineWidth(1)
    c.line(50, alto - 115, ancho - 50, alto - 115)

    # Fila 1: métricas generales
    tarjetas_f1 = [
        ('Total ventas', f'{total_ventas:.2f} EUR', COLOR_AZUL),
        ('Ticket medio', f'{ticket_medio:.2f} EUR', COLOR_AZUL),
        ('Variacion ultimo mes', f'{variacion}%', COLOR_AZUL),
    ]
    x = 50
    y = alto - 195
    ancho_t1 = 155
    for titulo, valor, color in tarjetas_f1:
        dibujar_tarjeta(x, y, ancho_t1, 55, titulo, valor, color)
        x += ancho_t1 + 10

    # Fila 2: mejores
    tarjetas_f2 = [
        ('Mejor mes', str(mejor_mes), COLOR_VERDE),
        ('Mejor producto', mejor_producto, COLOR_VERDE),
    ]
    x = 50
    y = alto - 270
    ancho_t2 = 240
    for titulo, valor, color in tarjetas_f2:
        dibujar_tarjeta(x, y, ancho_t2, 50, titulo, valor, color)
        x += ancho_t2 + 10

    # Fila 3: peores
    tarjetas_f3 = [
        ('Peor mes', str(peor_mes), COLOR_ROJO),
        ('Peor producto', peor_producto, COLOR_ROJO),
    ]
    x = 50
    y = alto - 340
    for titulo, valor, color in tarjetas_f3:
        dibujar_tarjeta(x, y, ancho_t2, 50, titulo, valor, color)
        x += ancho_t2 + 10

    # Fila 4: días
    tarjetas_f4 = [
        ('Mejor dia', mejor_dia, COLOR_VERDE),
        ('Peor dia', peor_dia, COLOR_ROJO),
    ]
    x = 50
    y = alto - 410
    for titulo, valor, color in tarjetas_f4:
        dibujar_tarjeta(x, y, ancho_t2, 50, titulo, valor, color)
        x += ancho_t2 + 10

    # Resumen ejecutivo
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(50, alto - 460, '¿Qué nos dicen los datos?')
    
    c.setFont('Helvetica', 10)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    
    # Dividir el texto en líneas para que quepa
    from textwrap import wrap
    lineas = wrap(resumen, width=90)
    y_texto = alto - 480
    for linea in lineas:
        c.drawString(50, y_texto, linea)
        y_texto -= 15

    # --- PÁGINA 2: Gráficas ---
    c.showPage()

    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(50, alto - 60, 'Ventas por mes')
    c.drawImage('uploads/grafica_mes.png', 50, alto - 330, width=ancho - 100, height=250)

    c.setFont('Helvetica-Bold', 14)
    c.drawString(50, alto - 360, 'Ventas por producto')
    c.drawImage('uploads/grafica_producto.png', 50, alto - 630, width=ancho - 100, height=250)

    c.save()
    return send_file(ruta_pdf, as_attachment=True)

if __name__=='__main__':
    app.run(debug=True)
