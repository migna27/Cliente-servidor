import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk, messagebox

HOST = "127.0.0.1"  # IP del servidor (127.0.0.1 si está en la misma PC)
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False

# --- Conectar con el servidor ---
def conectar():
    global connected
    username = entry_user.get()
    if not username:
        messagebox.showerror("Error", "Debes ingresar un nombre de usuario.")
        return

    try:
        client.connect((HOST, PORT))
        connected = True
        
        # Enviar el nombre de usuario primero
        client.sendall(username.encode("utf-8"))
        
        status_label.config(text=f"🟢 Conectado como: {username}", foreground="green")
        
        # Habilitar chat y deshabilitar conexión
        entry_msg.config(state=tk.NORMAL)
        btn_enviar.config(state=tk.NORMAL)
        entry_user.config(state=tk.DISABLED)
        btn_conectar.config(state=tk.DISABLED)
        
        chat_area.config(state=tk.NORMAL)
        chat_area.insert(tk.END, f"✅ Conectado a {HOST}:{PORT} como {username}\n")
        chat_area.config(state=tk.DISABLED)
        chat_area.see(tk.END)
        
        # Iniciar hilo para recibir mensajes
        threading.Thread(target=recibir_mensajes, daemon=True).start()
        
    except Exception as e:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor: {e}")
        chat_area.config(state=tk.NORMAL)
        chat_area.insert(tk.END, f"❌ Error al conectar: {e}\n")
        chat_area.config(state=tk.DISABLED)
        chat_area.see(tk.END)

# --- Recibir mensajes del servidor ---
def recibir_mensajes():
    global connected
    while connected:
        try:
            data = client.recv(1024)
            if not data:
                raise Exception("Servidor desconectado.")
            
            chat_area.config(state=tk.NORMAL)
            chat_area.insert(tk.END, data.decode('utf-8')) # El servidor ya envía el \n
            chat_area.config(state=tk.DISABLED)
            chat_area.see(tk.END)
        except:
            status_label.config(text="🔴 Desconectado", fg="red")
            entry_msg.config(state=tk.DISABLED)
            btn_enviar.config(state=tk.DISABLED)
            connected = False
            client.close()
            break

# --- Enviar mensajes al servidor ---
def enviar(event=None): # event=None para poder bindear 'Enter'
    msg = entry_msg.get()
    if msg and connected:
        client.sendall(msg.encode("utf-8"))
        entry_msg.delete(0, tk.END)
        
# --- Cerrar ventana (opcional pero buena práctica) ---
def al_cerrar():
    global connected
    if connected:
        connected = False
        client.close()
    ventana.quit()
    ventana.destroy()

# --- Interfaz Tkinter (Mejorada con ttk) ---
ventana = tk.Tk()
ventana.title("Cliente TCP - Chat")
ventana.geometry("450x450")

# Estilo
style = ttk.Style(ventana)
style.theme_use('clam')

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

chat_area = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=15, state='disabled', font=("Arial", 10))
chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

status_label = ttk.Label(chat_frame, text="🔴 Desconectado", foreground="red", font=("Arial", 10, "bold"), anchor="center")
status_label.pack(fill=tk.X, pady=5)

# --- Frame de Mensaje ---
msg_frame = ttk.Frame(ventana, padding="10 0 10 10")
msg_frame.pack(fill=tk.X)

entry_msg = ttk.Entry(msg_frame, state=tk.DISABLED, width=40)
entry_msg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
btn_enviar = ttk.Button(msg_frame, text="Enviar", state=tk.DISABLED, command=enviar)
btn_enviar.pack(side=tk.LEFT, padx=5)

# Bindear la tecla 'Enter' para enviar
ventana.bind('<Return>', enviar)

# Manejar cierre de ventana
ventana.protocol("WM_DELETE_WINDOW", al_cerrar)

ventana.mainloop()