import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk

# ### Importar nuestros módulos ###
import config
import logger
import command_handler

# --- Estado Global del Servidor ---
clientes = {}  # {conn: username}
lock = threading.Lock() # Lock para la lista de 'clientes'

# --- Funciones de Lógica de Red ---

### función para centralizar el log Y la GUI ###
def log_y_mostrar(mensaje):
    """
    Paso 1: Escribe el mensaje en el archivo de log (usando nuestro módulo logger).
    Paso 2: Muestra el mensaje en la GUI del servidor.
    """
    # Paso 1: Loggear en el archivo
    logger.escribir_log(mensaje)
    
    # Paso 2: Mostrar en la GUI
    # (El timestamp ya lo añade el módulo logger, pero lo añadimos aquí 
    # para la GUI)
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S") # Hora corta para la GUI
    
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, f"[{timestamp}] {mensaje}\n")
    chat_area.see(tk.END)
    chat_area.config(state=tk.DISABLED)


def broadcast(mensaje, prefijo="", sender_conn=None):
    """
    Envía un mensaje a todos los clientes, excepto al remitente.
    También lo loguea.
    """
    mensaje_formateado = f"{prefijo}{mensaje}"
    
    ### Ahora llama a nuestra nueva función central ###
    log_y_mostrar(mensaje_formateado)
    
    mensaje_para_clientes = f"{mensaje_formateado}\n".encode("utf-8")
    
    with lock:
        for conn in list(clientes.keys()):
            if conn == sender_conn:
                continue # No enviar al remitente
            try:
                conn.sendall(mensaje_para_clientes)
            except Exception as e:
                print(f"Error enviando a {clientes[conn]}: {e}")
                conn.close()
                del clientes[conn]

def manejar_cliente(conn, addr):
    username = None
    try:
        username = conn.recv(1024).decode("utf-8")
        if not username:
            raise Exception("No se recibió nombre de usuario.")
        
        with lock:
            clientes[conn] = username
        
        ###Usar log_y_mostrar ###
        log_y_mostrar(f"🔗 {username} se ha conectado desde {addr}")
        broadcast(f"{username} se ha unido al chat.", prefijo="📢 Servidor: ")

        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            msg = data.decode("utf-8")
            
            ###Lógica de comando modularizada ###
            if msg.startswith('/'):
                command_handler.procesar_comando(conn, username, msg, clientes, lock)
            else:
                broadcast(msg, prefijo=f"💬 {username}: ", sender_conn=conn)
            
    except Exception as e:
        print(f"Error con {addr}: {e}")
    finally:
        if conn in clientes:
            with lock:
                del clientes[conn]
            if username:
                broadcast(f"{username} se ha desconectado.", prefijo="📢 Servidor: ")
                ### Usar log_y_mostrar ###
                log_y_mostrar(f"❌ {username} (conexión cerrada).")
        conn.close()

def iniciar_servidor():
    btn_iniciar.config(state=tk.DISABLED, text="Servidor Activo")
    ### Usar colores desde config ###
    status_label.config(text=f"🟢 Servidor activo en {config.HOST}:{config.PORT}", 
                        foreground=config.GREEN_STATUS)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((config.HOST, config.PORT))
    server.listen()
    
    ### Usar log_y_mostrar ###
    log_y_mostrar(f"Servidor escuchando en {config.HOST}:{config.PORT}")

    try:
        while True:
            conn, addr = server.accept()
            hilo = threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True)
            hilo.start()
    except:
        log_y_mostrar("Servidor detenido manualmente.")
    finally:
        server.close()

# --- Interfaz Tkinter ---
ventana = tk.Tk()
ventana.title("Servidor TCP - Chat (Modular)")
ventana.geometry("500x450")
ventana.configure(bg=config.BG_COLOR)

# --- Configuración de Estilo Dark Mode ---
style = ttk.Style(ventana)
style.theme_use('clam') 

# Estilos generales (usando config)
style.configure('.',
                background=config.BG_COLOR,
                foreground=config.FG_COLOR,
                fieldbackground=config.WIDGET_BG,
                borderwidth=0)
style.configure('TFrame', background=config.BG_COLOR)
style.configure('TButton',
                background=config.BTN_BG,
                foreground=config.BTN_FG,
                bordercolor=config.WIDGET_BG)
style.map('TButton',
          background=[('active', config.BTN_ACTIVE), ('disabled', config.WIDGET_BG)],
          foreground=[('disabled', config.BTN_BG)])
style.configure('TLabel', background=config.BG_COLOR, foreground=config.FG_COLOR)

# --- Creación de Widgets ---
main_frame = ttk.Frame(ventana, padding="10 10 10 10", style='TFrame')
main_frame.pack(fill=tk.BOTH, expand=True)

chat_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15,
                                      font=("Arial", 10),
                                      bg=config.WIDGET_BG,
                                      fg=config.WIDGET_FG,
                                      insertbackground=config.ENTRY_CURSOR,
                                      state='normal')
chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
chat_area.config(state=tk.DISABLED)

status_label = ttk.Label(main_frame, text="🔴 Servidor detenido", 
                         foreground=config.RED_STATUS,
                         font=("Arial", 10, "bold"), anchor="center")
status_label.pack(pady=5, fill=tk.X)

btn_iniciar = ttk.Button(main_frame, text="Iniciar Servidor",
                         command=lambda: threading.Thread(target=iniciar_servidor, daemon=True).start())
btn_iniciar.pack(pady=5, fill=tk.X, padx=5)

# --- Saludo Inicial ---
log_y_mostrar("--- Servidor (Modular) iniciado. Esperando conexiones. ---")

ventana.mainloop()