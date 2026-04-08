from flask import Flask

#Crear la aplicacion web
#El __name__ le dice a Flask donde esta el archivo para que encuentre las carpetas templates y static
app = Flask(__name__)

#Le dice a Flask "cuando alguien entre a la direccion raiz de la web, ejecuta la funcion de abajo", el / es la página principal, como el index
@app.route('/')
#La funcion se ejecuta cuando alguien entra a esa ruta, ahora mismo solo devuelve un texto
def index():
    return 'Hola sales-analyzer funciona!'


if __name__=='__main__':
    app.run(debug=True)
