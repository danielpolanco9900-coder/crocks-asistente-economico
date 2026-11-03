# crocks_streamlit.py
import os
import json
import time
from datetime import date
from pathlib import Path

import requests  # pyright: ignore[reportMissingModuleSource]
import streamlit as st  # pyright: ignore[reportMissingImports]

# Cargar .env en desarrollo local. En Streamlit Cloud usa Secrets.
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)
except ImportError:
    pass

# Debe ejecutarse antes de cualquier otro elemento de Streamlit.
st.set_page_config(page_title="CROCKS", page_icon="📊", layout="centered")


def obtener_secreto(nombre, default=""):
    """Lee primero Streamlit Secrets y, si no existe, una variable de entorno."""
    try:
        valor = st.secrets.get(nombre, None)
        if valor:
            return str(valor).strip()
    except Exception:
        pass
    return (os.getenv(nombre) or default).strip()


try:
    from supabase import create_client
    SUPABASE_DISPONIBLE = True
except ImportError:
    create_client = None
    SUPABASE_DISPONIBLE = False


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Los modelos "compound" de Groq son los que hacen búsqueda web.
MODELOS_WEB = ["groq/compound", "groq/compound-mini"]
MODELOS_SIN_WEB = ["openai/gpt-oss-20b"]
ARCHIVO_MEMORIA = Path(__file__).resolve().with_name("crocks_recuerdos.json")

TABLA_CONVERSACIONES = "conversaciones_crocks"
TABLA_RECUERDOS = "recuerdos_crocks"


# ---------------------- SUPABASE ----------------------

@st.cache_resource
def _crear_cliente_supabase(url, key):
    # Si lanza excepción, Streamlit NO cachea el fallo y reintenta en la siguiente ejecución.
    return create_client(url, key)


def init_supabase():
    """Devuelve (cliente, error). Nunca imprime la clave."""
    if not SUPABASE_DISPONIBLE:
        return None, "Falta instalar el paquete 'supabase' (agrégalo a requirements.txt)."

    # Limpia comillas, espacios y rutas sobrantes (/rest/v1) de la URL.
    url = obtener_secreto("SUPABASE_URL").strip().strip('"').strip("'").rstrip("/")
    for sufijo in ("/rest/v1", "/rest"):
        if url.endswith(sufijo):
            url = url[: -len(sufijo)].rstrip("/")

    key = obtener_secreto("SUPABASE_KEY").strip().strip('"').strip("'")

    if not url or not key:
        return None, "Faltan SUPABASE_URL o SUPABASE_KEY en Secrets."

    try:
        return _crear_cliente_supabase(url, key), None
    except Exception as error:
        return None, f"No se pudo crear el cliente: {error}"


supabase, error_supabase = init_supabase()


def guardar_en_supabase(pregunta, respuesta):
    if supabase is None:
        return False, error_supabase or "Supabase no conectado"

    try:
        supabase.table(TABLA_CONVERSACIONES).insert(
            {"pregunta": str(pregunta), "respuesta": str(respuesta)}
        ).execute()
        return True, None
    except Exception as error:
        print(f"❌ ERROR SUPABASE (conversaciones): {error}")
        return False, str(error)


def cargar_recuerdos_supabase():
    if supabase is None:
        return None
    try:
        filas = supabase.table(TABLA_RECUERDOS).select("nombre, info").execute().data
        return {fila["nombre"]: fila["info"] for fila in filas}
    except Exception as error:
        print(f"❌ ERROR SUPABASE (leer recuerdos): {error}")
        return None


def guardar_recuerdo_supabase(nombre, info):
    if supabase is None:
        return False
    try:
        supabase.table(TABLA_RECUERDOS).upsert(
            {"nombre": nombre, "info": info}, on_conflict="nombre"
        ).execute()
        return True
    except Exception as error:
        print(f"❌ ERROR SUPABASE (guardar recuerdo): {error}")
        return False


def borrar_recuerdo_supabase(nombre):
    if supabase is None:
        return False
    try:
        supabase.table(TABLA_RECUERDOS).delete().eq("nombre", nombre).execute()
        return True
    except Exception as error:
        print(f"❌ ERROR SUPABASE (borrar recuerdo): {error}")
        return False


# ---------------------- MEMORIA LOCAL (respaldo) ----------------------

