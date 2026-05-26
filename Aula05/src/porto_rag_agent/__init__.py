"""Boilerplate e gabarito da Aula 5 — RAG aplicado a agentes."""

from .pure_agent import run_agent, build_default_agent
from .models import AgentState, Document, RetrievedContext

__all__ = ["run_agent", "build_default_agent", "AgentState", "Document", "RetrievedContext"]
