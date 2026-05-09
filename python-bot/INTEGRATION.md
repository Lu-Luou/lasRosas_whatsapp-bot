# Guía de Integración con evolution-api

## 🔗 Configuración del webhook en evolution-api

Tu backend Python está listo para recibir mensajes de evolution-api. Aquí te muestro cómo configurarlo.

### Opción 1: Configuración vía API de evolution-api

Envía un POST a tu instancia de evolution-api:

```bash
curl -X POST http://localhost:8080/webhooks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "url": "http://localhost:8000/webhook/message",
    "events": [
      "messages.upsert"
    ],
    "webhook_by_events": true,
    "webhook_by_api": true,
    "api_mode": true,
    "instance": "your_instance_name"
  }'
```

### Opción 2: Configuración en docker-compose

Si usas Docker Compose para evolution-api, añade el webhook:

```yaml
services:
  evolution-api:
    image: evolution-api:latest
    environment:
      - WEBHOOK_URL=http://bot-backend:8000/webhook/message
      - WEBHOOK_EVENTS=messages.upsert
      - API_MODE=true
```

### Opción 3: Configuración vía archivo env

En el `.env` de evolution-api:

```env
WEBHOOK_URL=http://localhost:8000/webhook/message
WEBHOOK_EVENTS=messages.upsert
WEBHOOK_ENABLE=true
```

## 📨 Estructura del mensaje que evolution-api enviará

Cuando un usuario envíe un mensaje en WhatsApp, evolution-api lo reenviará a tu backend así:

```json
{
  "sender_jid": "5491234567890@s.whatsapp.net",
  "message_text": "1",
  "message_type": "text",
  "attachments": [],
  "location": null,
  "timestamp": "2024-05-09T10:30:00.000000"
}
```

## ✅ Respuesta esperada del backend

Tu backend responderá con:

```json
{
  "status": "processed",
  "response": {
    "sender_jid": "5491234567890@s.whatsapp.net",
    "message": "¿Cómo podemos ayudarte?",
    "options": [
      {
        "id": "opt1",
        "label": "1️⃣ Consulta sobre productos",
        "next_flow_id": "products"
      }
    ],
    "expects_attachment": false,
    "expects_location": false,
    "expects_free_text": false,
    "next_flow_id": "start"
  }
}
```

## 🔄 Flujo completo de integración

```
┌─────────────────────────────────────────────────────────────┐
│  1. Usuario envía mensaje en WhatsApp                       │
│     "Hola, quiero hacer un pedido"                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. evolution-api recibe el mensaje                         │
│     Valida que es de WhatsApp                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. evolution-api POST a tu backend                         │
│     POST /webhook/message                                   │
│     + sender_jid: "5491234567890@s.whatsapp.net"            │
│     + message_text: "Hola, quiero hacer un pedido"          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Backend procesa el mensaje                              │
│     - Crea/obtiene estado de conversación                   │
│     - Ejecuta la lógica del flujo                           │
│     - Prepara la respuesta                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Backend devuelve respuesta                              │
│     Status 200 OK                                           │
│     + message: "¿Cuál es tu ubicación para envío?"          │
│     + expects_location: true                                │
│     + options: []                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  6. evolution-api envía la respuesta al usuario             │
│     El usuario recibe en WhatsApp el mensaje                │
│     Y la solicitud de ubicación                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Seguridad

### Token de API

Asegúrate de proteger tu backend con un token. Puedes usar:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    if credentials.credentials != settings.evolution_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication credentials"
        )
    return credentials.credentials

@app.post("/webhook/message")
async def receive_message(message: Message, token: str = Depends(verify_token)):
    # Procesar mensaje
    ...
```

### HTTPS en producción

Para producción, usa HTTPS y verifica certificados SSL.

## 🧪 Pruebas

### Test 1: Health check

```bash
curl http://localhost:8000/health
```

Respuesta:
```json
{
  "status": "healthy",
  "timestamp": "2024-05-09T10:30:00.123456",
  "service": "Las Rosas WhatsApp Bot"
}
```

### Test 2: Enviar mensaje de prueba

```bash
curl -X POST http://localhost:8000/webhook/message \
  -H "Content-Type: application/json" \
  -d '{
    "sender_jid": "5491234567890@s.whatsapp.net",
    "message_text": "1",
    "message_type": "text",
    "attachments": [],
    "location": null,
    "timestamp": "2024-05-09T10:30:00"
  }'
```

### Test 3: Usar script de pruebas

```bash
python test_api.py
```

## 🐛 Debugging

### Logs en tiempo real

```bash
LOG_LEVEL=DEBUG python main.py
```

### Ver conversación guardada

```bash
cat data/5491234567890@s.whatsapp.net_conversation.json
```

### Ver adjuntos

```bash
ls -la data/attachments/5491234567890@s.whatsapp.net/
```

## 🔗 Webhook eventos que evolution-api puede enviar

```
- messages.upsert       # Nuevo mensaje
- messages.update       # Mensaje actualizado
- messages.delete       # Mensaje eliminado
- connection.update     # Cambio de conexión
- presence.update       # Actualización de presencia
- status.instance       # Estado de instancia
- status.connection     # Estado de conexión
```

Para recibir más eventos, configura múltiples webhooks:

```bash
curl -X POST http://localhost:8080/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8000/webhook",
    "events": ["messages.upsert", "messages.update", "presence.update"]
  }'
```

## 📝 Notas importantes

1. **Timeouts**: El backend debe responder en menos de 30 segundos
2. **Encoding**: evolution-api envía UTF-8, asegúrate de manejarlo
3. **Rate limiting**: Para alta carga, implementa colas con Redis/RabbitMQ
4. **Retries**: evolution-api reintentará si recibe error 5xx
5. **IDs únicos**: El `sender_jid` incluye el dominio (`@s.whatsapp.net`)

## 🔄 Próximas integraciones

Cuando agregues AI (Fase 2), necesitarás:

1. **LLM API** (OpenAI, Claude, Llama, etc.)
   - Para reconocer intención del usuario
   - Para generar respuestas más naturales

2. **Storage mejorado**
   - Base de datos (PostgreSQL, MongoDB)
   - Cache (Redis)

3. **Message queue**
   - Para procesar mensajes en background
   - Para alta concurrencia

Te guiamos cuando llegues a esa fase.
