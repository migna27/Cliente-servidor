import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import json  # Importar JSON
import uuid  # Importar para IDs únicos

# ### Importar nuestros módulos ###
import config
import logger
import command_handler
import network_utils

# --- Estado Global del Servidor ---
clientes = {}  # {conn: username}
lock = threading.Lock() # Lock para la lista de 'clientes'

# --- Funciones de Lógica de Red ---

def log_y_mostrar(mensaje):
    """
    Paso 1: Escribe el mensaje en el archivo de log (usando nuestro módulo logger).
    Paso 2: Muestra el mensaje en la GUI del servidor.
    """
    # Paso 1: Loggear en el archivo
    logger.escribir_log(mensaje)
    
    # Paso 2: Mostrar en la GUI
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S") # Hora corta para la GUI
    
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, f"[{timestamp}] {mensaje}\n")
    chat_area.see(tk.END)
    chat_area.config(state=tk.DISABLED)


def broadcast_data(data_dict, sender_conn=None):
    """
    Convierte un diccionario a JSON y lo envía a todos los clientes
    (excepto al remitente).
    Añade una nueva línea para actuar como delimitador.
    """
    try:
        # Usamos '\n' como delimitador de mensajes JSON
        mensaje_json = json.dumps(data_dict) + "\n"
        mensaje_bytes = mensaje_json.encode("utf-8")
        
        with lock:
            for conn in list(clientes.keys()):
                if conn == sender_conn:
                    continue
                try:
                    conn.sendall(mensaje_bytes)
                except Exception as e:
                    print(f"Error enviando a {clientes[conn]}: {e}")
                    conn.close()
                    del clientes[conn]
    except Exception as e:
        print(f"Error en broadcast_data: {e}")

def manejar_cliente(conn, addr):
    username = None
    try:
        username = conn.recv(1024).decode("utf-8")
        if not username:
            raise Exception("No se recibió nombre de usuario.")
        
        with lock:
            clientes[conn] = username
        
        # Loguear localmente
        log_y_mostrar(f"🔗 {username} se ha conectado desde {addr}")
        
        # Enviar notificación de unión a todos (incluido el nuevo cliente)
        join_data = {
            "type": "chat",
            "id": "server_" + str(uuid.uuid4())[:4],
            "prefix": "📢 Servidor: ",
            "payload": f"{username} se ha unido al chat."
        }
        broadcast_data(join_data) # Sin sender_conn para que lo reciban todos

        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            msg = data.decode("utf-8")
            
            if msg.startswith('/'):
                # Es un comando, pasarlo al command_handler
                command_handler.procesar_comando(conn, username, msg, clientes, lock)
            else:
                # Es un mensaje de chat normal
                # 1. Generar un ID único para este mensaje
                msg_id = str(uuid.uuid4())[:8] # Un ID corto de 8 caracteres
                prefix = f"💬 {username}: "
                
                # 2. Loguearlo localmente (servidor) con su ID
                log_y_mostrar(f"[ID: {msg_id}] {prefix}{msg}")
                
                # 3. Preparar el paquete de datos JSON para los clientes
                data_to_send = {
                    "type": "chat",
                    "id": msg_id,
                    "prefix": prefix,
                    "payload": msg
                }
                
                # 4. Enviar a todos los demás
                broadcast_data(data_to_send, sender_conn=conn)
            
    except Exception as e:
        print(f"Error con {addr}: {e}")
    finally:
        if conn in clientes:
            with lock:
                del clientes[conn]
            if username:
                # Enviar notificación de salida
                leave_msg = f"{username} se ha desconectado."
                leave_data = {
                    "type": "chat",
                    "id": "server_" + str(uuid.uuid4())[:4],
                    "prefix": "📢 Servidor: ",
                    "payload": leave_msg
                }
                broadcast_data(leave_data) # Sin sender_conn
                
                log_y_mostrar(f"❌ {username} (conexión cerrada).")
        conn.close()

def iniciar_servidor():
    btn_iniciar.config(state=tk.DISABLED, text="Servidor Activo")
    status_label.config(text=f"🟢 Servidor activo en {config.HOST}:{config.PORT}", 
                        foreground=config.GREEN_STATUS)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((config.HOST, config.PORT))
    server.listen()
    
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
ventana.geometry("500x550") # Aumenté un poco la altura
ventana.configure(bg=config.BG_COLOR)

