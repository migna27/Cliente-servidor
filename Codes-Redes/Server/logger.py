import threading
from datetime import datetime
import config  

# Lock para evitar que dos hilos escriban al log al mismo tiempo
log_lock = threading.Lock()

def escribir_log(mensaje):
    """
    Escribe un mensaje (con timestamp) en el archivo de log 
    de forma segura (thread-safe).
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_con_timestamp = f"[{timestamp}] {mensaje}\n"
    
    with log_lock:
        try:
            with open(config.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(mensaje_con_timestamp)
        except Exception as e:
            print(f"Error fatal al escribir en el log: {e}")