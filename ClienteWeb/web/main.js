// --- Exponer funciones de JS a Python ---

// Esta función será llamada por Python (desde recibir_mensajes)
eel.expose(actualizar_chat_js);
function actualizar_chat_js(msg_data) {
    const chatArea = document.getElementById('chat-area');
    let messageHtml = '';
    const msgType = msg_data.type;

    if (msgType === "chat") {
        const prefix = msg_data.prefix || "";
        const payload = msg_data.payload || "";
        const id = msg_data.id || "msg-unknown";
        // Usamos el ID del mensaje como ID del elemento HTML
        messageHtml = `<div class="chat-message" id="${id}">${prefix}${payload}</div>`;
    } 
    else if (msgType === "delete") {
        const idToDelete = msg_data.id;
        const msgElement = document.getElementById(idToDelete);
        if (msgElement) {
            msgElement.innerHTML = ">> Mensaje eliminado por el administrador <<";
            msgElement.classList.add("deleted");
        }
        return; // No añadir más HTML
    } 
    else if (msgType === "clear") {
        chatArea.innerHTML = '<div class="chat-message server">📢 El chat fue limpiado por un administrador.</div>';
        return; // No añadir más HTML
    }

    chatArea.innerHTML += messageHtml;
    // Auto-scroll
    chatArea.scrollTop = chatArea.scrollHeight;
}

eel.expose(actualizar_status_js);
function actualizar_status_js(status, color) {
    const statusLabel = document.getElementById('status-label');
    statusLabel.innerText = status;
    statusLabel.style.color = color;
}

eel.expose(mostrar_error_js);
function mostrar_error_js(error) {
    document.getElementById('error-log').innerText = error;
}

eel.expose(conexion_exitosa_js);
function conexion_exitosa_js(username) {
    document.getElementById('conn-frame').style.display = 'none';
    document.getElementById('chat-container').style.display = 'flex'; // Mostrar chat
    actualizar_chat_js({
        type: "chat",
        id: "local-connect",
        prefix: "✅ ",
        payload: `Conectado como ${username}`
    });
}


// --- Lógica de la Interfaz (Clicks de botones) ---

window.onload = function() {
    const connButton = document.getElementById('conn-button');
    const sendButton = document.getElementById('send-button');
    const userInput = document.getElementById('user-input');
    const msgInput = document.getElementById('msg-input');

    // Conectar
    connButton.onclick = function() {
        const username = userInput.value;
        // Llama a la función de Python
        eel.conectar_py(username);
    };

    // Enviar mensaje
   connButton.onclick = function() {
        const username = userInput.value;
        // Llama a la función de Python
        eel.conectar_py(username);
    };

    // Enviar mensaje
   
   sendButton.onclick = function() { 
        const msg = msgInput.value;
        if (!msg) return;

        // --- Aplicamos la lógica del cliente Tkinter ---

        // 1. Si NO es un comando, actualiza la UI local INMEDIATAMENTE.
        if (!msg.startsWith('/')) {
            actualizar_chat_js({
                type: "chat",
                id: "local-" + Date.now(), // ID local
                prefix: "💬 Tú: ",
                payload: msg
            });
        }
        
        // 2. Limpia la caja de texto INMEDIATAMENTE.
        msgInput.value = ""; 

        // 3. Ahora, envía el mensaje al backend (sin esperar respuesta).
        eel.enviar_mensaje_py(msg); 
    };

    // Permitir enviar con 'Enter'
    msgInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            sendButton.click();
        }
    });
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            connButton.click();
        }
    });
};