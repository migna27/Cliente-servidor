# Proyecto Chat Cliente-Servidor (Quick Start)

# Guía esencial para ejecutar el servidor y los clientes.

# 1. Dependencias

Este proyecto requiere Python 3.

Para el Cliente Web, instala eel:

pip install eel


# 2. Iniciar el Servidor

Abre una terminal y ejecuta:

# Navega a la carpeta del servidor
cd Codes-Redes/Server

# Ejecuta el servidor (esto abre la GUI de admin)
python servidor_main.py


# 3. Conectar un Cliente

Abre una segunda terminal y elige una opción:

Opción A: Cliente Nativo (Tkinter)

# Navega a la carpeta del cliente Tkinter
cd Codes-Redes/REDES-CODE

# Ejecuta el cliente
python ClienteTCP.py


Opción B: Cliente Web (Eel)

# Navega a la carpeta del cliente web
cd ClienteWeb

# Ejecuta el backend (esto lanza el navegador)
python cliente_web_backend.py
