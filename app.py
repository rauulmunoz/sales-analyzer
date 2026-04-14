from flask import Flask, render_template, request
import pandas as pd

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

    return df.to_html()

if __name__=='__main__':
    app.run(debug=True)
