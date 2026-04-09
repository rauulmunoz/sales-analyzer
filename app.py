from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

@app.route('/')

def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    archivo = request.files['archivo']
    df =pd.read_csv(archivo)
    filas = len(df)
    columnas = list(df.columns)
    return f'Filas: {filas} | Columnas: {columnas}'

if __name__=='__main__':
    app.run(debug=True)
