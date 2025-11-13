import eel
import socket
import threading
import json

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
recv_buffer = ""

# Inicializa Eel en la carpeta 'web'
eel.init('web')

def recibir_mensajes():
    global connected, recv_buffer
    while connected:
        try:
            data = client.recv(4096).decode('utf-8')
            if not data:
                raise Exception("Servidor desconectado.")
            
            recv_buffer += data
            
            while "\n" in recv_buffer:
                message_line, recv_buffer = recv_buffer.split("\n", 1)
                
                if not message_line:
                    continue
                    
                try:
                    msg_data = json.loads(message_line)
                    # --- CAMBIO CLAVE ---
                    # En lugar de Tkinter, llama a una función de JavaScript
                    eel.actualizar_chat_js(msg_data)
                except json.JSONDecodeError:
                    print(f"Error decodificando JSON: {message_line}")

        except Exception as e:
            print(f"Error en recibir_mensajes: {e}")
            eel.actualizar_status_js(f"🔴 Desconectado: {e}", "red")
            connected = False
            break

# Expone esta función a JavaScript
@eel.expose
def conectar_py(username):
    global connected
    if not username:
        eel.mostrar_error_js("Debes ingresar un nombre de usuario.")
        return False
    try:
        client.connect((HOST, PORT))
        connected = True
        client.sendall(username.encode("utf-8"))
        
        # Iniciar hilo para recibir mensajes
        threading.Thread(target=recibir_mensajes, daemon=True).start()
        
        # Avisar a JS que la conexión fue exitosa
        eel.conexion_exitosa_js(username)
        eel.actualizar_status_js(f"🟢 Conectado como: {username}", "green")
        return True
        
    except Exception as e:
        eel.mostrar_error_js(f"No se pudo conectar al servidor: {e}")
        eel.actualizar_status_js(f"❌ Error al conectar: {e}", "red")
        return False

# Expone esta función a JavaScript
@eel.expose
def enviar_mensaje_py(msg):
    global connected
    if msg and connected:
        try:
            client.sendall(msg.encode("utf-8"))
            # Devuelve el mensaje para mostrarlo localmente como "Tú"
            return msg
        except Exception as e:
            eel.actualizar_status_js(f"🔴 Error al enviar: {e}", "red")
            return None
    return None

print("Iniciando cliente web... Abre la ventana.")
# Iniciar la aplicación web
eel.start('main.html', size=(450, 550), port=8080)
print("Cliente web cerrado.")