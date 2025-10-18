const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Estado de las conexiones (por usuario)
const clients = new Map();
const qrCodes = new Map();
const connectionStatus = new Map();

// Directorio para sesiones
const SESSION_DIR = path.join(__dirname, '.wwebjs_auth');
if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
}

// Función para crear cliente de WhatsApp
function createClient(userId) {
    console.log(`[${userId}] Creando nuevo cliente WhatsApp...`);
    
    const client = new Client({
        authStrategy: new LocalAuth({
            clientId: `user_${userId}`,
            dataPath: SESSION_DIR
        }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        }
    });

    // Evento: QR Code generado
    client.on('qr', (qr) => {
        console.log(`[${userId}] QR Code generado`);
        qrCodes.set(userId, qr);
        connectionStatus.set(userId, 'qr_pending');
        
        // Mostrar QR en terminal
        qrcode.generate(qr, { small: true });
    });

    // Evento: Cliente listo
    client.on('ready', () => {
        console.log(`[${userId}] Cliente WhatsApp conectado!`);
        connectionStatus.set(userId, 'connected');
        qrCodes.delete(userId);
    });

    // Evento: Cliente autenticado
    client.on('authenticated', () => {
        console.log(`[${userId}] Autenticado exitosamente`);
        connectionStatus.set(userId, 'connecting');
    });

    // Evento: Error de autenticación
    client.on('auth_failure', (msg) => {
        console.error(`[${userId}] Error de autenticación:`, msg);
        connectionStatus.set(userId, 'error');
        qrCodes.delete(userId);
    });

    // Evento: Cliente desconectado
    client.on('disconnected', (reason) => {
        console.log(`[${userId}] Cliente desconectado:`, reason);
        connectionStatus.set(userId, 'disconnected');
        clients.delete(userId);
        qrCodes.delete(userId);
    });

    // Evento: Mensaje recibido
    client.on('message', async (message) => {
        console.log(`[${userId}] Mensaje recibido de ${message.from}: ${message.body}`);
        
        // Enviar mensaje a Django para procesar
        try {
            const response = await fetch('http://localhost:8000/api/whatsapp/message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    from: message.from,
                    body: message.body,
                    timestamp: message.timestamp,
                    message_id: message.id._serialized
                })
            });
            
            const data = await response.json();
            
            // Si Django devuelve una respuesta automática, enviarla
            if (data.auto_reply) {
                await message.reply(data.auto_reply);
                console.log(`[${userId}] Respuesta automática enviada: ${data.auto_reply}`);
            }
        } catch (error) {
            console.error(`[${userId}] Error al procesar mensaje:`, error);
        }
    });

    return client;
}

// ==================== ENDPOINTS API ====================

// Estado del servidor
app.get('/health', (req, res) => {
    res.json({
        status: 'running',
        active_connections: clients.size,
        uptime: process.uptime()
    });
});

// Iniciar conexión de WhatsApp
app.post('/connect', async (req, res) => {
    const { user_id } = req.body;
    
    if (!user_id) {
        return res.status(400).json({ error: 'user_id es requerido' });
    }

    try {
        // Si ya existe un cliente, verificar su estado
        if (clients.has(user_id)) {
            const status = connectionStatus.get(user_id) || 'unknown';
            const qr = qrCodes.get(user_id);
            
            console.log(`[${user_id}] Cliente ya existe con estado: ${status}`);
            
            // Si ya está conectado, retornar estado actual
            if (status === 'connected') {
                return res.json({
                    status: 'connected',
                    message: 'Ya estás conectado a WhatsApp',
                    already_connected: true
                });
            }
            
            // Si está esperando QR, retornar el QR actual
            if (status === 'qr_pending' && qr) {
                return res.json({
                    status: 'qr_pending',
                    qr: qr,
                    message: 'Escanea el código QR para conectar',
                    already_connecting: true
                });
            }
            
            // Si está en cualquier otro estado, retornar info
            return res.json({
                status: status,
                qr: qr,
                message: `Cliente existente en estado: ${status}`,
                already_exists: true
            });
        }

        // Crear nuevo cliente
        console.log(`[${user_id}] Creando nuevo cliente WhatsApp`);
        const client = createClient(user_id);
        clients.set(user_id, client);
        connectionStatus.set(user_id, 'connecting');

        // Inicializar cliente
        await client.initialize();

        res.json({
            status: 'connecting',
            message: 'Cliente inicializado, generando QR...'
        });

    } catch (error) {
        console.error(`[${user_id}] Error al conectar:`, error);
        connectionStatus.set(user_id, 'error');
        res.status(500).json({
            error: 'Error al inicializar WhatsApp',
            details: error.message
        });
    }
});

