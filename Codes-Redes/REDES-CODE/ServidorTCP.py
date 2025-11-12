import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk  # Importar themed widgets

HOST = "0.0.0.0"
PORT = 5000

# --- Almacenamiento de clientes y lock ---
clientes = {}  # Usar un diccionario para guardar (conn, username)
lock = threading.Lock()

# --- Función para retransmitir mensajes a todos ---
def broadcast(mensaje, prefijo=""):
    """Envía un mensaje a todos los clientes conectados."""
    # Usamos un lock para evitar problemas si un cliente se une/desconecta
    # mientras estamos iterando
    with lock:
        # El mensaje completo a enviar
        mensaje_completo = f"{prefijo}{mensaje}\n".encode("utf-8")
        chat_area.insert(tk.END, f"{prefijo}{mensaje}\n")
        chat_area.see(tk.END)
        
        # Iterar sobre una copia para poder modificar el dict original si hay un error
        for conn in list(clientes.keys()):
            try:
                conn.sendall(mensaje_completo)
            except Exception as e:
                print(f"Error enviando a {clientes[conn]}: {e}")
                # Si hay error, asumimos que se desconectó
                conn.close()
                del clientes[conn]

# --- Función para manejar la conexión con un cliente ---
def manejar_cliente(conn, addr):
    username = None
    try:
        # Lo primero que recibimos es el nombre de usuario
        username = conn.recv(1024).decode("utf-8")
        if not username:
            raise Exception("No se recibió nombre de usuario.")
        
        # Añadir cliente a la lista
        with lock:
            clientes[conn] = username
        
        chat_area.insert(tk.END, f"🔗 {username} se ha conectado desde {addr}\n")
        chat_area.see(tk.END)
        broadcast(f"{username} se ha unido al chat.", prefijo="📢 Servidor: ")

        # Loop para recibir mensajes del cliente
        while True:
            data = conn.recv(1024)
            if not data:
                break  # Cliente se desconectó
            
            msg = data.decode("utf-8")
            # Retransmitir el mensaje con el nombre del usuario
            broadcast(msg, prefijo=f"💬 {username}: ")
            
    except Exception as e:
        print(f"Error con {addr}: {e}")
    finally:
        # Limpieza al desconectar
        if conn in clientes:
            with lock:
                del clientes[conn]
            if username:
                broadcast(f"{username} se ha desconectado.", prefijo="📢 Servidor: ")
                chat_area.insert(tk.END, f"❌ {username} se ha desconectado.\n")
                chat_area.see(tk.END)
        conn.close()

# --- Función para iniciar el servidor ---
def iniciar_servidor():
    btn_iniciar.config(state=tk.DISABLED, text="Servidor Activo")
    status_label.config(text=f"🟢 Servidor activo en {HOST}:{PORT}", foreground="green")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    chat_area.insert(tk.END, f"Servidor escuchando en {HOST}:{PORT}\n")
    chat_area.see(tk.END)

    try:
        while True:
            conn, addr = server.accept()
            # Iniciar un hilo para cada cliente
            hilo = threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True)
            hilo.start()
    except:
        print("Servidor detenido.")
    finally:
        server.close()

# --- Interfaz Tkinter (Mejorada con ttk) ---
ventana = tk.Tk()
ventana.title("Servidor TCP - Chat")
ventana.geometry("450x400")

# Estilo
style = ttk.Style(ventana)
style.theme_use('clam')  # 'clam', 'alt', 'default', 'classic'

# Frame principal
main_frame = ttk.Frame(ventana, padding="10 10 10 10")
main_frame.pack(fill=tk.BOTH, expand=True)

# Área de chat
chat_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15, state='normal', font=("Arial", 10))
chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Etiqueta de estado
status_label = ttk.Label(main_frame, text="🔴 Servidor detenido", foreground="red", font=("Arial", 10, "bold"))
status_label.pack(pady=5)

# Botón de inicio
btn_iniciar = ttk.Button(main_frame, text="Iniciar Servidor",
                         command=lambda: threading.Thread(target=iniciar_servidor, daemon=True).start())
btn_iniciar.pack(pady=5, fill=tk.X, padx=5)

ventana.mainloop()
