# crocks_app.py
# CROCKS: asistente económico con interfaz web (Streamlit + Groq)
#
# Instalar (una sola vez):   pip install streamlit requests python-dotenv
# Clave de Groq:             $env:GROQ_API_KEY="gsk_tu_clave"   (o en un archivo .env)
# Ejecutar:                  streamlit run crocks_app.py

import json
import os
import time
from datetime import date
from pathlib import Path

import requests
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

URL = "https://api.groq.com/openai/v1/chat/completions"
MODELOS_WEB = ["groq/compound-mini", "groq/compound"]
MODELOS_SIN_WEB = ["llama-3.3-70b-versatile", "openai/gpt-oss-20b"]
ARCHIVO_MEMORIA = Path(__file__).with_name("crocks_recuerdos.json")

st.set_page_config(page_title="CROCKS", page_icon="📊", layout="centered")


# ------------------------------------------------------------
# Memoria permanente (archivo JSON sencillo)
# ------------------------------------------------------------
def cargar_recuerdos():
    try:
        return json.loads(ARCHIVO_MEMORIA.read_text(encoding="utf-8"))
    except Exception:
        return {}


def guardar_recuerdos(recuerdos):
    try:
        ARCHIVO_MEMORIA.write_text(
            json.dumps(recuerdos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        st.sidebar.error(f"No se pudo guardar: {e}")


# ------------------------------------------------------------
# Conexión con Groq (con respaldo para que no falle)
# ------------------------------------------------------------
def sistema(recuerdos):
    texto = (
        f"Eres CROCKS, un asistente de economía y de cultura general. "
        f"La fecha de hoy es {date.today().strftime('%d/%m/%Y')}. "
        "Responde SIEMPRE en español, de forma clara y fácil de entender. "
        "Si la pregunta es académica, explica primero de forma sencilla y luego con "
        "detalle técnico si hace falta. Para cálculos: muestra la fórmula, sustituye "
        "los valores, da el resultado y explica qué significa. "
        "No inventes datos, cifras, fechas ni fuentes; si no estás seguro, dilo. "
        "Para datos actuales (inflación, PIB, IMAE, tasas, tipo de cambio, petróleo, "
        "oro, bitcoin, mercados) busca en la web, indica la fecha y la fuente, y "
        "prioriza fuentes oficiales (Banguat, INE, FMI, Banco Mundial, Reserva "
        "Federal, BLS). Sé breve salvo que pidan más detalle."
    )
    if recuerdos:
        texto += "\n\nDatos que el usuario pidió recordar:\n" + "\n".join(
            f"- {k}: {v}" for k, v in recuerdos.items()
        )
    return texto


def llamar(api_key, modelo, mensajes, web):
    payload = {"model": modelo, "messages": mensajes}
    if web:
        payload["search_settings"] = {"exclude_domains": ["wikipedia.org"]}
    else:
        payload["max_tokens"] = 1500

    error = "Error desconocido"
    for intento in range(3):
        try:
            r = requests.post(
                URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=120,
            )
        except requests.Timeout:
            error = "Groq tardó demasiado."
            continue
        except requests.RequestException as e:
            error = f"Error de conexión: {e}"
            time.sleep(2)
            continue

        if r.status_code == 200:
            try:
                texto = r.json()["choices"][0]["message"].get("content")
            except Exception:
                return None, "Formato inesperado."
            if texto and texto.strip():
                return texto.strip(), None
            return None, "Respuesta vacía."
        if r.status_code == 401:
            return None, "CLAVE_INVALIDA"
        if r.status_code in (429, 500, 502, 503, 504):
            error = f"Groq saturado ({r.status_code})."
            time.sleep(3 * (intento + 1))
            continue
        try:
            detalle = r.json().get("error", {}).get("message", r.text)
        except Exception:
            detalle = r.text
        return None, f"Código {r.status_code}: {str(detalle)[:200]}"
    return None, error


def responder(pregunta, historial, recuerdos, usar_web):
    """Devuelve (texto, usó_web). Nunca lanza excepciones."""
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        return ("❌ No encontré la GROQ_API_KEY. Configúrala y reinicia la app.", False)

    mensajes = (
        [{"role": "system", "content": sistema(recuerdos)}]
        + historial[-8:]
        + [{"role": "user", "content": pregunta}]
    )
    solos = [mensajes[0], mensajes[-1]]

    intentos = ([(m, True) for m in MODELOS_WEB] if usar_web else []) + [
        (m, False) for m in MODELOS_SIN_WEB
    ]
    for modelo, web in intentos:
        texto, error = llamar(api_key, modelo, mensajes, web)
        if error and error.startswith("Código 413"):
            texto, error = llamar(api_key, modelo, solos, web)
        if texto:
            return texto, web
        if error == "CLAVE_INVALIDA":
            return (
                "❌ Tu GROQ_API_KEY no es válida. Crea una nueva en "
                "https://console.groq.com/keys",
                False,
            )
    return "❌ No pude obtener respuesta ahora. Intenta de nuevo en un minuto.", False


# ------------------------------------------------------------
# Estilo (oscuro y sencillo)
# ------------------------------------------------------------
st.markdown(
    """
<style>
.stApp { background-color: #111827; color: #F9FAFB; }
section[data-testid="stSidebar"] { background-color: #0B1220; border-right: 1px solid #273449; }
h1, h2, h3, p, label, li, span { color: #F9FAFB; }
div[data-testid="stChatMessage"] {
    background-color: #1F2937; border: 1px solid #374151;
    border-radius: 14px; padding: 1rem; margin-bottom: 10px;
}
.stTextInput input, .stTextArea textarea, .stChatInput textarea {
    background-color: #1F2937 !important; color: #FFFFFF !important;
    border: 1px solid #475569 !important;
}
div.stButton > button, .stFormSubmitButton button, div.stDownloadButton > button {
    background-color: #2563EB; color: #FFFFFF; border: none; border-radius: 9px;
}
div.stButton > button:hover, .stFormSubmitButton button:hover { background-color: #1D4ED8; color: #FFFFFF; }
.encabezado {
    background: linear-gradient(135deg, #1E3A8A, #1F2937);
    border: 1px solid #374151; border-radius: 16px;
    padding: 22px 26px; margin-bottom: 18px;
}
.encabezado h1 { margin: 0 0 4px 0; color: #FFFFFF; font-size: 1.9rem; }
.encabezado p { margin: 0; color: #CBD5E1; }
a { color: #60A5FA; }
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Estado
# ------------------------------------------------------------
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# ------------------------------------------------------------
# Barra lateral
# ------------------------------------------------------------
with st.sidebar:
    st.title("📊 CROCKS")
    st.caption("Asistente económico con IA")

    usar_web = st.toggle("🌐 Buscar datos actuales en la web", value=True)

    if st.button("＋ Nueva conversación", use_container_width=True):
        st.session_state.mensajes = []
        st.rerun()

    st.divider()
    st.subheader("🧠 Memoria")
    recuerdos = cargar_recuerdos()

    with st.form("form_memoria", clear_on_submit=True):
        nombre = st.text_input("Nombre", placeholder="Ej. Mi proyecto")
        info = st.text_area("Qué debe recordar", placeholder="Escribe aquí...", height=90)
        if st.form_submit_button("Guardar", use_container_width=True):
            if nombre.strip() and info.strip():
                recuerdos[nombre.strip()] = info.strip()
                guardar_recuerdos(recuerdos)
                st.rerun()
            else:
                st.warning("Completa ambos campos.")

    with st.expander(f"Ver recuerdos ({len(recuerdos)})"):
        if not recuerdos:
            st.caption("Todavía no hay recuerdos.")
        for k, v in list(recuerdos.items()):
            st.markdown(f"**{k}**")
            st.write(v)
            if st.button("Eliminar", key=f"del_{k}"):
                recuerdos.pop(k, None)
                guardar_recuerdos(recuerdos)
                st.rerun()

    st.divider()
    if (os.getenv("GROQ_API_KEY") or "").strip():
        st.success("Clave de Groq detectada")
    else:
        st.error("Falta GROQ_API_KEY")
    st.caption("Powered by Groq")

# ------------------------------------------------------------
# Encabezado y conversación
# ------------------------------------------------------------
st.markdown(
    """
<div class="encabezado">
    <h1>Centro de análisis económico</h1>
    <p>Pregunta sobre economía, finanzas, estadística o actualidad.</p>
</div>
""",
    unsafe_allow_html=True,
)

if not st.session_state.mensajes:
    with st.chat_message("assistant"):
        st.markdown(
            "¡Hola! Soy **CROCKS** 👋\n\n"
            "Puedo explicarte conceptos de economía, hacer cálculos y buscar "
            "datos actuales como inflación, tipo de cambio o petróleo.\n\n"
            "**¿Qué te gustaría consultar?**"
        )

for m in st.session_state.mensajes:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

pregunta = st.chat_input("Escribe tu pregunta aquí...")

if pregunta:
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("CROCKS está pensando..."):
            texto, uso_web = responder(
                pregunta, st.session_state.mensajes, recuerdos, usar_web
            )
        st.markdown(texto)
        if usar_web and not uso_web and not texto.startswith("❌"):
            st.caption("⚠️ Respuesta sin búsqueda web: los datos actuales pueden no ser exactos.")

    if not texto.startswith("❌"):
        st.session_state.mensajes.append({"role": "user", "content": pregunta})
        st.session_state.mensajes.append({"role": "assistant", "content": texto})

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