# Las Rosas WhatsApp Bot - Backend Python

Backend FastAPI para bot de WhatsApp integrado con evolution-api. Flujos conversacionales con soporte para imágenes, documentos y ubicaciones.

## 🚀 Características

✅ **Fase 1 - Flujo Lineal (Actual)**
- Menús con opciones predefinidas
- Sistema de estados de conversación
- Soporte para adjuntos (imágenes, documentos)
- Soporte para ubicaciones
- Almacenamiento persistente de conversaciones
- API REST para integración con evolution-api

🔜 **Fase 2 - AI (Próximo)**
- Reconocimiento de intención con NLP
- Salto flexible entre opciones
- Respuestas más naturales

## 📋 Requisitos

- Python 3.12 o 3.13 recomendado
- pip

Nota: Python 3.14 todavía puede forzar compilaciones de dependencias como `pydantic-core`. Si usas 3.14, necesitas versiones recientes de esas librerías; si quieres evitar problemas, crea el entorno con 3.12 o 3.13.

## 🔧 Instalación

### 1. Crear ambiente virtual

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

Si tu `python` apunta a 3.14 y da errores al instalar dependencias, crea el entorno con una versión soportada:

```bash
py -3.13 -m venv venv
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con tus valores:
```env
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=your_api_key_here
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
```

## ▶️ Ejecutar el backend

```bash
python main.py
```

O con uvicorn directamente:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

El servidor estará disponible en: `http://localhost:8000`

## 📚 Documentación API

### Endpoints disponibles:

#### 1. Health Check
```
GET /health
```
Verifica que el servidor está funcionando.

#### 2. Recibir mensaje
```
POST /webhook/message
Content-Type: application/json

{
  "sender_jid": "5491234567890@s.whatsapp.net",
  "message_text": "1",
  "message_type": "text",
  "attachments": [],
  "location": null,
  "timestamp": "2024-05-09T10:30:00"
}
```

Respuesta:
```json
{
  "status": "processed",
  "response": {
    "sender_jid": "5491234567890@s.whatsapp.net",
    "message": "Aquí puedes consultar nuestros productos...",
    "options": [
      {
        "id": "opt1",
        "label": "1️⃣ Ver catálogo",
        "next_flow_id": "catalog"
      }
    ],
    "expects_attachment": false,
    "expects_location": false,
    "expects_free_text": true,
    "next_flow_id": "products"
  }
}
```

#### 3. Obtener estado de conversación
```
GET /conversation/{sender_jid}
```

Retorna el estado actual de la conversación del usuario.

#### 4. Reiniciar conversación
```
DELETE /conversation/{sender_jid}
```

Limpia el historial y reinicia desde el menú inicial.

#### 5. Recibir adjunto
```
POST /webhook/attachment
Content-Type: multipart/form-data

sender_jid: "5491234567890@s.whatsapp.net"
file: <archivo>
message_type: "document"
```

#### 6. Listar flujos (debug)
```
GET /flows
```

## 🔌 Integración con evolution-api

### Configurar webhook en evolution-api

En la configuración de evolution-api, añade tu webhook backend:

```json
{
  "webhook": {
    "url": "http://localhost:8000/webhook/message",
    "events": ["messages.upsert"]
  }
}
```

O si usas Docker:

```json
{
  "webhook": {
    "url": "http://host.docker.internal:8000/webhook/message",
    "events": ["messages.upsert"]
  }
}
```

### Flujo de integración:

1. **Usuario envía mensaje en WhatsApp**
2. **evolution-api recibe el mensaje**
3. **evolution-api envía POST a `/webhook/message` en tu backend**
4. **Backend procesa el flujo y retorna la respuesta**
5. **Backend instruye a evolution-api qué mensaje enviar de vuelta**

## 📁 Estructura de flujos

Los flujos están definidos en `flows.py`. Cada nodo tiene:

- `id`: Identificador único
- `name`: Nombre del nodo
- `message`: Mensaje a enviar
- `options`: Lista de opciones (menú)
- `allow_attachments`: Si permite archivos
- `allow_location`: Si permite ubicación
- `allow_free_text`: Si permite texto libre

### Ejemplo de nuevo flujo:

```python
"mi_flujo": FlowNode(
    id="mi_flujo",
    name="Mi flujo personalizado",
    message="¿Qué necesitas?",
    options=[
        FlowOption(id="opt1", label="1️⃣ Opción 1", next_flow_id="flujo_siguiente"),
        FlowOption(id="opt2", label="2️⃣ Opción 2", next_flow_id="otro_flujo"),
    ],
    allow_free_text=True,
),
```

## 💾 Almacenamiento

- **Conversaciones**: Se guardan en `./data/{sender_jid}_conversation.json`
- **Adjuntos**: Se guardan en `./data/attachments/{sender_jid}/`

## 🐳 Con Docker

```bash
docker build -t las-rosas-bot .
docker run -p 8000:8000 \
  -e EVOLUTION_API_URL=http://evolution-api:8080 \
  -e EVOLUTION_API_KEY=your_key \
  -v ./data:/app/data \
  las-rosas-bot
```

## 📊 Logs

Los logs se guardan en la consola. Para cambiar el nivel:

```bash
LOG_LEVEL=DEBUG python main.py
```

Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🔜 Próximos pasos (Fase 2 - AI)

- [ ] Integrar modelo de IA para NLP
- [ ] Reconocimiento de intención de usuario
- [ ] Salto flexible entre opciones
- [ ] Parser de documentos (OCR, PDF)
- [ ] Análisis de ubicación y rutas

## 📝 Notas

- El estado de conversación se mantiene en memoria entre requests
- Los datos persisten en archivos JSON
- Para producción, considerar usar una base de datos
- Los adjuntos se guardan localmente, considerar usar S3 para escala

## 🤝 Contribuciones

Para agregar nuevos flujos o mejoras, edita `flows.py` y `main.py`.

## 📧 Soporte

Para preguntas o problemas, revisa los logs con `LOG_LEVEL=DEBUG`.
