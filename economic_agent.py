from intermediate_tools import IntermediateTools

SYSTEM_PROMPT = """
Eres un agente económico. Tu objetivo es analizar datos de tipo de cambio y clima
para apoyar decisiones económicas básicas en Guatemala.
"""

def main():
    print(SYSTEM_PROMPT)
    tools = IntermediateTools()

    # Obtener tipo de cambio USD → GTQ
    tipo_cambio = tools.obtener_tipo_cambio_api("USD", "GTQ")
    print("Tipo de cambio USD/GTQ:", tipo_cambio)

    # Obtener latitud y longitud de Guatemala
    latlong = tools.obtener_lat_long("Guatemala")
    print("Lat/Long de Guatemala:", latlong)

    # Obtener clima actual
    clima = tools.obtener_clima_api("14.6349", "-90.5069")
    print("Clima en Guatemala:", clima)

if __name__ == "__main__":
    main()
