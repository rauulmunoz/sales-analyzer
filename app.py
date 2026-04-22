from flask import Flask, render_template, request
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt 
import io 
import base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from flask import send_file

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    archivo = request.files['archivo']
    ruta = 'uploads/' + archivo.filename
    archivo.save(ruta)

    if archivo.filename.endswith('.csv'):
        df = pd.read_csv(ruta)
    else:
        df = pd.read_excel(ruta)

    columnas = list(df.columns)
    return render_template('mapeo.html', columnas = columnas, ruta = ruta)

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
    df = df[list(columnas_utiles.keys())].rename(columns = columnas_utiles)

    #convertir fecha y agrupar por mes
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['mes'] = df['fecha'].dt.to_period('M')
    ventas_mes = df.groupby('mes')['precio'].sum()

    #Gráfica ventas por mes
    plt.figure(figsize=(10,5))
    ventas_mes.plot(kind='bar')
    plt.title('Ventas por mes')
    plt.xlabel('Mes')
    plt.ylabel('Total ventas')
    plt.tight_layout()

    #convertir gráfica a imagen
    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.savefig('uploads/grafica_mes.png')
    img.seek(0)
    grafica = base64.b64encode(img.getvalue()).decode()
    plt.close()


    #Grafica ventas por producto
    ventas_producto = df.groupby('producto')['precio'].sum().sort_values(ascending=False)

    plt.figure(figsize=(10,5))
    ventas_producto.plot(kind='bar')
    plt.title('Ventas por producto')
    plt.xlabel('Producto')
    plt.ylabel('Total ventas')
    plt.tight_layout()

    img2 = io.BytesIO()
    plt.savefig(img2, format='png')
    plt.savefig('uploads/grafica_producto.png')
    img.seek(0)
    grafica2 = base64.b64encode(img2.getvalue()).decode()
    plt.close()

    #Resumen
    total_ventas = df['precio'].sum()
    mejor_mes = ventas_mes.idxmax()
    mejor_producto = ventas_producto.idxmax()
    peor_mes = ventas_mes.idxmin()
    peor_producto = ventas_producto.idxmin()

    return render_template('resultado.html',
        grafica = grafica,
        grafica2 = grafica2,
        total_ventas = total_ventas,
        mejor_mes = mejor_mes,
        mejor_producto = mejor_producto,
        peor_mes = peor_mes,
        peor_producto = peor_producto)

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
