"""Command line demo for Aula 4 guardrails agent."""

from __future__ import annotations

import argparse

from aula04_guardrails_agent.facade import GuardrailsAgentFacade


def main() -> None:
    parser = argparse.ArgumentParser(description="Aula 4 guardrails agent demo")
    parser.add_argument(
        "question",
        nargs="?",
        default="Explique prompt injection e gere um checklist de risco alto.",
    )
    parser.add_argument("--model", default=None, help="Google Gemini model name")
    args = parser.parse_args()

    agent = GuardrailsAgentFacade.with_google(model_name=args.model)
    result = agent.ask(args.question)
    print(result.to_json())


if __name__ == "__main__":
    main()
