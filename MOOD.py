import os
from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Railway define automaticamente la variable MONGO_URI
# Nunca pongas tu usuario y password directo en el codigo
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise ValueError("No se encontro la variable de entorno MONGO_URI")

cliente = MongoClient(MONGO_URI)

db = cliente["mood"]

usuarios  = db["usuarios"]
peliculas = db["peliculas"]
series    = db["series"]
libros    = db["libros"]


# ── USUARIOS ──────────────────────────────────────────────

@app.route("/usuarios", methods=["POST"])
def insertar_usuario():
    datos = request.json
    usuarios.insert_one(datos)
    return jsonify({"mensaje": "Usuario agregado"})


@app.route("/usuarios", methods=["GET"])
def ver_usuarios():
    resultado = []
    for usuario in usuarios.find():
        resultado.append({
            "nombre":         usuario.get("nombre", ""),
            "edad":           usuario.get("edad", ""),
            "generofavorito": usuario.get("generofavorito", "")
        })
    return jsonify(resultado)


# ── PELICULAS ─────────────────────────────────────────────

@app.route("/peliculas", methods=["POST"])
def insertar_peliculas():
    datos = request.json
    peliculas.insert_one(datos)
    return jsonify({"mensaje": "Pelicula agregada"})


@app.route("/peliculas/<titulo>", methods=["GET"])
def buscar_pelicula(titulo):
    pelicula = peliculas.find_one({"titulo": titulo})
    if pelicula:
        return jsonify({
            "titulo":     pelicula.get("titulo", ""),
            "genero":     pelicula.get("genero", ""),
            "duracion":   pelicula.get("duracion", 0),
            "plataforma": pelicula.get("plataforma", "")
        })
    return jsonify({"mensaje": "Pelicula no encontrada"}), 404


# ── SERIES ────────────────────────────────────────────────

@app.route("/series", methods=["POST"])
def insertar_series():
    datos = request.json
    series.insert_one(datos)
    return jsonify({"mensaje": "Serie agregada"})


@app.route("/series/<titulo>", methods=["GET"])
def buscar_serie(titulo):
    serie = series.find_one({"titulo": titulo})
    if serie:
        return jsonify({
            "titulo":     serie.get("titulo", ""),
            "genero":     serie.get("genero", ""),
            "temporadas": serie.get("temporadas", 0),
            "plataforma": serie.get("plataforma", "")
        })
    return jsonify({"mensaje": "Serie no encontrada"}), 404


# ── LIBROS ────────────────────────────────────────────────

@app.route("/libros", methods=["POST"])
def insertar_libros():
    datos = request.json
    libros.insert_one(datos)
    return jsonify({"mensaje": "Libro agregado"})


@app.route("/libros/<titulo>", methods=["GET"])
def buscar_libro(titulo):
    libro = libros.find_one({"titulo": titulo})
    if libro:
        return jsonify({
            "titulo": libro.get("titulo", ""),
            "autor":  libro.get("autor", ""),
            "genero": libro.get("genero", "")
        })
    return jsonify({"mensaje": "Libro no encontrado"}), 404


# ── RECOMENDACIONES ───────────────────────────────────────

@app.route("/recomendacion/<nombre>", methods=["GET"])
def recomendar(nombre):
    usuario = usuarios.find_one({"nombre": nombre})

    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    mood   = usuario.get("estado_animo", "")
    tiempo = usuario.get("tiempo_disponible", 9999)

    recomendaciones_peliculas = []
    recomendaciones_series    = []
    recomendaciones_libros    = []

    for pelicula in peliculas.find({"mood": mood}):
        if pelicula.get("duracion", 0) <= tiempo:
            recomendaciones_peliculas.append({
                "titulo":     pelicula.get("titulo", ""),
                "genero":     pelicula.get("genero", ""),
                "duracion":   pelicula.get("duracion", 0),
                "plataforma": pelicula.get("plataforma", "")
            })

    for serie in series.find({"mood": mood}):
        recomendaciones_series.append({
            "titulo":     serie.get("titulo", ""),
            "genero":     serie.get("genero", ""),
            "temporadas": serie.get("temporadas", 0),
            "plataforma": serie.get("plataforma", "")
        })

    for libro in libros.find({"mood": mood}):
        recomendaciones_libros.append({
            "titulo":  libro.get("titulo", ""),
            "autor":   libro.get("autor", ""),
            "paginas": libro.get("paginas", 0)
        })

    return jsonify({
        "usuario":   usuario.get("nombre", ""),
        "mood":      mood,
        "peliculas": recomendaciones_peliculas,
        "series":    recomendaciones_series,
        "libros":    recomendaciones_libros
    })


# ── ARRANQUE ──────────────────────────────────────────────

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
