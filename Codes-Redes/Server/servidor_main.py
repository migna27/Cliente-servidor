import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk

# ### Importar nuestros módulos ###
import config
import logger
import command_handler
import network_utils

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


def broadcast(mensaje, prefijo="", sender_conn=None, log_this=True):
    """
    Envía un mensaje a todos los clientes, excepto al remitente.
    También lo loguea.
    """
    mensaje_formateado = f"{prefijo}{mensaje}"
    
    ###Loguear solo si se solicita ###
    if log_this:
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


# -- Frame de Controles de Admin ---

def on_send_admin_notification():
    """Envía un mensaje de admin a todos."""
    msg = admin_msg_entry.get()
    if not msg:
        return
    # Llama a broadcast, lo loguea (por defecto) y lo envía a todos
    broadcast(msg, prefijo="📢 [ADMIN]: ", sender_conn=None)
    admin_msg_entry.delete(0, tk.END)

def on_clear_all_chats():
    """Limpia la pantalla de chat de todos los clientes."""
    # 1. Loguear la acción administrativa por separado
    log_y_mostrar("[ADMIN_ACTION] Admin ha limpiado las ventanas de chat.")
    
    # 2. Enviar el comando secreto a todos SIN LOGUEARLO
    broadcast("__CLEAR_CHAT__", prefijo="", sender_conn=None, log_this=False)

admin_frame = ttk.Frame(main_frame, style='TFrame')
admin_frame.pack(fill=tk.X, padx=5, pady=(10, 5))

admin_msg_entry = ttk.Entry(admin_frame, style='TEntry')
admin_msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

btn_send_admin = ttk.Button(admin_frame, text="Enviar Notificación", command=on_send_admin_notification)
btn_send_admin.pack(side=tk.LEFT)

btn_clear_chat = ttk.Button(admin_frame, text="Limpiar Chats", command=on_clear_all_chats, style='TButton')
btn_clear_chat.pack(side=tk.LEFT, padx=5)



# Crear un marco para la información de IP
info_frame = ttk.Frame(main_frame, style='TFrame')
info_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

info_frame.columnconfigure(1, weight=1) # Hacer que la columna 1 (la IP) se expanda

# Obtener la IP Local (LAN)
try:
    local_ip = network_utils.get_local_ip()
except Exception as e:
    print(f"Error interno al obtener IP: {e}") # Imprime el error real en la consola
    local_ip = "Error al obtener IP"

# Etiqueta y texto para Conexión Local (Misma PC)
ttk.Label(info_frame, text="IP Local (Misma PC):", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5)
ip_local_text = tk.Text(info_frame, height=1, borderwidth=0, 
                         bg=config.WIDGET_BG, fg=config.WIDGET_FG, 
                         font=("Courier", 10))
ip_local_text.insert(tk.END, f"127.0.0.1:{config.PORT}")
ip_local_text.config(state=tk.DISABLED) # Hacerlo de solo lectura
ip_local_text.grid(row=0, column=1, sticky="ew", padx=5)

# Etiqueta y texto para Conexión de Red (LAN)
ttk.Label(info_frame, text="IP de Red (LAN):", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", padx=5)
ip_lan_text = tk.Text(info_frame, height=1, borderwidth=0, 
                       bg=config.WIDGET_BG, fg=config.WIDGET_FG, 
                       font=("Courier", 10))
ip_lan_text.insert(tk.END, f"{local_ip}:{config.PORT}")
ip_lan_text.config(state=tk.DISABLED) # Hacerlo de solo lectura
ip_lan_text.grid(row=1, column=1, sticky="ew", padx=5)

# Etiqueta para IP Pública
ttk.Label(info_frame, text="IP Pública (Internet):", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", padx=5)
ttk.Label(info_frame, text="(Debes buscar 'Cual es mi IP' en Google)", font=("Arial", 9, "italic")).grid(row=2, column=1, sticky="w", padx=5)

# --- Saludo Inicial ---
log_y_mostrar("--- Servidor (Modular) iniciado. Esperando conexiones. ---")

ventana.mainloop()