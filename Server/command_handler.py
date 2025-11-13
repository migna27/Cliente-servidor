def enviar_mensaje_privado(conn, mensaje):
    """Envía un mensaje de vuelta solo al cliente que lo pidió."""
    try:
        conn.sendall(f"{mensaje}\n".encode("utf-8"))
    except Exception as e:
        print(f"Error enviando mensaje privado: {e}")

def procesar_comando(conn, username, msg, clientes, lock):
    """
    Procesa un comando recibido de un cliente.
    
    Argumentos:
    - conn: El socket del cliente que envió el comando.
    - username: El nombre del cliente.
    - msg: El string completo del mensaje (ej. "/usuarios").
    - clientes: El diccionario completo de clientes {conn: username}.
    - lock: El threading.Lock para acceder a 'clientes' de forma segura.
    """
    
    comando = msg.split(' ')[0] # Obtener la primera palabra (ej. "/usuarios")
    
    # --- Comando /help ---
    if comando == "/help":
        respuesta = """
--- Comandos Disponibles ---
/help          Muestra esta ayuda.
/usuarios      Muestra los usuarios conectados.
--------------------------------
"""
        enviar_mensaje_privado(conn, respuesta)

    # --- Comando /usuarios ---
    elif comando == "/usuarios":
        lista_usuarios = []
        
        # Accedemos a la lista de forma segura
        with lock:
            lista_usuarios = list(clientes.values())
            
        respuesta = "📢 Servidor: Usuarios conectados (" + str(len(lista_usuarios)) + "):\n"
        for i, user in enumerate(lista_usuarios):
            respuesta += f"  {i+1}. {user}\n"
        
        enviar_mensaje_privado(conn, respuesta)
        
    # --- Comando Desconocido ---
    else:
        respuesta = f"📢 Servidor: Comando '{comando}' no reconocido. Escribe /help para ver la lista."
        enviar_mensaje_privado(conn, respuesta)