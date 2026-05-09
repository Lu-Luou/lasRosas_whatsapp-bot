"""
Script de prueba para el backend del bot
"""

import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


def test_health():
    """Probar que el servidor está activo"""
    print("🔍 Probando health check...")
    response = httpx.get(f"{BASE_URL}/health")
    print(f"✅ Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()


def test_list_flows():
    """Listar todos los flujos disponibles"""
    print("🔍 Listando flujos disponibles...")
    response = httpx.get(f"{BASE_URL}/flows")
    print(f"✅ Status: {response.status_code}")
    flows = response.json()
    for flow in flows["flows"]:
        print(f"  - {flow['id']}: {flow['name']} ({flow['options_count']} opciones)")
    print()


def test_send_message(sender_jid: str, message_text: str):
    """Enviar un mensaje de prueba"""
    print(f"📨 Enviando mensaje: '{message_text}' desde {sender_jid}...")
    
    payload = {
        "sender_jid": sender_jid,
        "message_text": message_text,
        "message_type": "text",
        "attachments": [],
        "location": None,
        "timestamp": datetime.now().isoformat()
    }
    
    response = httpx.post(f"{BASE_URL}/webhook/message", json=payload)
    print(f"✅ Status: {response.status_code}")
    data = response.json()
    
    if "response" in data:
        bot_response = data["response"]
        print(f"\n📲 Respuesta del bot:")
        print(f"Mensaje: {bot_response['message']}")
        if bot_response["options"]:
            print(f"Opciones:")
            for opt in bot_response["options"]:
                print(f"  {opt['label']}")
    print()


def test_get_conversation(sender_jid: str):
    """Obtener el estado de una conversación"""
    print(f"🔍 Obteniendo conversación de {sender_jid}...")
    response = httpx.get(f"{BASE_URL}/conversation/{sender_jid}")
    
    if response.status_code == 200:
        print(f"✅ Status: {response.status_code}")
        data = response.json()["conversation"]
        print(f"Flow actual: {data['current_flow_id']}")
        print(f"Nodo actual: {data['current_node_id']}")
        print(f"Adjuntos recibidos: {len(data['attachments_collected'])}")
        print(f"Metadata: {data['metadata']}")
    else:
        print(f"❌ Status: {response.status_code}")
    print()


def test_reset_conversation(sender_jid: str):
    """Reiniciar una conversación"""
    print(f"🔄 Reiniciando conversación de {sender_jid}...")
    response = httpx.delete(f"{BASE_URL}/conversation/{sender_jid}")
    print(f"✅ Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()


def test_full_flow():
    """Probar un flujo completo de conversación"""
    print("\n" + "="*60)
    print("🤖 PRUEBA DE FLUJO COMPLETO")
    print("="*60 + "\n")
    
    sender_jid = "5491234567890@s.whatsapp.net"
    
    # 1. Iniciar conversación
    print("1️⃣ Iniciando conversación...")
    test_send_message(sender_jid, "Hola")
    
    # 2. Seleccionar opción 1 (Consulta sobre productos)
    print("2️⃣ Seleccionando opción 1...")
    test_send_message(sender_jid, "1")
    
    # 3. Seleccionar opción 2 (Disponibilidad)
    print("3️⃣ Seleccionando opción 2...")
    test_send_message(sender_jid, "2")
    
    # 4. Escribir consulta libre
    print("4️⃣ Enviando consulta libre...")
    test_send_message(sender_jid, "¿Tienen rosas rojas?")
    
    # 5. Ver estado final
    print("5️⃣ Estado final de la conversación:")
    test_get_conversation(sender_jid)
    
    # 6. Reiniciar
    print("6️⃣ Reiniciando para la próxima prueba...")
    test_reset_conversation(sender_jid)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBAS DEL BACKEND LAS ROSAS BOT")
    print("="*60 + "\n")
    
    try:
        # Pruebas básicas
        test_health()
        test_list_flows()
        
        # Prueba de flujo completo
        test_full_flow()
        
        print("\n✅ ¡Todas las pruebas completadas!")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        print("Asegúrate de que el servidor está corriendo en http://localhost:8000")
