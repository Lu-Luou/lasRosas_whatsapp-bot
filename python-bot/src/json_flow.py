"""Carga y validación de flujos conversacionales declarativos en JSON."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, model_validator

from config import settings


class TriggerRule(BaseModel):
    """Regla para decidir si se dispara un nodo/flujo."""

    mode: str = "llm_intent"
    prompt: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    regex: Optional[str] = None
    examples_positive: List[str] = Field(default_factory=list)
    examples_negative: List[str] = Field(default_factory=list)
    confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0)


class MenuOption(BaseModel):
    """Opción de salida para nodos de menú."""

    label: str
    next: Optional[str] = None
    action: Optional[str] = None


class FormField(BaseModel):
    """Campo de formulario en nodos tipo form."""

    name: str
    type: str = "text"
    required: bool = False
    prompt: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


class SubmitAction(BaseModel):
    """Acción a ejecutar al enviar un formulario."""

    action: Optional[str] = None
    next: Optional[str] = None


class FlowNodeDefinition(BaseModel):
    """Nodo declarativo del flujo JSON."""

    id: str
    type: str
    text: Optional[str] = None
    prompt: Optional[str] = None
    next: List[str] = Field(default_factory=list)
    options: List[MenuOption] = Field(default_factory=list)
    fields: List[FormField] = Field(default_factory=list)
    on_submit: Optional[SubmitAction] = None
    action: Optional[str] = None
    trigger: Optional[TriggerRule] = None
    guardrails: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = {
        "extra": "allow",
        "populate_by_name": True,
    }


class JsonFlowDefinition(BaseModel):
    """Documento completo del flujo conversacional."""

    flow_id: str
    start_node: str
    nodes: List[FlowNodeDefinition]
    version: str = "1.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "extra": "allow",
    }

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data: Any) -> Any:
        """Normaliza campos legacy para mantener compatibilidad."""
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        normalized_nodes = []

        for node in normalized.get("nodes", []):
            if not isinstance(node, dict):
                normalized_nodes.append(node)
                continue

            normalized_node = dict(node)

            # Legacy: actionAI -> trigger (se toma la primera regla)
            action_ai = normalized_node.pop("actionAI", None)
            if action_ai and not normalized_node.get("trigger"):
                first_rule = action_ai[0] if isinstance(action_ai, list) and action_ai else None
                if isinstance(first_rule, dict):
                    normalized_node["trigger"] = {
                        "mode": "llm_intent",
                        "prompt": first_rule.get("prompt"),
                    }

            normalized_nodes.append(normalized_node)

        normalized["nodes"] = normalized_nodes
        return normalized

    @model_validator(mode="after")
    def validate_graph(self) -> "JsonFlowDefinition":
        """Valida integridad básica del grafo de nodos."""
        node_ids = [node.id for node in self.nodes]
        unique_ids = set(node_ids)

        if len(unique_ids) != len(node_ids):
            raise ValueError("Hay nodos con id duplicado en bot_flow.json")

        if self.start_node not in unique_ids:
            raise ValueError("start_node no existe en la lista de nodes")

        for node in self.nodes:
            for target in node.next:
                if target not in unique_ids:
                    raise ValueError(f"El nodo '{node.id}' apunta a next inválido: '{target}'")

            for option in node.options:
                if option.next and option.next not in unique_ids:
                    raise ValueError(
                        f"La opción '{option.label}' del nodo '{node.id}' apunta a '{option.next}' inexistente"
                    )

            if node.on_submit and node.on_submit.next and node.on_submit.next not in unique_ids:
                raise ValueError(
                    f"on_submit del nodo '{node.id}' apunta a '{node.on_submit.next}' inexistente"
                )

        return self


class JsonFlowService:
    """Servicio para cargar/consultar el flujo declarativo."""

    def __init__(self, flow_path: Path):
        self.flow_path = flow_path
        self._flow: Optional[JsonFlowDefinition] = None

    def load(self) -> JsonFlowDefinition:
        raw_data = self.flow_path.read_text(encoding="utf-8")
        self._flow = JsonFlowDefinition.model_validate_json(raw_data)
        return self._flow

    def reload(self) -> JsonFlowDefinition:
        return self.load()

    def get(self) -> Optional[JsonFlowDefinition]:
        return self._flow

    def summary(self) -> Dict[str, Any]:
        if not self._flow:
            return {
                "loaded": False,
                "path": str(self.flow_path),
            }

        nodes_by_type: Dict[str, int] = {}
        for node in self._flow.nodes:
            nodes_by_type[node.type] = nodes_by_type.get(node.type, 0) + 1

        return {
            "loaded": True,
            "path": str(self.flow_path),
            "flow_id": self._flow.flow_id,
            "start_node": self._flow.start_node,
            "version": self._flow.version,
            "nodes_count": len(self._flow.nodes),
            "nodes_by_type": nodes_by_type,
        }


json_flow_service = JsonFlowService(settings.flow_json_file)


def load_json_flow_or_raise() -> JsonFlowDefinition:
    """Carga flujo JSON y entrega un error amigable si falla."""
    try:
        return json_flow_service.load()
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"No se encontró el archivo de flujo JSON: {json_flow_service.flow_path}"
        ) from exc
    except ValidationError as exc:
        raise RuntimeError(f"bot_flow.json inválido: {exc}") from exc
