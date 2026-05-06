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

    #Comparativa mes anterior
    if len(ventas_mes) >= 2:
        ultimo_mes = ventas_mes.iloc[-1]
        mes_anterior = ventas_mes.iloc[-2]
        variacion = ((ultimo_mes -mes_anterior) / mes_anterior) * 100 
        variacion = round(variacion, 1)

    else:
        variacion = None

    total_ventas = float(total_ventas)

    return render_template('resultado.html',
        grafica = grafica,
        grafica2 = grafica2,
        total_ventas = total_ventas,
        mejor_mes = mejor_mes,
        mejor_producto = mejor_producto,
        peor_mes = peor_mes,
        peor_producto = peor_producto,
        variacion = variacion,
        filas_vacias = filas_vacias,
        duplicados = duplicados)

@app.route('/exportar', methods=['POST'])
def exportar():
    total_ventas = float(request.form['total_ventas'])
    mejor_mes = request.form['mejor_mes']
    mejor_producto = request.form['mejor_producto']
    peor_mes = request.form['peor_mes']
    peor_producto = request.form['peor_producto']

    ruta_pdf = 'uploads/informe.pdf'
    c = canvas.Canvas(ruta_pdf, pagesize=A4)
    ancho, alto = A4

    # Título
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(50, alto - 60, 'Informe de ventas')
    c.setFont('Helvetica', 11)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, alto - 80, 'Resultados generados automaticamente')

    # Tarjetas resumen
    tarjetas = [
        ('Total ventas', f'{total_ventas:.2f} EUR'),
        ('Mejor mes', str(mejor_mes)),
        ('Mejor producto', mejor_producto),
        ('Peor mes', str(peor_mes)),
        ('Peor producto', peor_producto),
    ]

    x = 50
    y = alto - 160
    ancho_tarjeta = 95
    for titulo, valor in tarjetas:
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.roundRect(x, y, ancho_tarjeta, 55, 5, fill=1, stroke=0)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont('Helvetica', 8)
        c.drawCentredString(x + ancho_tarjeta/2, y + 42, titulo)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(x + ancho_tarjeta/2, y + 20, valor)
        x += ancho_tarjeta + 10

    # Gráficas
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(50, alto - 240, 'Ventas por mes')
    c.drawImage('uploads/grafica_mes.png', 50, alto - 450, width=480, height=200)

    c.drawString(50, alto - 470, 'Ventas por producto')
    c.drawImage('uploads/grafica_producto.png', 50, alto - 680, width=480, height=200)

    c.save()
    return send_file(ruta_pdf, as_attachment=True)

if __name__=='__main__':
    app.run(debug=True)
