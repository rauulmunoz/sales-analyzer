from flask import Flask, render_template, request

#Crear la aplicacion web
#El __name__ le dice a Flask donde esta el archivo para que encuentre las carpetas templates y static
app = Flask(__name__)

#Le dice a Flask "cuando alguien entre a la direccion raiz de la web, ejecuta la funcion de abajo", el / es la página principal, como el index
@app.route('/')
#La funcion se ejecuta cuando alguien entra a esa ruta, ahora mismo solo devuelve un texto
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    archivo = request.files['archivo']
    return 'Archivo recibido: '+archivo.filename

if __name__=='__main__':
    app.run(debug=True)
