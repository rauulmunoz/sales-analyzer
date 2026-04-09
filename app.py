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
    columnas = list(df.columns)
    return render_template('mapeo.html', columnas = columnas)

if __name__=='__main__':
    app.run(debug=True)
