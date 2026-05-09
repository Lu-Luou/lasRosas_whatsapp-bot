"""Definición de flujos conversacionales"""

from models import FlowNode, FlowOption


# Definir los nodos del flujo
FLOW_NODES = {
    "start": FlowNode(
        id="start",
        name="Bienvenida",
        message="¡Hola! Bienvenido a Las Rosas. ¿Cómo podemos ayudarte?",
        options=[
            FlowOption(id="opt1", label="1️⃣ Consulta sobre productos", next_flow_id="products"),
            FlowOption(id="opt2", label="2️⃣ Realizar un pedido", next_flow_id="order"),
            FlowOption(id="opt3", label="3️⃣ Seguimiento de pedido", next_flow_id="tracking"),
            FlowOption(id="opt4", label="4️⃣ Hablar con un agente", next_flow_id="agent"),
        ],
        allow_free_text=False,
    ),
    
    "products": FlowNode(
        id="products",
        name="Consulta de productos",
        message="Aquí puedes consultar nuestros productos. ¿Qué te interesa?",
        options=[
            FlowOption(id="opt1", label="1️⃣ Ver catálogo", next_flow_id="catalog"),
            FlowOption(id="opt2", label="2️⃣ Disponibilidad", next_flow_id="availability"),
            FlowOption(id="opt3", label="3️⃣ Volver al menú", next_flow_id="start"),
        ],
        allow_free_text=True,
    ),
    
    "order": FlowNode(
        id="order",
        name="Realizar pedido",
        message="¿Cuál es tu ubicación para calcular envío?",
        options=[
            FlowOption(id="opt1", label="1️⃣ Enviar ubicación", next_flow_id="order_location"),
            FlowOption(id="opt2", label="2️⃣ Volver al menú", next_flow_id="start"),
        ],
        allow_location=True,
    ),
    
    "order_location": FlowNode(
        id="order_location",
        name="Confirmación de ubicación",
        message="Gracias por tu ubicación. Ahora, ¿qué deseas pedir? Describe tus productos.",
        options=[
            FlowOption(id="opt1", label="1️⃣ Continuar", next_flow_id="order_items"),
        ],
        allow_attachments=True,
        allow_free_text=True,
    ),
    
    "order_items": FlowNode(
        id="order_items",
        name="Detalles del pedido",
        message="Tu pedido ha sido recibido. ¿Necesitas algo más?",
        options=[
            FlowOption(id="opt1", label="1️⃣ Nuevo pedido", next_flow_id="order"),
            FlowOption(id="opt2", label="2️⃣ Volver al menú", next_flow_id="start"),
        ],
        allow_free_text=True,
    ),
    
    "tracking": FlowNode(
        id="tracking",
        name="Seguimiento de pedido",
        message="Para rastrear tu pedido, ingresa tu número de orden.",
        options=[
            FlowOption(id="opt1", label="1️⃣ Volver al menú", next_flow_id="start"),
        ],
        allow_free_text=True,
    ),
    
    "catalog": FlowNode(
        id="catalog",
        name="Catálogo de productos",
        message="📦 Catálogo disponible. Consulta nuestros productos.",
        options=[
            FlowOption(id="opt1", label="1️⃣ Volver", next_flow_id="products"),
        ],
        allow_free_text=True,
    ),
    
    "availability": FlowNode(
        id="availability",
        name="Verificar disponibilidad",
        message="¿Cuál es el producto que deseas verificar?",
        options=[
            FlowOption(id="opt1", label="1️⃣ Volver", next_flow_id="products"),
        ],
        allow_free_text=True,
    ),
    
    "agent": FlowNode(
        id="agent",
        name="Hablar con agente",
        message="Un agente se pondrá en contacto contigo pronto. ¿Algún comentario?",
        options=[
            FlowOption(id="opt1", label="1️⃣ Volver al menú", next_flow_id="start"),
        ],
        allow_attachments=True,
        allow_free_text=True,
    ),
}


def get_flow_node(node_id: str) -> FlowNode | None:
    """Obtiene un nodo del flujo por su ID"""
    return FLOW_NODES.get(node_id)


def get_initial_flow() -> FlowNode:
    """Retorna el nodo inicial del flujo"""
    return FLOW_NODES["start"]
