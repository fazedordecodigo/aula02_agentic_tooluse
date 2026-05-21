from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field


@dataclass
class AgentBlueprint:
    problema: str
    objetivo: str
    fontes: list[str]
    ferramentas: list[str] = field(default_factory=list)
    fluxo: list[str] = field(default_factory=list)
    riscos: list[str] = field(default_factory=list)
    qualidade: list[str] = field(default_factory=list)
    observabilidade: list[str] = field(default_factory=list)


def create_blueprint(problema: str, objetivo: str, fontes: list[str]) -> AgentBlueprint:
    tools = [f"consultar_{fonte}" for fonte in fontes]
    return AgentBlueprint(
        problema=problema,
        objetivo=objetivo,
        fontes=fontes,
        ferramentas=tools + ["validar_consistencia", "gerar_resumo_executivo"],
        fluxo=[
            "interpretar_intencao",
            "selecionar_ferramentas",
            "consultar_fontes",
            "consolidar_resultados",
            "validar_consistencia",
            "responder_com_insights",
        ],
        riscos=[
            "hallucination_por_contexto_insuficiente",
            "dados_desatualizados",
            "exposicao_de_informacao_sensivel",
            "custo_por_excesso_de_chamadas",
        ],
        qualidade=[
            "resposta_deve_citar_fontes_consultadas",
            "acoes_sensiveis_exigem_human_in_the_loop",
            "limite_maximo_de_passos",
            "saida_validada_por_schema",
        ],
        observabilidade=[
            "log_por_tool_call",
            "correlation_id_por_solicitacao",
            "metrica_de_latencia",
            "metrica_de_custo_estimado",
            "taxa_de_bloqueio_por_guardrail",
        ],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--problema", required=True)
    parser.add_argument("--objetivo", required=True)
    parser.add_argument("--fonte", action="append", default=[])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    blueprint = create_blueprint(args.problema, args.objetivo, args.fonte)
    print(json.dumps(asdict(blueprint), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