def cargar_recuerdos_local():
    try:
        if ARCHIVO_MEMORIA.exists():
            datos = json.loads(ARCHIVO_MEMORIA.read_text(encoding="utf-8"))
            return datos if isinstance(datos, dict) else {}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def guardar_recuerdos_local(recuerdos):
    try:
        ARCHIVO_MEMORIA.write_text(
            json.dumps(recuerdos, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True
    except OSError as error:
        st.sidebar.error(f"No se pudo guardar la memoria local: {error}")
        return False


def cargar_recuerdos():
    """Supabase es la fuente principal; el archivo local es respaldo."""
    remotos = cargar_recuerdos_supabase()
    if remotos is not None:
        return remotos
    return cargar_recuerdos_local()


# ---------------------- GROQ ----------------------

def sistema(recuerdos):
    texto = (
        "Eres CROCKS, un asistente de economía y cultura general. "
        f"La fecha de hoy es {date.today().strftime('%d/%m/%Y')}. "
        "Responde SIEMPRE en español, de forma clara y fácil de entender. "
        "Si la pregunta es académica, explica primero de forma sencilla y luego "
        "con detalle técnico si hace falta. Para cálculos: muestra la fórmula, "
        "sustituye los valores, da el resultado y explica qué significa. "
        "No inventes datos, cifras, fechas ni fuentes; si no estás seguro, dilo. "
        "Para datos actuales, indica la fecha y la fuente cuando estén disponibles, "
        "y prioriza fuentes oficiales como Banguat, INE, FMI y Banco Mundial. "
        "Sé breve salvo que pidan más detalle."
    )

    if recuerdos:
        texto += "\n\nDatos que el usuario pidió recordar:\n" + "\n".join(
            f"- {clave}: {valor}" for clave, valor in recuerdos.items()
        )

    return texto


def llamar_groq(api_key, modelo, mensajes, usar_busqueda):
    payload = {
        "model": modelo,
        "messages": mensajes,
        "temperature": 0.5,
    }

    if not usar_busqueda:
        payload["max_tokens"] = 1500

    ultimo_error = "Error desconocido."

    for intento in range(3):
        try:
            respuesta = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120,
            )
        except requests.Timeout:
            ultimo_error = "Groq tardó demasiado en responder."
            continue
        except requests.RequestException as error:
            ultimo_error = f"Error de conexión: {error}"
            time.sleep(2)
            continue

        if respuesta.status_code == 200:
            try:
                contenido = respuesta.json()["choices"][0]["message"].get("content")
            except (KeyError, IndexError, TypeError, ValueError):
                return None, "Groq devolvió una respuesta con formato inesperado."

            if isinstance(contenido, str) and contenido.strip():
                return contenido.strip(), None
            return None, "Groq devolvió una respuesta vacía."

        if respuesta.status_code == 401:
            return None, "CLAVE_INVALIDA"

        if respuesta.status_code in (429, 500, 502, 503, 504):
            ultimo_error = f"Groq no está disponible temporalmente ({respuesta.status_code})."
            time.sleep(2 * (intento + 1))
            continue

        try:
            detalle = respuesta.json().get("error", {}).get("message", respuesta.text)
        except (ValueError, AttributeError):
            detalle = respuesta.text

        return None, f"Error {respuesta.status_code}: {str(detalle)[:300]}"

    return None, ultimo_error


def responder(pregunta, historial, recuerdos, usar_web):
    api_key = obtener_secreto("GROQ_API_KEY")
    if not api_key:
        return "❌ No se encontró GROQ_API_KEY. Configúrala en Secrets.", False

    mensajes = (
        [{"role": "system", "content": sistema(recuerdos)}]
        + historial[-8:]
        + [{"role": "user", "content": pregunta}]
    )

    intentos = []
    if usar_web:
        intentos.extend((modelo, True) for modelo in MODELOS_WEB)
    intentos.extend((modelo, False) for modelo in MODELOS_SIN_WEB)

    errores = []
    for modelo, es_modelo_web in intentos:
        contenido, error = llamar_groq(api_key, modelo, mensajes, es_modelo_web)

        if error and error.startswith("Error 413"):
            mensajes_cortos = [mensajes[0], mensajes[-1]]
            contenido, error = llamar_groq(api_key, modelo, mensajes_cortos, es_modelo_web)

        if contenido:
            return contenido, es_modelo_web

        if error == "CLAVE_INVALIDA":
            return (
                "❌ La clave de Groq no es válida. Genera una nueva en "
                "https://console.groq.com/keys y actualiza tus Secrets.",
                False,
            )

        if error:
            errores.append(f"{modelo}: {error}")
            print(f"⚠️ Falló {modelo}: {error}")

    detalle = errores[-1] if errores else "No hubo respuesta de los modelos."
    return f"❌ No pude obtener una respuesta. Detalle: {detalle}", False


# ---------------------- ESTILOS ----------------------

st.markdown(
    """
    <style>
    .stApp { background-color: #111827; color: #F9FAFB; }
    section[data-testid="stSidebar"] {
        background-color: #0B1220;
        border-right: 1px solid #273449;
    }
    h1, h2, h3, p, label, li, span { color: #F9FAFB; }
    div[data-testid="stChatMessage"] {
        background-color: #1F2937;
        border: 1px solid #374151;
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 10px;
    }
    .stTextInput input, .stTextArea textarea, .stChatInput textarea {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border: 1px solid #475569 !important;
    }
    div.stButton > button, .stFormSubmitButton button,
    div.stDownloadButton > button {
        background-color: #2563EB; color: #FFFFFF;
        border: none; border-radius: 9px;
    }
    div.stButton > button:hover, .stFormSubmitButton button:hover {
        background-color: #1D4ED8; color: #FFFFFF;
    }
    .encabezado {
        background: linear-gradient(135deg, #1E3A8A, #1F2937);
        border: 1px solid #374151;
        border-radius: 16px;
        padding: 22px 26px;
        margin-bottom: 18px;
    }
    .encabezado h1 { margin: 0 0 4px 0; color: #FFFFFF; font-size: 1.9rem; }
    .encabezado p { margin: 0; color: #CBD5E1; }
    a { color: #60A5FA; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------- ESTADO DE LA APP ----------------------

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

if "recuerdos" not in st.session_state:
    st.session_state.recuerdos = cargar_recuerdos()


# ---------------------- BARRA LATERAL ----------------------

with st.sidebar:
    st.title("📊 CROCKS")
    st.caption("Asistente económico con IA")

    usar_web = st.toggle("🌐 Buscar datos actuales en la web", value=True)

    if st.button("＋ Nueva conversación", use_container_width=True):
        st.session_state.mensajes = []
        st.rerun()

    st.divider()
    st.subheader("🧠 Memoria")

    recuerdos = st.session_state.recuerdos

    with st.form("form_memoria", clear_on_submit=True):
        nombre = st.text_input("Nombre", placeholder="Ej. Mi proyecto")
        info = st.text_area("Qué debe recordar", placeholder="Escribe aquí...", height=90)

        if st.form_submit_button("Guardar", use_container_width=True):
            if nombre.strip() and info.strip():
                recuerdos[nombre.strip()] = info.strip()
                en_nube = guardar_recuerdo_supabase(nombre.strip(), info.strip())
                en_local = guardar_recuerdos_local(recuerdos)
                if en_nube or en_local:
                    st.session_state.recuerdos = recuerdos
                    st.success("Recuerdo guardado." if en_nube else "Guardado solo localmente.")
                    st.rerun()
            else:
                st.warning("Completa ambos campos.")

    with st.expander(f"Ver recuerdos ({len(recuerdos)})"):
        if not recuerdos:
            st.caption("Todavía no hay recuerdos.")

        for clave, valor in list(recuerdos.items()):
            st.markdown(f"**{clave}**")
            st.write(valor)

            if st.button("Eliminar", key=f"eliminar_{clave}"):
                recuerdos.pop(clave, None)
                borrar_recuerdo_supabase(clave)
                guardar_recuerdos_local(recuerdos)
                st.session_state.recuerdos = recuerdos
                st.rerun()

    st.divider()

    if obtener_secreto("GROQ_API_KEY"):
        st.success("Clave de Groq detectada")
    else:
        st.error("Falta GROQ_API_KEY")

    if supabase:
        st.success("✅ Supabase conectado")
        if st.button("🧪 Probar escritura en Supabase", use_container_width=True):
            ok, err = guardar_en_supabase("[prueba]", "[prueba de conexión]")
            if ok:
                st.success("Se guardó una fila de prueba.")
            else:
                st.error(f"Falló: {err}")
    else:
        st.error(f"❌ Supabase no conectado: {error_supabase}")

    st.caption("Powered by Groq")


# ---------------------- ENCABEZADO ----------------------

st.markdown(
    """
    <div class="encabezado">
        <h1>Centro de análisis económico</h1>
        <p>Pregunta sobre economía, finanzas, estadística o actualidad.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------- CHAT ----------------------

if not st.session_state.mensajes:
    with st.chat_message("assistant"):
        st.markdown(
            "¡Hola! Soy **CROCKS** 👋\n\n"
            "Puedo explicarte conceptos de economía, hacer cálculos y ayudarte "
            "a investigar datos actuales como inflación, tipo de cambio o petróleo.\n\n"
            "**¿Qué te gustaría consultar?**"
        )

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])


