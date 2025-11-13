import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk, messagebox
import json 

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
recv_buffer = "" # Buffer para mensajes JSON

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

def process_message_data(msg_data):
    """Procesa un objeto de mensaje JSON ya decodificado."""
    global chat_area
    msg_type = msg_data.get("type")

    try:
        if msg_type == "chat":
            msg_id = msg_data.get("id", "unknown")
            prefix = msg_data.get("prefix", "")
            payload = msg_data.get("payload", "")
            full_msg = f"{prefix}{payload}\n"
            
            chat_area.config(state=tk.NORMAL)
            
            # --- Lógica de Tags para Eliminar ---
            # 1. Obtenemos el índice DE INICIO (antes de insertar)
            start_index = chat_area.index(tk.END + "-1c")
            
            # 2. Insertamos el texto
            chat_area.insert(tk.END, full_msg)
            
            # 3. Obtenemos el índice DE FIN (después de insertar)
            end_index = chat_area.index(tk.END + "-1c")
            
            # 4. Añadimos un 'tag' al texto que acabamos de insertar
            #    El nombre del tag es el propio ID del mensaje
            chat_area.tag_add(msg_id, start_index, end_index)
            # --- Fin de Lógica de Tags ---

            chat_area.config(state=tk.DISABLED)
            chat_area.see(tk.END)

        elif msg_type == "delete":
            id_to_delete = msg_data.get("id")
            if not id_to_delete:
                return

            # Buscar rangos de texto con el tag (ID)
            tag_ranges = chat_area.tag_ranges(id_to_delete)
            
            if tag_ranges:
                # tag_ranges nos da (start, end)
                start, end = tag_ranges
                chat_area.config(state=tk.NORMAL)
                # Reemplazar el contenido
                chat_area.delete(start, end)
                chat_area.insert(start, ">> Mensaje eliminado por el administrador <<\n")
                chat_area.config(state=tk.DISABLED)

        elif msg_type == "clear":
            chat_area.config(state=tk.NORMAL)
            chat_area.delete('1.0', tk.END)
            chat_area.insert(tk.END, "📢 El chat fue limpiado por un administrador.\n")
            chat_area.config(state=tk.DISABLED)
            
    except Exception as e:
        print(f"Error procesando mensaje: {e}")


def recibir_mensajes():
    global connected, recv_buffer
    while connected:
        try:
            # Recibimos datos en el buffer
            data = client.recv(4096).decode('utf-8')
            if not data:
                raise Exception("Servidor desconectado.")
            
            recv_buffer += data
            
            # Procesamos todos los mensajes completos (terminados en \n)
            # que tengamos en el buffer
            while "\n" in recv_buffer:
                # Separamos el primer mensaje del resto
                message_line, recv_buffer = recv_buffer.split("\n", 1)
                
                if not message_line:
                    continue
                    
                # Intentamos decodificar el JSON
                try:
                    msg_data = json.loads(message_line)
                    # Llamamos a la función que procesa la lógica
                    process_message_data(msg_data)
                except json.JSONDecodeError:
                    print(f"Error decodificando JSON, datos corruptos: {message_line}")

        except Exception as e:
            # Si hay un error, salimos del bucle
            print(f"Error en recibir_mensajes: {e}")
            status_label.config(text="🔴 Desconectado", fg=RED_STATUS)
            entry_msg.config(state=tk.DISABLED)
            btn_enviar.config(state=tk.DISABLED)
            connected = False
            break # Salir del bucle while

def enviar(event=None):
    msg = entry_msg.get()
    if msg and connected:
        # El cliente NO envía JSON, solo texto plano.
        # El servidor se encarga de envolverlo en JSON.
        
        # PERO, sí mostramos el "Tú: " localmente.
        # Para esto, necesitamos crear un ID local y usar el tag
        # por si queremos borrar nuestros propios mensajes (aunque no es el caso)
        # Simplificación: El cliente solo envía el texto crudo.
        
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
style.configure('TButton',
                background=BTN_BG,
                foreground=BTN_FG,
                bordercolor=WIDGET_BG)
style.map('TButton',
          background=[('active', BTN_ACTIVE), ('disabled', WIDGET_BG)],
          foreground=[('disabled', BTN_BG)])
style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR)
style.configure('TEntry',
                foreground=WIDGET_FG,
                fieldbackground=WIDGET_BG,
                insertcolor=ENTRY_CURSOR)
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
                                      insertbackground=ENTRY_CURSOR,
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