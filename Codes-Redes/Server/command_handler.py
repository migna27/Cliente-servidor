import json
import uuid

def enviar_mensaje_privado(conn, mensaje_payload):
    """
    Envía un mensaje privado (como un comando) al cliente 
    usando el protocolo JSON.
    """
    try:
        # Creamos un paquete JSON, igual que en el servidor principal
        data_to_send = {
            "type": "chat",
            "id": "cmd_" + str(uuid.uuid4())[:4], # ID único para el comando
            "prefix": "", # El payload ya lo incluye todo
            "payload": mensaje_payload
        }
        
        mensaje_json = json.dumps(data_to_send) + "\n"
        conn.sendall(mensaje_json.encode("utf-8"))
        
    except Exception as e:
        print(f"Error enviando mensaje privado JSON: {e}")

def procesar_comando(conn, username, msg, clientes, lock):
    """
    Procesa un comando recibido de un cliente.
    """
    
    comando = msg.split(' ')[0]
    
    # --- Comando /help ---
    if comando == "/help":
        respuesta = """
--- Comandos Disponibles ---
/help          Muestra esta ayuda.
/usuarios      Muestra los usuarios conectados.
--------------------------------
"""
        # (Importante) Usamos <pre> para que el HTML respete los saltos de línea
        respuesta_html = f"<pre>{respuesta}</pre>"
        enviar_mensaje_privado(conn, respuesta_html)

    # --- Comando /usuarios ---
    elif comando == "/usuarios":
        lista_usuarios = []
        with lock:
            lista_usuarios = list(clientes.values())
            
        respuesta = f"📢 Servidor: Usuarios conectados ({len(lista_usuarios)}):\n"
        for i, user in enumerate(lista_usuarios):
            respuesta += f"  {i+1}. {user}\n"
        
        # (Importante) Usamos <pre> para que el HTML respete los saltos de línea
        respuesta_html = f"<pre>{respuesta}</pre>"
        enviar_mensaje_privado(conn, respuesta_html)
        
    # --- Comando Desconocido ---
    else:
        respuesta = f"📢 Servidor: Comando '{comando}' no reconocido. Escribe /help."
        enviar_mensaje_privado(conn, respuesta)