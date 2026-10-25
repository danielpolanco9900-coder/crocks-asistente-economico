#######################
# Agente Basico De IA #
# Herramientas        #
#######################

import requests

class IntermediateTools:

    def __init__(self):
        pass

    # 1. Tipo de cambio general
    def consultar_tipo_cambio_api(self, moneda: str):
        print(f"Herramienta consultar_tipo_cambio_api llamada con moneda: {moneda}")
        if not moneda:
            return "Error: Se requiere el código de la moneda."
        url = f"https://open.er-api.com/v6/latest/{moneda.upper()}"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return f"ERROR: No se pudo obtener el tipo de cambio para {moneda}. Error: {e}"

    # 2. Tipo de cambio específico USD → GTQ
    def obtener_tipo_cambio_api(self, base: str = "USD", target: str = "GTQ"):
        print(f"Herramienta obtener_tipo_cambio_api llamada con base: {base}, target: {target}")
        url = f"https://api.exchangerate.host/latest?base={base}&symbols={target}"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return f"ERROR: No se pudo obtener el tipo de cambio de {base} a {target}. Error: {e}"

    # 3. Precio del Bitcoin
    def obtener_precio_bitcoin(self):
        url = "https://api.coindesk.com/v1/bpi/currentprice.json"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return f"ERROR: No se pudo obtener el precio del Bitcoin. Error: {e}"

    # 4. Precio del petróleo
    def obtener_precio_petroleo(self):
        url = "https://api.api-ninjas.com/v1/oilprice"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return f"ERROR: No se pudo obtener el precio del petróleo. Error: {e}"

    # 5. Precio del oro
    def obtener_precio_oro(self):
        url = "https://data-asg.goldprice.org/dbXRates/USD"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return f"ERROR: No se pudo obtener el precio del oro. Error: {e}"
