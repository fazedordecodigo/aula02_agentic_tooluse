from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal

from activities.activity_02_openai_tool_agent import run_mock_agent, run_openai_agent
from activities.common import MEMORY_PATH, configure_environment, configure_logging, has_openai_key, normalize

logger = logging.getLogger("aula01.agent")


@dataclass
class AgentAnswer:
    status: Literal["ok", "blocked", "error"]
    summary: str
    risks: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    def validate(self) -> "AgentAnswer":
        if self.status not in {"ok", "blocked", "error"}:
            raise ValueError("status invalido")
        if len(self.summary.strip()) < 5:
            raise ValueError("summary muito curto")
        return self

    def to_json(self, indent: int | None = None) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=indent)


def is_sensitive_request(question: str) -> bool:
    blocked_terms = ["delete", "apagar", "excluir", "cancelar apolice", "alterar pagamento"]
    return any(term in normalize(question) for term in blocked_terms)


def remember(question: str, answer: str) -> None:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer_preview": answer[:300],
    }
    with MEMORY_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def build_validated_answer(raw_answer: str) -> AgentAnswer:
    risks = []
    if "erro" in normalize(raw_answer):
        risks.append("resultado_de_ferramenta_com_erro")
    return AgentAnswer(
        status="ok",
        summary=raw_answer[:600],
        risks=risks,
        next_steps=["validar com fonte oficial", "registrar trace da execucao"],
    ).validate()


def run_guarded_agent(question: str, max_steps: int = 3) -> AgentAnswer:
    logger.info("agent_start question=%s max_steps=%s", question, max_steps)

    if is_sensitive_request(question):
        logger.warning("guardrail_blocked question=%s", question)
        answer = AgentAnswer(
            status="blocked",
            summary="Solicitacao sensivel bloqueada. Exige aprovacao humana.",
            risks=["acao_sensivel"],
            next_steps=["encaminhar para operador humano"],
        ).validate()
        remember(question, answer.to_json())
        return answer

    if max_steps < 1:
        answer = AgentAnswer(status="error", summary="Limite de passos invalido.").validate()
        remember(question, answer.to_json())
        return answer

    raw = run_openai_agent(question) if has_openai_key() else run_mock_agent(question)
    try:
        answer = build_validated_answer(raw)
    except ValueError as exc:
        logger.exception("validation_error")
        answer = AgentAnswer(status="error", summary=str(exc), risks=["schema_invalido"])
        remember(question, answer.to_json())
        return answer

    remember(question, answer.to_json())
    logger.info("agent_finish status=%s risks=%s", answer.status, answer.risks)
    return answer


def main() -> None:
    configure_environment()
    configure_logging()
    question = " ".join(sys.argv[1:]) or "Resumo do cliente 42"
    print(run_guarded_agent(question).to_json(indent=2))


if __name__ == "__main__":
    main()
