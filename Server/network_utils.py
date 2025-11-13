# network_utils.py
import socket

def get_local_ip():
    """
    Encuentra la dirección IP local (LAN) de la máquina.
    
    Esto se logra creando una conexión temporal a un host externo (Google DNS)
    y viendo qué IP local utiliza el sistema operativo para esa conexión.
    """
    try:
        # No es necesario que sea '8.8.8.8', solo una IP externa
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # Si no hay conexión a internet o hay un firewall, 
        # es posible que falle y devolvamos la IP de 'localhost'.
        return "127.0.0.1"