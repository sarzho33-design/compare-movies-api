"""
compare_movies - Mini API que compara dos películas usando TMDB.

Endpoint principal:
    GET /compare_movies?title1=...&title2=...

Ejemplo:
    /compare_movies?title1=Inception&title2=Interstellar
"""

from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Pega aquí tu API key de TMDB (o usa una variable de entorno)
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"


def buscar_pelicula(titulo):
    """Busca una película por título y devuelve su info básica (primer resultado)."""
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": titulo, "language": "es-ES"}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("results"):
        return None

    return data["results"][0]


def obtener_detalles(movie_id):
    """Obtiene detalles completos de una película (incluye reparto vía append_to_response)."""
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "es-ES",
        "append_to_response": "credits",
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


def extraer_info(pelicula_detalle):
    """Extrae los campos relevantes de un JSON anidado de TMDB."""
    generos = [g["name"] for g in pelicula_detalle.get("genres", [])]

    reparto = []
    credits = pelicula_detalle.get("credits", {})
    for actor in credits.get("cast", [])[:5]:  # top 5 actores
        reparto.append(actor.get("name"))

    return {
        "titulo": pelicula_detalle.get("title"),
        "anio": (pelicula_detalle.get("release_date") or "")[:4],
        "puntuacion": pelicula_detalle.get("vote_average"),
        "duracion": pelicula_detalle.get("runtime"),  # minutos
        "generos": generos,
        "reparto": reparto,
        "sinopsis": pelicula_detalle.get("overview"),
    }


def generar_html(info1, info2):
    """Genera HTML dinámico comparando dos películas."""

    def fila_comparativa(etiqueta, valor1, valor2, mejor=None):
        clase1 = "mejor" if mejor == 1 else ""
        clase2 = "mejor" if mejor == 2 else ""
        return f"""
        <tr>
            <td class="etiqueta">{etiqueta}</td>
            <td class="{clase1}">{valor1}</td>
            <td class="{clase2}">{valor2}</td>
        </tr>
        """

    # Determinar "ganador" en puntuación y duración
    mejor_puntuacion = None
    if info1["puntuacion"] is not None and info2["puntuacion"] is not None:
        if info1["puntuacion"] > info2["puntuacion"]:
            mejor_puntuacion = 1
        elif info2["puntuacion"] > info1["puntuacion"]:
            mejor_puntuacion = 2

    filas = ""
    filas += fila_comparativa("Año", info1["anio"], info2["anio"])
    filas += fila_comparativa(
        "Puntuación", info1["puntuacion"], info2["puntuacion"], mejor_puntuacion
    )
    filas += fila_comparativa(
        "Duración (min)", info1["duracion"], info2["duracion"]
    )
    filas += fila_comparativa(
        "Géneros", ", ".join(info1["generos"]), ", ".join(info2["generos"])
    )
    filas += fila_comparativa(
        "Reparto principal", ", ".join(info1["reparto"]), ", ".join(info2["reparto"])
    )

    html = f"""
    <html>
    <head>
        <title>Comparativa: {info1['titulo']} vs {info2['titulo']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f4f4f9; }}
            h1 {{ text-align: center; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; background: white; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
            th {{ background-color: #4a4a8a; color: white; }}
            .etiqueta {{ font-weight: bold; background: #eee; text-align: left; }}
            .mejor {{ background-color: #c8f7c5; font-weight: bold; }}
            .sinopsis {{ margin-top: 30px; }}
            .sinopsis h3 {{ color: #4a4a8a; }}
        </style>
    </head>
    <body>
        <h1>{info1['titulo']} vs {info2['titulo']}</h1>
        <table>
            <tr>
                <th>Comparativa</th>
                <th>{info1['titulo']}</th>
                <th>{info2['titulo']}</th>
            </tr>
            {filas}
        </table>

        <div class="sinopsis">
            <h3>Sinopsis - {info1['titulo']}</h3>
            <p>{info1['sinopsis']}</p>
            <h3>Sinopsis - {info2['titulo']}</h3>
            <p>{info2['sinopsis']}</p>
        </div>
    </body>
    </html>
    """
    return html


@app.route("/compare_movies")
def compare_movies():
    title1 = request.args.get("title1")
    title2 = request.args.get("title2")

    # --- Gestión de errores: parámetros faltantes ---
    if not title1 or not title2:
        return (
            "<h2>Error: faltan parámetros</h2>"
            "<p>Usa /compare_movies?title1=...&title2=...</p>",
            400,
        )

    # --- Buscar ambas películas ---
    resultado1 = buscar_pelicula(title1)
    resultado2 = buscar_pelicula(title2)

    if not resultado1:
        return f"<h2>Error: no se encontró la película '{title1}'</h2>", 404
    if not resultado2:
        return f"<h2>Error: no se encontró la película '{title2}'</h2>", 404

    # --- Obtener detalles completos (JSON anidado: credits, genres...) ---
    detalle1 = obtener_detalles(resultado1["id"])
    detalle2 = obtener_detalles(resultado2["id"])

    # --- Extraer info relevante ---
    info1 = extraer_info(detalle1)
    info2 = extraer_info(detalle2)

    # --- Generar HTML dinámico ---
    return generar_html(info1, info2)


@app.route("/")
def home():
    return """
    <h1>Compare Movies API</h1>
    <p>Prueba: <a href="/compare_movies?title1=Inception&title2=Interstellar">
    /compare_movies?title1=Inception&title2=Interstellar</a></p>
    """


if __name__ == "__main__":
    app.run(debug=True, port=5000)