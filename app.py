from flask import Flask, render_template, request
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt 
import io 
import base64

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    archivo = request.files['archivo']
    ruta = 'uploads/' + archivo.filename
    archivo.save(ruta)
    df =pd.read_csv(ruta)
    columnas = list(df.columns)
    return render_template('mapeo.html', columnas = columnas, ruta = ruta)

@app.route('/analizar', methods=['POST'])
def analizar():
    ruta = request.form['ruta']
    df = pd.read_csv(ruta)

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
    img.seek(0)
    grafica2 = base64.b64encode(img2.getvalue()).decode()
    plt.close()

    return render_template('resultado.html', grafica = grafica, grafica2 = grafica2)

if __name__=='__main__':
    app.run(debug=True)
