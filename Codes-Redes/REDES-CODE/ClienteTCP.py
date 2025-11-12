import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk, messagebox

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False

# --- COLORES DARK MODE ---
BG_COLOR = "#2d2d2d"
FG_COLOR = "#d0d0d0"
WIDGET_BG = "#3c3c3c"
WIDGET_FG = "#d0d0d0"
BTN_BG = "#555555"
BTN_FG = "#ffffff"
BTN_ACTIVE = "#6a6a6a"
GREEN_STATUS = "#4CAF50"
RED_STATUS = "#F44336"
# Color especial para el texto del "cursor" en las cajas de entrada
ENTRY_CURSOR = "#ffffff" 

def conectar():
    global connected
    username = entry_user.get()
    if not username:
        messagebox.showerror("Error", "Debes ingresar un nombre de usuario.")
        return

    try:
        client.connect((HOST, PORT))
        connected = True
        
        client.sendall(username.encode("utf-8"))
        
        status_label.config(text=f"🟢 Conectado como: {username}", foreground=GREEN_STATUS)
        
        entry_msg.config(state=tk.NORMAL)
        btn_enviar.config(state=tk.NORMAL)
        entry_user.config(state=tk.DISABLED)
        btn_conectar.config(state=tk.DISABLED)
        
        chat_area.config(state=tk.NORMAL)
        chat_area.insert(tk.END, f"✅ Conectado a {HOST}:{PORT} como {username}\n")
        chat_area.config(state=tk.DISABLED)
        chat_area.see(tk.END)
        
        threading.Thread(target=recibir_mensajes, daemon=True).start()
        
    except Exception as e:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor: {e}")
        chat_area.config(state=tk.NORMAL)
        chat_area.insert(tk.END, f"❌ Error al conectar: {e}\n")
        chat_area.config(state=tk.DISABLED)
        chat_area.see(tk.END)

def recibir_mensajes():
    global connected
    while connected:
        try:
            data = client.recv(1024)
            if not data:
                raise Exception("Servidor desconectado.")
            
            chat_area.config(state=tk.NORMAL)
            chat_area.insert(tk.END, data.decode('utf-8'))
            chat_area.config(state=tk.DISABLED)
            chat_area.see(tk.END)
        except:
            status_label.config(text="🔴 Desconectado", fg=RED_STATUS)
            entry_msg.config(state=tk.DISABLED)
            btn_enviar.config(state=tk.DISABLED)
            connected = False
            # client.close() # No cerrar aquí, se maneja en 'al_cerrar'
            break

def enviar(event=None):
    msg = entry_msg.get()
    if msg and connected:
        # Añadir "Tú: " al chat localmente
        chat_area.config(state=tk.NORMAL)
        chat_area.insert(tk.END, f"💬 Tú: {msg}\n")
        chat_area.config(state=tk.DISABLED)
        chat_area.see(tk.END)
        
        client.sendall(msg.encode("utf-8"))
        entry_msg.delete(0, tk.END)
        
def al_cerrar():
    global connected
    if connected:
        connected = False
        client.close()
    ventana.quit()
    ventana.destroy()

# --- Interfaz Tkinter (Dark Mode) ---
ventana = tk.Tk()
ventana.title("Cliente TCP - Chat (Dark)")
ventana.geometry("450x450")
ventana.configure(bg=BG_COLOR)

# --- Configuración de Estilo Dark Mode ---
style = ttk.Style(ventana)
style.theme_use('clam')

# Estilos generales
style.configure('.',
                background=BG_COLOR,
                foreground=FG_COLOR,
                fieldbackground=WIDGET_BG,
                borderwidth=0)

style.configure('TFrame', background=BG_COLOR)

# TButton
style.configure('TButton',
                background=BTN_BG,
                foreground=BTN_FG,
                bordercolor=WIDGET_BG)
style.map('TButton',
          background=[('active', BTN_ACTIVE), ('disabled', WIDGET_BG)],
          foreground=[('disabled', BTN_BG)])

# TLabel
style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR)

# TEntry (cajas de texto)
style.configure('TEntry',
                foreground=WIDGET_FG,
                fieldbackground=WIDGET_BG,
                insertcolor=ENTRY_CURSOR) # Color del cursor de texto
style.map('TEntry',
          fieldbackground=[('disabled', WIDGET_BG)],
          foreground=[('disabled', BTN_BG)])

# --- Frame de Conexión ---
conn_frame = ttk.Frame(ventana, padding="10 10 10 10")
conn_frame.pack(fill=tk.X)

ttk.Label(conn_frame, text="Nombre:").pack(side=tk.LEFT, padx=5)
entry_user = ttk.Entry(conn_frame, width=20)
entry_user.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
btn_conectar = ttk.Button(conn_frame, text="Conectar", command=conectar)
btn_conectar.pack(side=tk.LEFT, padx=5)

# --- Frame de Chat ---
chat_frame = ttk.Frame(ventana, padding="10 0 10 10")
chat_frame.pack(fill=tk.BOTH, expand=True)

chat_area = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=15,
                                      font=("Arial", 10),
                                      bg=WIDGET_BG,
                                      fg=WIDGET_FG,
                                      insertbackground=ENTRY_CURSOR, # Cursor
                                      state='disabled')
chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

status_label = ttk.Label(chat_frame, text="🔴 Desconectado", foreground=RED_STATUS,
                         font=("Arial", 10, "bold"), anchor="center")
status_label.pack(fill=tk.X, pady=5)

# --- Frame de Mensaje ---
msg_frame = ttk.Frame(ventana, padding="10 0 10 10")
msg_frame.pack(fill=tk.X)

entry_msg = ttk.Entry(msg_frame, state=tk.DISABLED, width=40)
entry_msg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
btn_enviar = ttk.Button(msg_frame, text="Enviar", state=tk.DISABLED, command=enviar)
btn_enviar.pack(side=tk.LEFT, padx=5)

ventana.bind('<Return>', enviar)
ventana.protocol("WM_DELETE_WINDOW", al_cerrar)

ventana.mainloop()