pregunta = st.chat_input("Escribe tu pregunta aquí...")

if pregunta:
    st.session_state.mensajes.append({"role": "user", "content": pregunta})

    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("CROCKS está pensando..."):
            texto, uso_web = responder(
                pregunta,
                st.session_state.mensajes[:-1],
                st.session_state.recuerdos,
                usar_web,
            )

        st.markdown(texto)

        if usar_web and not uso_web and not texto.startswith("❌"):
            st.caption(
                "⚠️ Esta respuesta se generó sin búsqueda web; "
                "los datos actuales podrían no estar actualizados."
            )

    st.session_state.mensajes.append({"role": "assistant", "content": texto})

    if not texto.startswith("❌"):
        guardado, error_guardado = guardar_en_supabase(pregunta, texto)
        if guardado:
            st.toast("Conversación guardada en Supabase", icon="✅")
        else:
            st.warning(
                "La respuesta se generó, pero no se pudo guardar en Supabase: "
                f"{error_guardado}"
            )


# ---------------------- DESCARGA DEL HISTORIAL ----------------------

if st.session_state.mensajes:
    transcripcion = "\n\n".join(
        ("TÚ" if m["role"] == "user" else "CROCKS") + ":\n" + m["content"]
        for m in st.session_state.mensajes
    )

    st.download_button(
        "Descargar conversación",
        data=transcripcion,
        file_name="conversacion_crocks.txt",
        mime="text/plain",
    )