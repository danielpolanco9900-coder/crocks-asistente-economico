import tkinter as tk
from tkinter import ttk, messagebox
import threading

from Crocks import IntermediateTools


# ==========================================================
# CROCKS - INTERFAZ GRÁFICA
# ==========================================================

class CrocksGUI:

    def __init__(self, root):

        self.root = root

        self.root.title("CROCKS — Asistente Económico con IA")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        # Colores
        self.bg = "#0F1117"
        self.sidebar = "#171A21"
        self.card = "#1C2029"
        self.card_hover = "#252B36"
        self.blue = "#4F8CFF"
        self.blue_hover = "#6A9DFF"
        self.white = "#F5F7FA"
        self.gray = "#9CA6B5"
        self.green = "#42D392"

        self.root.configure(bg=self.bg)

        # Cerebro
        self.tools = IntermediateTools()

        self.crear_interfaz()

    # ======================================================
    # INTERFAZ
    # ======================================================

    def crear_interfaz(self):

        # -----------------------------------------------
        # SIDEBAR
        # -----------------------------------------------

        self.sidebar_frame = tk.Frame(
            self.root,
            bg=self.sidebar,
            width=270
        )

        self.sidebar_frame.pack(
            side="left",
            fill="y"
        )

        self.sidebar_frame.pack_propagate(False)

        # Logo
        tk.Label(
            self.sidebar_frame,
            text="🤖",
            font=("Segoe UI Emoji", 35),
            bg=self.sidebar,
            fg=self.white
        ).pack(pady=(30, 5))

        tk.Label(
            self.sidebar_frame,
            text="CROCKS",
            font=("Segoe UI", 24, "bold"),
            bg=self.sidebar,
            fg=self.white
        ).pack()

        tk.Label(
            self.sidebar_frame,
            text="ASISTENTE ECONÓMICO",
            font=("Segoe UI", 9),
            bg=self.sidebar,
            fg=self.gray
        ).pack(pady=(0, 20))

        # Estado
        estado = "●  API conectada"

        tk.Label(
            self.sidebar_frame,
            text=estado,
            font=("Segoe UI", 9, "bold"),
            bg=self.sidebar,
            fg=self.green
        ).pack(pady=(0, 20))

        # Separador
        tk.Frame(
            self.sidebar_frame,
            height=1,
            bg="#2A303A"
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 15)
        )

        tk.Label(
            self.sidebar_frame,
            text="HERRAMIENTAS",
            font=("Segoe UI", 8, "bold"),
            bg=self.sidebar,
            fg=self.gray
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 8)
        )

        # Botones
        botones = [

            ("💱   Tipo de cambio", self.tipo_cambio),

            ("₿   Bitcoin", self.bitcoin),

            ("🛢️   Petróleo", self.petroleo),

            ("🥇   Oro", self.oro),

            ("🇬🇹   Economía Guatemala", self.economia_gt),

            ("🇺🇸   Economía EE.UU.", self.economia_usa),

            ("📊   Inflación Guatemala", self.inflacion_gt),

            ("📈   Inflación EE.UU.", self.inflacion_usa),

            ("📉   IMAE Guatemala", self.imae),

        ]

        for texto, comando in botones:

            boton = tk.Button(
                self.sidebar_frame,
                text=texto,
                command=comando,

                font=("Segoe UI", 10),

                bg=self.sidebar,
                fg=self.white,

                activebackground=self.card_hover,
                activeforeground=self.white,

                relief="flat",
                bd=0,

                anchor="w",

                padx=25,
                pady=9,

                cursor="hand2"
            )

            boton.pack(
                fill="x"
            )

        # Footer

        tk.Label(
            self.sidebar_frame,
            text="Powered by Groq",
            font=("Segoe UI", 8),
            bg=self.sidebar,
            fg=self.gray
        ).pack(
            side="bottom",
            pady=20
        )

        # -----------------------------------------------
        # ÁREA PRINCIPAL
        # -----------------------------------------------

        self.main_frame = tk.Frame(
            self.root,
            bg=self.bg
        )

        self.main_frame.pack(
            side="left",
            fill="both",
            expand=True
        )

        # -----------------------------------------------
        # ENCABEZADO
        # -----------------------------------------------

        tk.Label(
            self.main_frame,
            text="Centro de análisis económico",
            font=("Segoe UI", 25, "bold"),
            bg=self.bg,
            fg=self.white
        ).pack(
            anchor="w",
            padx=40,
            pady=(35, 5)
        )

        tk.Label(
            self.main_frame,
            text="Consulta indicadores, mercados y conceptos económicos con inteligencia artificial.",
            font=("Segoe UI", 10),
            bg=self.bg,
            fg=self.gray
        ).pack(
            anchor="w",
            padx=40
        )

        # -----------------------------------------------
        # CAJA DE CONSULTA
        # -----------------------------------------------

        consulta = tk.Frame(
            self.main_frame,
            bg=self.card
        )

        consulta.pack(
            fill="x",
            padx=40,
            pady=(25, 20)
        )

        tk.Label(
            consulta,
            text="💬  Pregúntale a CROCKS",
            font=("Segoe UI", 12, "bold"),
            bg=self.card,
            fg=self.white
        ).pack(
            anchor="w",
            padx=20,
            pady=(15, 10)
        )

        fila = tk.Frame(
            consulta,
            bg=self.card
        )

        fila.pack(
            fill="x",
            padx=20,
            pady=(0, 18)
        )

        self.entrada = tk.Entry(
            fila,
            font=("Segoe UI", 11),

            bg="#252B36",
            fg=self.white,

            insertbackground=self.white,

            relief="flat",
            bd=0
        )

        self.entrada.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=11
        )

        self.entrada.insert(
            0,
            "Escribe tu pregunta..."
        )

        self.entrada.bind(
            "<FocusIn>",
            self.quitar_placeholder
        )

        self.entrada.bind(
            "<Return>",
            lambda event: self.consultar()
        )

        self.boton_consultar = tk.Button(
            fila,
            text="CONSULTAR  →",

            command=self.consultar,

            font=("Segoe UI", 10, "bold"),

            bg=self.blue,
            fg="white",

            activebackground=self.blue_hover,
            activeforeground="white",

            relief="flat",
            bd=0,

            cursor="hand2",

            padx=20,
            pady=10
        )

        self.boton_consultar.pack(
            side="right",
            padx=(12, 0)
        )

        # -----------------------------------------------
        # RESPUESTA
        # -----------------------------------------------

        encabezado = tk.Frame(
            self.main_frame,
            bg=self.bg
        )

        encabezado.pack(
            fill="x",
            padx=40
        )

        tk.Label(
            encabezado,
            text="Respuesta",
            font=("Segoe UI", 13, "bold"),
            bg=self.bg,
            fg=self.white
        ).pack(
            side="left"
        )

        self.estado = tk.Label(
            encabezado,
            text="● Listo",
            font=("Segoe UI", 9),
            bg=self.bg,
            fg=self.green
        )

        self.estado.pack(
            side="right"
        )

        # -----------------------------------------------
        # CAJA DE RESPUESTA
        # -----------------------------------------------

        respuesta_frame = tk.Frame(
            self.main_frame,
            bg=self.card
        )

        respuesta_frame.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=(8, 30)
        )

        self.respuesta = tk.Text(
            respuesta_frame,

            font=("Segoe UI", 11),

            bg=self.card,
            fg=self.white,

            insertbackground=self.white,

            relief="flat",
            bd=0,

            wrap="word",

            padx=25,
            pady=20
        )

        self.respuesta.pack(
            fill="both",
            expand=True
        )

        self.respuesta.insert(
            "1.0",

            "👋 Bienvenido a CROCKS.\n\n"

            "Tu asistente económico está listo.\n\n"

            "Puedes utilizar el menú de la izquierda "
            "o escribir una pregunta arriba.\n\n"

            "Ejemplos:\n\n"

            "• ¿Qué es la inflación?\n"
            "• ¿Cómo funciona la política monetaria?\n"
            "• ¿Cuál es el PIB de Guatemala?\n"
            "• Analiza el tipo de cambio USD/GTQ."
        )

        self.respuesta.config(
            state="disabled"
        )

    # ======================================================
    # PLACEHOLDER
    # ======================================================

    def quitar_placeholder(self, event):

        if self.entrada.get() == "Escribe tu pregunta...":

            self.entrada.delete(
                0,
                "end"
            )

    # ======================================================
    # MOSTRAR RESULTADO
    # ======================================================

    def mostrar(self, texto):

        self.respuesta.config(
            state="normal"
        )

        self.respuesta.delete(
            "1.0",
            "end"
        )

        self.respuesta.insert(
            "1.0",
            texto
        )

        self.respuesta.config(
            state="disabled"
        )

    # ======================================================
    # EJECUTAR CONSULTA
    # ======================================================

    def ejecutar(self, funcion):

        self.boton_consultar.config(
            state="disabled"
        )

        self.estado.config(
            text="● Consultando...",
            fg="#F5C451"
        )

        self.mostrar(
            "⏳ CROCKS está procesando la información...\n\n"
            "Espera un momento."
        )

        def proceso():

            try:

                resultado = funcion()

            except Exception as e:

                resultado = (
                    "❌ Ocurrió un error.\n\n"
                    f"{e}"
                )

            self.root.after(
                0,
                lambda: self.finalizar(resultado)
            )

        threading.Thread(
            target=proceso,
            daemon=True
        ).start()

    # ======================================================
    # FINALIZAR
    # ======================================================

    def finalizar(self, resultado):

        self.mostrar(
            resultado
        )

        self.estado.config(
            text="● Consulta completada",
            fg=self.green
        )

        self.boton_consultar.config(
            state="normal"
        )

    # ======================================================
    # CONSULTA ABIERTA
    # ======================================================

    def consultar(self):

        pregunta = self.entrada.get().strip()

        if not pregunta or pregunta == "Escribe tu pregunta...":

            messagebox.showwarning(
                "CROCKS",
                "Escribe una pregunta primero."
            )

            return

        self.ejecutar(
            lambda: self.tools.consulta_abierta(
                pregunta
            )
        )

    # ======================================================
    # BOTONES
    # ======================================================

    def tipo_cambio(self):

        self.ejecutar(
            self.tools.obtener_tipo_cambio
        )

    def bitcoin(self):

        self.ejecutar(
            self.tools.obtener_bitcoin
        )

    def petroleo(self):

        self.ejecutar(
            self.tools.obtener_petroleo
        )

    def oro(self):

        self.ejecutar(
            self.tools.obtener_oro
        )

    def economia_gt(self):

        self.ejecutar(
            self.tools.economia_guatemala
        )

    def economia_usa(self):

        self.ejecutar(
            self.tools.economia_usa
        )

    def inflacion_gt(self):

        self.ejecutar(
            self.tools.inflacion_guatemala
        )

    def inflacion_usa(self):

        self.ejecutar(
            self.tools.inflacion_usa
        )

    def imae(self):

        self.ejecutar(
            self.tools.imae_guatemala
        )


# ==========================================================
# INICIAR
# ==========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = CrocksGUI(root)

    root.mainloop()