# --- Configuración de Estilo Dark Mode ---
style = ttk.Style(ventana)
style.theme_use('clam') 
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
style.configure('TEntry',
                foreground=config.WIDGET_FG,
                fieldbackground=config.WIDGET_BG,
                insertcolor=config.ENTRY_CURSOR)

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
    """Envía un mensaje de admin a todos usando el protocolo JSON."""
    msg = admin_msg_entry.get()
    if not msg:
        return
    
    msg_id = "admin_" + str(uuid.uuid4())[:4]
    prefix = "📢 [ADMIN]: "
    
    # 1. Loguear localmente
    log_y_mostrar(f"[ID: {msg_id}] {prefix}{msg}")
    
    # 2. Preparar JSON y enviar
    data_to_send = {
        "type": "chat",
        "id": msg_id,
        "prefix": prefix,
        "payload": msg
    }
    broadcast_data(data_to_send) # Enviar a todos
    admin_msg_entry.delete(0, tk.END)

def on_clear_all_chats():
    """Limpia la pantalla de chat de todos los clientes."""
    # 1. Loguear la acción
    log_y_mostrar("[ADMIN_ACTION] Admin ha limpiado las ventanas de chat.")
    
    # 2. Enviar el comando "clear"
    data_to_send = {"type": "clear"}
    broadcast_data(data_to_send)

admin_frame = ttk.Frame(main_frame, style='TFrame')
admin_frame.pack(fill=tk.X, padx=5, pady=(10, 5))

admin_msg_entry = ttk.Entry(admin_frame, style='TEntry')
admin_msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

btn_send_admin = ttk.Button(admin_frame, text="Enviar Notificación", command=on_send_admin_notification)
btn_send_admin.pack(side=tk.LEFT)

btn_clear_chat = ttk.Button(admin_frame, text="Limpiar Chats", command=on_clear_all_chats, style='TButton')
btn_clear_chat.pack(side=tk.LEFT, padx=5)


# --- Frame de Eliminar por ID ---

def on_delete_by_id():
    """Envía un comando 'delete' con un ID específico."""
    id_to_delete = admin_id_entry.get().strip()
    if not id_to_delete:
        return
        
    # 1. Loguear la acción
    log_y_mostrar(f"[ADMIN_ACTION] Admin eliminó mensaje ID: {id_to_delete}")
    
    # 2. Enviar el comando "delete"
    data_to_send = {"type": "delete", "id": id_to_delete}
    broadcast_data(data_to_send)
    
    admin_id_entry.delete(0, tk.END)

# Nuevo frame para la función de eliminar
delete_frame = ttk.Frame(main_frame, style='TFrame')
delete_frame.pack(fill=tk.X, padx=5, pady=5)

ttk.Label(delete_frame, text="ID de Mensaje:").pack(side=tk.LEFT, padx=5)
admin_id_entry = ttk.Entry(delete_frame, style='TEntry', width=15)
admin_id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

btn_delete_id = ttk.Button(delete_frame, text="Eliminar Mensaje", command=on_delete_by_id)
btn_delete_id.pack(side=tk.LEFT)


# --- Frame de Información de Conexión ---
info_frame = ttk.Frame(main_frame, style='TFrame')
info_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

info_frame.columnconfigure(1, weight=1)

try:
    local_ip = network_utils.get_local_ip()
except Exception as e:
    print(f"Error interno al obtener IP: {e}")
    local_ip = "Error al obtener IP"

# Conexión Local (Misma PC)
ttk.Label(info_frame, text="IP Local (Misma PC):", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5)
ip_local_text = tk.Text(info_frame, height=1, borderwidth=0, 
                         bg=config.WIDGET_BG, fg=config.WIDGET_FG, 
                         font=("Courier", 10))
ip_local_text.insert(tk.END, f"127.0.0.1:{config.PORT}")
ip_local_text.config(state=tk.DISABLED)
ip_local_text.grid(row=0, column=1, sticky="ew", padx=5)

# Conexión de Red (LAN)
ttk.Label(info_frame, text="IP de Red (LAN):", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", padx=5)
ip_lan_text = tk.Text(info_frame, height=1, borderwidth=0, 
                       bg=config.WIDGET_BG, fg=config.WIDGET_FG, 
                       font=("Courier", 10))
ip_lan_text.insert(tk.END, f"{local_ip}:{config.PORT}")
ip_lan_text.config(state=tk.DISABLED)
ip_lan_text.grid(row=1, column=1, sticky="ew", padx=5)

# IP Pública
ttk.Label(info_frame, text="IP Pública (Internet):", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", padx=5)
ttk.Label(info_frame, text="(Requiere Port Forwarding o VPN)", font=("Arial", 9, "italic")).grid(row=2, column=1, sticky="w", padx=5)

# --- Saludo Inicial ---
log_y_mostrar("--- Servidor (Modular) iniciado. Esperando conexiones. ---")

ventana.mainloop()