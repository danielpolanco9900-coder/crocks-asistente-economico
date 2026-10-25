# CROCKS.py
# Asistente Económico con IA
# Groq + Compound Mini + APIs

import os
import requests
import time


class IntermediateTools:

    def __init__(self):
        # ======================================================
        # CONFIGURACIÓN GROQ
        # ======================================================
        self.api_key = os.getenv("GROQ_API_KEY")

        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    # ==========================================================
    # CEREBRO DE CROCKS
    # ==========================================================

    def responder_consulta(self, pregunta, buscar_web=False):

        if not self.api_key:
            return """
❌ ERROR

No se encontró GROQ_API_KEY.

En PowerShell ejecuta:

$env:GROQ_API_KEY="TU_API_KEY"

Después vuelve a ejecutar:

python .\\Crocks.py
"""

        # ------------------------------------------------------
        # MODELO
        # ------------------------------------------------------
        if buscar_web:
            modelo = "groq/compound-mini"
        else:
            modelo = "openai/gpt-oss-120b"

        # ------------------------------------------------------
        # PROMPT
        # ------------------------------------------------------
        sistema = """
Eres CROCKS, un asistente económico y general.

Responde SIEMPRE en español.

Especialidad:
- Economía
- Macroeconomía
- Microeconomía
- Economía de Guatemala
- Economía internacional
- Inflación
- PIB
- IMAE
- Política monetaria
- Política fiscal
- Finanzas
- Econometría
- Estadística
- Mercados financieros

También puedes responder preguntas generales.

REGLAS:
1. Sé claro y fácil de entender.
2. No inventes datos.
3. Si la pregunta es académica, explica primero de forma sencilla.
4. Después puedes dar una explicación técnica.
5. Si utilizas información actual, indica la fecha.
6. Si utilizas una fuente externa, indícala.
7. No hagas respuestas innecesariamente largas.
"""

        payload = {
            "model": modelo,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": pregunta}
            ],
            "max_completion_tokens": 600
        }

        # ======================================================
        # BÚSQUEDA WEB
        # ======================================================
        # Compound Mini ya utiliza web search.
        # NO agregamos compound_custom manualmente.
        # Esto evita errores de configuración.
        if buscar_web:
            payload["search_settings"] = {
                "exclude_domains": ["wikipedia.org"]
            }

        # ======================================================
        # SOLICITUD
        # ======================================================
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=120
            )

            if response.status_code == 401:
                return """
❌ API KEY INVÁLIDA.

Tu GROQ_API_KEY no está siendo aceptada.

Crea una nueva API key en Groq y vuelve a configurar:

$env:GROQ_API_KEY="TU_NUEVA_API_KEY"
"""

            if response.status_code == 404:
                return (
                    "\n❌ MODELO NO DISPONIBLE\n\n"
                    f"Modelo utilizado: {modelo}\n\n"
                    "Groq no permitió utilizar este modelo."
                )

            if response.status_code == 413:
                return """
⚠️ GROQ RECHAZÓ LA SOLICITUD POR TAMAÑO.

La búsqueda produjo demasiada información.

Intenta nuevamente.
"""

            if response.status_code == 429:
                return """
⏳ LÍMITE DE GROQ ALCANZADO.

Tu cuenta llegó temporalmente al límite de solicitudes.

Espera unos segundos y vuelve a intentarlo.
"""

            if response.status_code != 200:
                return (
                    "\n❌ ERROR DE GROQ API\n\n"
                    f"Código: {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            try:
                return data["choices"][0]["message"]["content"]
            except Exception:
                return (
                    "\n⚠️ Groq respondió, pero "
                    "el formato fue inesperado.\n\n"
                    f"{data}"
                )

        except requests.Timeout:
            return """
⏱️ GROQ TARDÓ DEMASIADO.

Intenta nuevamente.
"""

        except requests.RequestException as e:
            return f"\n❌ ERROR DE CONEXIÓN\n\n{e}"

        except Exception as e:
            return f"\n❌ ERROR INESPERADO\n\n{e}"

    # ==========================================================
    # 1. TIPO DE CAMBIO USD → GTQ
    # ==========================================================

    def obtener_tipo_cambio(self):
        # ------------------------------------------------------
        # IMPORTANTE:
        # Esta función NO utiliza Groq.
        #
        # Usamos el endpoint /v2/rate/{base}/{quote} de Frankfurter,
        # que devuelve un objeto plano:
        #   {"date": "...", "base": "USD", "quote": "GTQ", "rate": 7.63}
        # (el endpoint /v2/rates devuelve otra forma de datos y NO
        # es una lista indexable con data[0], como estaba antes).
        # ------------------------------------------------------
        url = "https://api.frankfurter.dev/v2/rate/USD/GTQ"

        try:
            response = requests.get(url, timeout=30)

            if response.status_code == 422 or response.status_code == 404:
                return (
                    "\n❌ No se pudo obtener el tipo de cambio.\n\n"
                    "El par USD/GTQ no está disponible en este momento "
                    "en la fuente de datos."
                )

            response.raise_for_status()

            data = response.json()

            if "rate" not in data:
                return "\n❌ No se recibió información del tipo de cambio."

            tasa = data["rate"]
            fecha = data["date"]

            return (
                "\n💱 TIPO DE CAMBIO\n\n"
                "USD → GTQ\n\n"
                f"1 USD = {tasa:.4f} GTQ\n"
                f"Fecha: {fecha}\n\n"
                "Fuente: Frankfurter"
            )

        except requests.RequestException as e:
            return f"\n❌ No se pudo obtener el tipo de cambio.\n\n{e}"

        except Exception as e:
            return f"\n❌ Error procesando el tipo de cambio.\n\n{e}"

    # ==========================================================
    # 2. BITCOIN
    # ==========================================================

    def obtener_bitcoin(self):
        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin&vs_currencies=usd"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            precio = data["bitcoin"]["usd"]

            return (
                "\n₿ BITCOIN\n\n"
                f"Precio: ${precio:,.2f} USD\n\n"
                "Fuente: CoinGecko"
            )

        except Exception as e:
            return f"\n❌ Error obteniendo Bitcoin:\n{e}"

    # ==========================================================
    # 3. PETRÓLEO
    # ==========================================================

    def obtener_petroleo(self):
        pregunta = """
Busca en la web el precio MÁS RECIENTE del petróleo.

Responde solamente:

WTI:
Brent:
Fecha:
Fuente:

No inventes datos.
Sé muy breve.
"""
        return self.responder_consulta(pregunta, buscar_web=True)

    # ==========================================================
    # 4. ORO
    # ==========================================================

    def obtener_oro(self):
        pregunta = """
Busca en la web el precio MÁS RECIENTE del oro.

Responde solamente:

Precio por onza troy:
Fecha:
Fuente:

No inventes datos.
Sé muy breve.
"""
        return self.responder_consulta(pregunta, buscar_web=True)

    # ==========================================================
    # 5. ECONOMÍA DE GUATEMALA
    # ==========================================================

    def economia_guatemala(self):
        pregunta = """
Busca información económica reciente de Guatemala.

Necesito solamente:

Crecimiento económico:
Inflación:
IMAE:
Tasa líder:
Remesas:

Indica las fechas.

Utiliza fuentes oficiales cuando sea posible.

Termina con una conclusión breve.
"""
        return self.responder_consulta(pregunta, buscar_web=True)

    # ==========================================================
    # 6. ECONOMÍA DE ESTADOS UNIDOS
    # ==========================================================

    def economia_usa(self):
        pregunta = """
Busca información económica reciente de Estados Unidos.

Necesito solamente:

PIB:
Inflación:
Desempleo:
Tasa de la Reserva Federal:

Indica las fechas y fuentes.

Termina con una conclusión breve.
"""
        return self.responder_consulta(pregunta, buscar_web=True)

    # ==========================================================
    # 8. INFLACIÓN GUATEMALA
    # ==========================================================

    def inflacion_guatemala(self):
        pregunta = """
Busca la inflación MÁS RECIENTE de Guatemala.

Necesito:

Inflación interanual:
Inflación mensual:
Fecha:
Fuente:

Explica brevemente qué significa.
No inventes datos.
"""
        return self.responder_consulta(pregunta, buscar_web=True)

    # ==========================================================
    # 9. INFLACIÓN USA
    # ==========================================================

    def inflacion_usa(self):
        pregunta = """
Busca la inflación MÁS RECIENTE de Estados Unidos.

Necesito:

CPI:
Inflación interanual:
Inflación subyacente:
Fecha:
Fuente:

Explica brevemente.
No inventes datos.
"""
        return self.responder_consulta(pregunta, buscar_web=True)

    # ==========================================================
    # 10. IMAE GUATEMALA
    # ==========================================================

    def imae_guatemala(self):
        pregunta = """
Busca el IMAE MÁS RECIENTE de Guatemala.

Necesito:

IMAE:
Crecimiento interanual:
Fecha:
Fuente:

Explica brevemente qué significa.
No inventes datos.
"""
        return self.responder_consulta(pregunta, buscar_web=True)

    # ==========================================================
    # CONSULTA ABIERTA
    # ==========================================================

    def consulta_abierta(self, pregunta):
        if not pregunta.strip():
            return "⚠️ Escribe una pregunta."

        # ------------------------------------------------------
        # Detectar si necesita información actual
        # ------------------------------------------------------
        palabras_actuales = [
            "actual", "actualmente", "hoy", "ahora", "reciente",
            "último", "última", "precio", "inflación", "PIB", "IMAE",
            "tipo de cambio", "dólar", "bitcoin", "oro", "petróleo",
            "2026"
        ]

        texto = pregunta.lower()

        necesita_web = any(
            palabra.lower() in texto for palabra in palabras_actuales
        )

        return self.responder_consulta(pregunta, buscar_web=necesita_web)


# ==============================================================
# MENÚ
# ==============================================================

def main():
    tools = IntermediateTools()

    # ==========================================================
    # ENCABEZADO
    # ==========================================================
    print(
        """
╔════════════════════════════════════════════╗
║                                            ║
║              🤖 CROCKS                     ║
║                                            ║
║       ASISTENTE ECONÓMICO CON IA           ║
║                                            ║
║              Powered by Groq               ║
║                                            ║
╚════════════════════════════════════════════╝
"""
    )

    # ==========================================================
    # COMPROBAR API KEY
    # ==========================================================
    if not tools.api_key:
        print(
            """
❌ GROQ_API_KEY NO ENCONTRADA.

En PowerShell:

$env:GROQ_API_KEY="TU_API_KEY"

Después:

python .\\Crocks.py
"""
        )
        return

    print("✅ GROQ_API_KEY encontrada.")
    print("✅ CROCKS está listo.\n")

    # ==========================================================
    # MENÚ PRINCIPAL
    # ==========================================================
    while True:
        print("\n" + "=" * 55)

        print(
            """
1️⃣  Tipo de cambio USD → GTQ
2️⃣  Bitcoin
3️⃣  Petróleo
4️⃣  Oro
5️⃣  Economía de Guatemala
6️⃣  Economía de Estados Unidos
7️⃣  Consulta abierta
8️⃣  Inflación de Guatemala
9️⃣  Inflación de Estados Unidos
🔟  IMAE de Guatemala
0️⃣  Salir
"""
        )

        print("=" * 55)

        opcion = input(
            "\n👉 Selecciona una opción o escribe directamente una pregunta: "
        ).strip()

        if opcion == "1":
            print("\n🔎 Consultando tipo de cambio...\n")
            print(tools.obtener_tipo_cambio())

        elif opcion == "2":
            print("\n🔎 Consultando Bitcoin...\n")
            print(tools.obtener_bitcoin())

        elif opcion == "3":
            print("\n🔎 Buscando petróleo...\n")
            print(tools.obtener_petroleo())

        elif opcion == "4":
            print("\n🔎 Buscando oro...\n")
            print(tools.obtener_oro())

        elif opcion == "5":
            print("\n🔎 Analizando economía de Guatemala...\n")
            print(tools.economia_guatemala())

        elif opcion == "6":
            print("\n🔎 Analizando economía de Estados Unidos...\n")
            print(tools.economia_usa())

        elif opcion == "7":
            pregunta = input("\n✍️ Escribe tu pregunta:\n\n> ")
            print("\n🤖 CROCKS está pensando...\n")
            print(tools.consulta_abierta(pregunta))

        elif opcion == "8":
            print("\n🔎 Buscando inflación de Guatemala...\n")
            print(tools.inflacion_guatemala())

        elif opcion == "9":
            print("\n🔎 Buscando inflación de Estados Unidos...\n")
            print(tools.inflacion_usa())

        elif opcion == "10":
            print("\n🔎 Buscando IMAE de Guatemala...\n")
            print(tools.imae_guatemala())

        elif opcion == "0":
            print(
                """
👋 Gracias por utilizar CROCKS.

🇬🇹 Tu asistente económico.
"""
            )
            break

        else:
            print("\n🤖 CROCKS está pensando...\n")
            print(tools.consulta_abierta(opcion))

        # Pequeña pausa para evitar bombardear la API.
        time.sleep(1)


# ==============================================================
# EJECUTAR
# ==============================================================

if __name__ == "__main__":
    main()