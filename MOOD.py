import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
import datetime

app = Flask(__name__)
CORS(app)

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


def doc_to_json(d):
    """Convierte ObjectId a string para poder enviarlo como JSON."""
    if d and "_id" in d:
        d["_id"] = str(d["_id"])
    return d


# ---------------- HEALTH ----------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "msg": "Mood API funcionando"})


# ---------------- AUTH ----------------
@app.route("/registro", methods=["POST"])
def registro():
    data = request.get_json()
    nombre = data.get("nombre", "").strip()
    correo = data.get("correo", "").strip().lower()
    password = data.get("password", "")

    if not nombre or not correo or not password:
        return jsonify({"ok": False, "msg": "Faltan datos"}), 400

    if db.usuarios.find_one({"correo": correo}):
        return jsonify({"ok": False, "msg": "Ese correo ya existe"}), 409

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    user = {
        "nombre": nombre,
        "correo": correo,
        "password": hashed,
        "mbti": "",
        "favoritos": [],
        "historial": [],
        "creado": datetime.datetime.utcnow(),
    }
    res = db.usuarios.insert_one(user)
    return jsonify({"ok": True, "id": str(res.inserted_id),
                    "nombre": nombre, "correo": correo, "mbti": ""}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    correo = data.get("correo", "").strip().lower()
    password = data.get("password", "")

    user = db.usuarios.find_one({"correo": correo})
    if not user:
        return jsonify({"ok": False, "msg": "Datos incorrectos"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return jsonify({"ok": False, "msg": "Datos incorrectos"}), 401

    return jsonify({"ok": True, "id": str(user["_id"]),
                    "nombre": user["nombre"], "correo": user["correo"],
                    "mbti": user.get("mbti", "")})


# ---------------- MBTI ----------------
@app.route("/usuario/mbti", methods=["POST"])
def guardar_mbti():
    data = request.get_json()
    correo = data.get("correo", "").strip().lower()
    mbti = data.get("mbti", "").strip().upper()

    if len(mbti) != 4:
        return jsonify({"ok": False, "msg": "MBTI invalido"}), 400

    db.usuarios.update_one({"correo": correo}, {"$set": {"mbti": mbti}})
    return jsonify({"ok": True, "mbti": mbti})


# ---------------- CONTENIDO ----------------
@app.route("/contenido", methods=["GET"])
def contenido():
    """Filtra por tipo (?tipo=libro) y opcionalmente por mbti (?mbti=INFJ)."""
    tipo = request.args.get("tipo")
    mbti = request.args.get("mbti")

    query = {}
    if tipo:
        query["tipo"] = tipo
    if mbti:
        # Esto busca si el mbti del usuario está dentro del array de la BD
        query["mbti"] = {"$in": [mbti]}
    items = [doc_to_json(d) for d in db.contenido.find(query)]

    # Si no hay match por mbti, devuelve todo del tipo (fallback)
    if mbti and not items and tipo:
        items = [doc_to_json(d) for d in db.contenido.find({"tipo": tipo})]

    return jsonify({"ok": True, "total": len(items), "items": items})


@app.route("/contenido/<id>", methods=["GET"])
def contenido_detalle(id):
    try:
        d = db.contenido.find_one({"_id": ObjectId(id)})
    except Exception:
        return jsonify({"ok": False, "msg": "ID invalido"}), 400
    if not d:
        return jsonify({"ok": False, "msg": "No encontrado"}), 404
    return jsonify({"ok": True, "item": doc_to_json(d)})


# ---------------- FAVORITOS ----------------
@app.route("/favoritos", methods=["POST"])
def add_favorito():
    data = request.get_json()
    correo = data.get("correo", "").strip().lower()
    item = {"titulo": data.get("titulo"), "tipo": data.get("tipo"),
            "contenido_id": data.get("contenido_id")}
    db.usuarios.update_one({"correo": correo},
                           {"$addToSet": {"favoritos": item}})
    return jsonify({"ok": True})


@app.route("/favoritos", methods=["GET"])
def get_favoritos():
    correo = request.args.get("correo", "").strip().lower()
    user = db.usuarios.find_one({"correo": correo})
    favs = user.get("favoritos", []) if user else []
    return jsonify({"ok": True, "items": favs})


# ---------------- HISTORIAL ----------------
@app.route("/historial", methods=["POST"])
def add_historial():
    data = request.get_json()
    correo = data.get("correo", "").strip().lower()
    item = {"titulo": data.get("titulo"), "tipo": data.get("tipo"),
            "fecha": datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M")}
    db.usuarios.update_one({"correo": correo},
                           {"$push": {"historial": {"$each": [item], "$position": 0}}})
    return jsonify({"ok": True})


@app.route("/historial", methods=["GET"])
def get_historial():
    correo = request.args.get("correo", "").strip().lower()
    user = db.usuarios.find_one({"correo": correo})
    hist = user.get("historial", []) if user else []
    return jsonify({"ok": True, "items": hist})

# ---------------- SOCIAL ----------------
@app.route("/posts", methods=["POST"])
def crear_post():
    data = request.get_json()
    post = {"correo": data.get("correo"), "nombre": data.get("nombre"),
            "texto": data.get("texto"), "likes": 0, "likes_por": [],
            "comentarios": [], "fecha": datetime.datetime.utcnow()}
    res = db.posts.insert_one(post)
    return jsonify({"ok": True, "id": str(res.inserted_id)})


@app.route("/posts", methods=["GET"])
def get_posts():
    posts = [doc_to_json(p) for p in db.posts.find().sort("fecha", -1).limit(50)]
    for p in posts:
        if "fecha" in p:
            p["fecha"] = p["fecha"].strftime("%d/%m/%Y %H:%M") \
                if hasattr(p["fecha"], "strftime") else str(p["fecha"])
        p["num_comentarios"] = len(p.get("comentarios", []))
    return jsonify({"ok": True, "items": posts})


@app.route("/posts/like", methods=["POST"])
def like_post():
    data = request.get_json()
    post_id = data.get("post_id")
    correo = data.get("correo")
    try:
        post = db.posts.find_one({"_id": ObjectId(post_id)})
    except Exception:
        return jsonify({"ok": False, "msg": "ID invalido"}), 400
    if not post:
        return jsonify({"ok": False}), 404

    if correo in post.get("likes_por", []):
        db.posts.update_one({"_id": ObjectId(post_id)},
                            {"$pull": {"likes_por": correo}, "$inc": {"likes": -1}})
        liked = False
    else:
        db.posts.update_one({"_id": ObjectId(post_id)},
                            {"$addToSet": {"likes_por": correo}, "$inc": {"likes": 1}})
        liked = True
    p = db.posts.find_one({"_id": ObjectId(post_id)})
    return jsonify({"ok": True, "liked": liked, "likes": p.get("likes", 0)})


@app.route("/posts/comentar", methods=["POST"])
def comentar():
    data = request.get_json()
    post_id = data.get("post_id")
    comentario = {"nombre": data.get("nombre"), "texto": data.get("texto"),
                  "fecha": datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M")}
    try:
        db.posts.update_one({"_id": ObjectId(post_id)},
                            {"$push": {"comentarios": comentario}})
    except Exception:
        return jsonify({"ok": False, "msg": "ID invalido"}), 400
    return jsonify({"ok": True})


@app.route("/posts/<post_id>/comentarios", methods=["GET"])
def get_comentarios(post_id):
    try:
        p = db.posts.find_one({"_id": ObjectId(post_id)})
    except Exception:
        return jsonify({"ok": False}), 400
    if not p:
        return jsonify({"ok": False}), 404
    return jsonify({"ok": True, "items": p.get("comentarios", [])})

# ── ARRANQUE ──────────────────────────────────────────────

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