// Obtener estado de conexión
app.get('/status/:user_id', (req, res) => {
    const { user_id } = req.params;
    
    const status = connectionStatus.get(user_id) || 'disconnected';
    const qr = qrCodes.get(user_id);
    
    res.json({
        status: status,
        qr: qr,
        has_client: clients.has(user_id)
    });
});

// Desconectar cliente
app.post('/disconnect', async (req, res) => {
    const { user_id } = req.body;
    
    if (!user_id) {
        return res.status(400).json({ error: 'user_id es requerido' });
    }

    try {
        const client = clients.get(user_id);
        
        if (client) {
            await client.destroy();
            clients.delete(user_id);
            connectionStatus.delete(user_id);
            qrCodes.delete(user_id);
            
            res.json({
                message: 'Cliente desconectado exitosamente'
            });
        } else {
            res.json({
                message: 'Cliente no encontrado'
            });
        }
    } catch (error) {
        console.error(`Error al desconectar usuario ${user_id}:`, error);
        res.status(500).json({
            error: 'Error al desconectar',
            details: error.message
        });
    }
});

// Enviar mensaje
app.post('/send', async (req, res) => {
    const { user_id, to, message } = req.body;
    
    if (!user_id || !to || !message) {
        return res.status(400).json({
            error: 'user_id, to y message son requeridos'
        });
    }

    try {
        const client = clients.get(user_id);
        
        if (!client) {
            return res.status(404).json({
                error: 'Cliente no encontrado o no conectado'
            });
        }

        const status = connectionStatus.get(user_id);
        if (status !== 'connected') {
            return res.status(400).json({
                error: 'Cliente no está conectado',
                status: status
            });
        }

        // Formatear número de teléfono si es necesario
        let chatId = to;
        if (!to.includes('@')) {
            chatId = to.includes('-') ? `${to}@g.us` : `${to}@c.us`;
        }

        // Enviar mensaje
        await client.sendMessage(chatId, message);
        
        res.json({
            success: true,
            message: 'Mensaje enviado exitosamente'
        });

    } catch (error) {
        console.error(`Error al enviar mensaje para usuario ${user_id}:`, error);
        res.status(500).json({
            error: 'Error al enviar mensaje',
            details: error.message
        });
    }
});

// Obtener información del usuario conectado
app.get('/info/:user_id', async (req, res) => {
    const { user_id } = req.params;
    
    try {
        const client = clients.get(user_id);
        
        if (!client) {
            return res.status(404).json({
                error: 'Cliente no encontrado'
            });
        }

        const status = connectionStatus.get(user_id);
        if (status !== 'connected') {
            return res.json({
                status: status,
                info: null
            });
        }

        const info = client.info;
        
        res.json({
            status: 'connected',
            info: {
                phone: info.wid.user,
                name: info.pushname,
                platform: info.platform
            }
        });

    } catch (error) {
        console.error(`Error al obtener info del usuario ${user_id}:`, error);
        res.status(500).json({
            error: 'Error al obtener información',
            details: error.message
        });
    }
});

// Iniciar servidor
app.listen(PORT, () => {
    console.log(`✅ Servidor WhatsApp corriendo en http://localhost:${PORT}`);
    console.log(`📱 Listo para recibir conexiones de WhatsApp`);
});

// Manejo de errores no capturados
process.on('unhandledRejection', (error) => {
    console.error('Error no manejado:', error);
});

process.on('uncaughtException', (error) => {
    console.error('Excepción no capturada:', error);
});
