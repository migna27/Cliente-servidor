import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from datetime import datetime
import network_utils

# --- Configuración del Servidor ---

HOST = "0.0.0.0"
PORT = 5000
LOG_FILE = "chat_log.txt"

clientes = {}
lock = threading.Lock()
log_lock = threading.Lock()

# --- COLORES DARK MODE ---
BG_COLOR = "#2d2d2d"      # Fondo principal
FG_COLOR = "#d0d0d0"      # Texto principal
WIDGET_BG = "#3c3c3c"     # Fondo para widgets (entries, chat)
WIDGET_FG = "#d0d0d0"     # Texto para widgets
BTN_BG = "#555555"        # Fondo de botones
BTN_FG = "#ffffff"        # Texto de botones
BTN_ACTIVE = "#6a6a6a"   # Botón al pasar el mouse/click
GREEN_STATUS = "#4CAF50"  # Verde para "conectado"
RED_STATUS = "#F44336"    # Rojo para "desconectado"

def log_evento(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_con_timestamp = f"[{timestamp}] {mensaje}\n"
    
    with log_lock:
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(mensaje_con_timestamp)
        except Exception as e:
            print(f"Error al escribir en el log: {e}")
            
    # La GUI del servidor ahora se actualiza con los colores correctos
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, mensaje_con_timestamp)
    chat_area.see(tk.END)
    chat_area.config(state=tk.DISABLED)

def broadcast(mensaje, prefijo="", sender_conn=None):
    mensaje_formateado = f"{prefijo}{mensaje}"
    log_evento(mensaje_formateado)
    
    mensaje_para_clientes = f"{mensaje_formateado}\n".encode("utf-8")
    
    with lock:
        for conn in list(clientes.keys()):
            if conn == sender_conn:
                continue
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
        
        log_evento(f"🔗 {username} se ha conectado desde {addr}")
        broadcast(f"{username} se ha unido al chat.", prefijo="📢 Servidor: ")

        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            msg = data.decode("utf-8")
            broadcast(msg, prefijo=f"💬 {username}: ", sender_conn=conn)
            
    except Exception as e:
        print(f"Error con {addr}: {e}")
    finally:
        if conn in clientes:
            with lock:
                del clientes[conn]
            if username:
                broadcast(f"{username} se ha desconectado.", prefijo="📢 Servidor: ")
                log_evento(f"❌ {username} (conexión cerrada).")
        conn.close()

def iniciar_servidor():
    btn_iniciar.config(state=tk.DISABLED, text="Servidor Activo")
    status_label.config(text=f"🟢 Servidor activo en {HOST}:{PORT}", foreground=GREEN_STATUS)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    
    log_evento(f"Servidor escuchando en {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            hilo = threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True)
            hilo.start()
    except:
        log_evento("Servidor detenido manualmente.")
    finally:
        server.close()

# --- Interfaz Tkinter (Dark Mode) ---
ventana = tk.Tk()
ventana.title("Servidor TCP - Chat (Dark)")
ventana.geometry("450x400")
ventana.configure(bg=BG_COLOR)  # Fondo de la ventana principal

# --- Configuración de Estilo Dark Mode ---
style = ttk.Style(ventana)
# Usar un tema base que podamos sobreescribir
style.theme_use('clam') 

# Estilos generales
style.configure('.',
                background=BG_COLOR,
                foreground=FG_COLOR,
                fieldbackground=WIDGET_BG,
                borderwidth=0)

# Estilo para TFrame
style.configure('TFrame', background=BG_COLOR)

# Estilo para TButton
style.configure('TButton',
                background=BTN_BG,
                foreground=BTN_FG,
                bordercolor=WIDGET_BG)
style.map('TButton',
          background=[('active', BTN_ACTIVE), ('disabled', WIDGET_BG)],
          foreground=[('disabled', BTN_BG)])

# Estilo para TLabel
style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR)


# Frame principal
main_frame = ttk.Frame(ventana, padding="10 10 10 10", style='TFrame')
main_frame.pack(fill=tk.BOTH, expand=True)

# Área de chat (NO es ttk, se configura manualmente)
chat_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15,
                                      font=("Arial", 10),
                                      bg=WIDGET_BG,           # Fondo del widget
                                      fg=WIDGET_FG,           # Texto
                                      insertbackground=FG_COLOR, # Cursor
                                      state='normal')
chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
chat_area.config(state=tk.DISABLED) # Deshabilitar después de insertar

# Etiqueta de estado
status_label = ttk.Label(main_frame, text="🔴 Servidor detenido", foreground=RED_STATUS,
                         font=("Arial", 10, "bold"), anchor="center")
status_label.pack(pady=5, fill=tk.X)

# Botón de inicio
btn_iniciar = ttk.Button(main_frame, text="Iniciar Servidor",
                         command=lambda: threading.Thread(target=iniciar_servidor, daemon=True).start())
btn_iniciar.pack(pady=5, fill=tk.X, padx=5)

def saludo_inicial_log():
    log_evento("--- Servidor iniciado (Dark Mode). Esperando conexiones. ---")

saludo_inicial_log()

ventana.mainloop()