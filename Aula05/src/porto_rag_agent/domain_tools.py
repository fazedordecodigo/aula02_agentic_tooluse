from __future__ import annotations

from typing import Any
import re
import uuid

from .models import ToolResult
from .text_utils import normalize_text


SINISTROS: dict[str, dict[str, Any]] = {
    "SIN-1001": {
        "produto": "auto",
        "status": "vistoria agendada",
        "etapa": "aguardando vistoria",
        "previsao": "2 dias úteis",
    },
    "SIN-2002": {
        "produto": "residencial",
        "status": "em análise técnica",
        "etapa": "validação de cobertura",
        "previsao": "3 dias úteis",
    },
}

FRAUD_CASES: dict[str, dict[str, Any]] = {
    "C001": {"risk": "alto", "signals": ["login incomum", "alteração recente de e-mail"]},
    "C002": {"risk": "baixo", "signals": []},
}

SLA_BASE_HORAS = {
    ("alta", "whatsapp"): 4,
    ("alta", "telefone"): 6,
    ("alta", "email"): 8,
    ("media", "whatsapp"): 12,
    ("media", "telefone"): 16,
    ("media", "email"): 24,
    ("baixa", "whatsapp"): 24,
    ("baixa", "telefone"): 36,
    ("baixa", "email"): 48,
}


def detectar_sinistro(texto: str) -> str | None:
    match = re.search(r"\bSIN-\d{4}\b", texto.upper())
    return match.group(0) if match else None


def detectar_canal(texto: str) -> str:
    texto_norm = normalize_text(texto)
    for canal in ["whatsapp", "telefone", "email"]:
        if canal in texto_norm:
            return canal
    return "email"


def detectar_prioridade(texto: str) -> str:
    texto_norm = normalize_text(texto)
    if any(term in texto_norm for term in ["urgente", "alta", "critico", "critica", "prioridade alta"]):
        return "alta"
    if any(term in texto_norm for term in ["media", "moderado"]):
        return "media"
    return "baixa"


def consultar_status_sinistro(numero_sinistro: str) -> ToolResult:
    numero = numero_sinistro.upper()
    data = SINISTROS.get(numero)
    if not data:
        return ToolResult("consultar_status_sinistro", False, {"numero_sinistro": numero}, "Sinistro não encontrado")
    return ToolResult("consultar_status_sinistro", True, {"numero_sinistro": numero, **data})


def calcular_prazo_sla(criticidade: str, canal: str) -> ToolResult:
    crit = normalize_text(criticidade)
    chan = normalize_text(canal)
    horas = SLA_BASE_HORAS.get((crit, chan))
    if horas is None:
        return ToolResult("calcular_prazo_sla", False, {}, "Combinação de criticidade/canal não suportada")
    return ToolResult(
        "calcular_prazo_sla",
        True,
        {"criticidade": crit, "canal": chan, "sla_horas": horas, "sla_legivel": f"{horas} horas úteis"},
    )


def abrir_ticket(area: str, resumo: str, prioridade: str) -> ToolResult:
    protocolo = f"TCK-{uuid.uuid4().hex[:8].upper()}"
    return ToolResult(
        "abrir_ticket",
        True,
        {
            "ticket_criado": True,
            "protocolo": protocolo,
            "area": normalize_text(area),
            "prioridade": normalize_text(prioridade),
            "resumo": resumo.strip(),
        },
    )


def check_fraud(customer_id: str | None) -> ToolResult:
    if not customer_id:
        return ToolResult("check_fraud", False, {}, "customer_id obrigatório para triagem de fraude")
    data = FRAUD_CASES.get(customer_id, {"risk": "desconhecido", "signals": []})
    return ToolResult("check_fraud", True, data)
