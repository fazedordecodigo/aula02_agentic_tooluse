import unittest

from src.mini_agent_porto import (
    ToolCall,
    ToolDefinition,
    ToolExecutor,
    abrir_ticket,
    build_agent,
    calcular_prazo_sla,
    consultar_cobertura_produto,
    consultar_franquia,
    consultar_status_sinistro,
)


class ToolTests(unittest.TestCase):
    def test_consultar_status_sinistro_encontrado(self):
        result = consultar_status_sinistro("sin-1001")
        self.assertTrue(result["encontrado"])
        self.assertEqual(result["numero_sinistro"], "SIN-1001")
        self.assertEqual(result["produto"], "auto")

    def test_consultar_cobertura_auto(self):
        result = consultar_cobertura_produto("auto")
        self.assertTrue(result["encontrado"])
        self.assertIn("guincho", result["coberturas"])

    def test_consultar_franquia_auto(self):
        result = consultar_franquia("auto")
        self.assertTrue(result["encontrado"])
        self.assertEqual(result["valor_referencia"], 1500.00)

    def test_calcular_prazo_sla(self):
        result = calcular_prazo_sla("alta", "whatsapp")
        self.assertTrue(result["calculado"])
        self.assertEqual(result["sla_horas"], 4)

    def test_abrir_ticket(self):
        result = abrir_ticket("Sinistros", "Teste", "Alta")
        self.assertTrue(result["ticket_criado"])
        self.assertRegex(result["protocolo"], r"^TCK-[A-F0-9]{8}$")


class ExecutorTests(unittest.TestCase):
    def test_executor_bloqueia_ferramenta_fora_da_allowlist(self):
        executor = ToolExecutor([])
        result = executor.execute(ToolCall("apagar_banco", {}))
        self.assertFalse(result.ok)
        self.assertEqual(result.error, "Ferramenta não permitida.")

    def test_executor_valida_argumentos_obrigatorios(self):
        executor = ToolExecutor(
            [
                ToolDefinition(
                    name="consultar_status_sinistro",
                    description="Consulta sinistro",
                    required_args=("numero_sinistro",),
                    handler=consultar_status_sinistro,
                )
            ]
        )
        result = executor.execute(ToolCall("consultar_status_sinistro", {}))
        self.assertFalse(result.ok)
        self.assertIn("Argumentos obrigatórios ausentes", result.error)


class AgentTests(unittest.TestCase):
    def test_agente_executa_fluxo_multistep(self):
        agent = build_agent()
        trace = agent.run("Qual o status do sinistro SIN-1001? Calcule SLA urgente via whatsapp e abrir ticket.")
        self.assertFalse(trace.blocked)
        self.assertEqual([call.name for call in trace.planned_calls], [
            "consultar_status_sinistro",
            "calcular_prazo_sla",
            "abrir_ticket",
        ])
        self.assertEqual(len(trace.tool_results), 3)
        self.assertIn("Sinistro SIN-1001", trace.final_answer)
        self.assertIn("SLA estimado: 4 horas úteis", trace.final_answer)
        self.assertIn("Ticket criado", trace.final_answer)

    def test_agente_usa_ferramenta_de_cobertura(self):
        agent = build_agent()
        trace = agent.run("O seguro auto cobre guincho?")
        self.assertFalse(trace.blocked)
        self.assertEqual(len(trace.planned_calls), 1)
        self.assertEqual(trace.planned_calls[0].name, "consultar_cobertura_produto")
        self.assertIn("guincho", trace.final_answer)

    def test_agente_usa_ferramenta_de_franquia(self):
        agent = build_agent()
        trace = agent.run("Qual a franquia do seguro auto?")
        self.assertFalse(trace.blocked)
        self.assertEqual(len(trace.planned_calls), 1)
        self.assertEqual(trace.planned_calls[0].name, "consultar_franquia")
        self.assertIn("Franquia de referência", trace.final_answer)

    def test_agente_bloqueia_dado_sensivel(self):
        agent = build_agent()
        trace = agent.run("Quero saber o CPF do cliente do sinistro SIN-1001")
        self.assertTrue(trace.blocked)
        self.assertEqual(trace.planned_calls, [])
        self.assertIn("dado sensível", trace.final_answer)

    def test_agente_sem_intencao_de_tool(self):
        agent = build_agent()
        trace = agent.run("Bom dia")
        self.assertFalse(trace.blocked)
        self.assertEqual(trace.planned_calls, [])
        self.assertIn("Não identifiquei uma ação segura", trace.final_answer)


if __name__ == "__main__":
    unittest.main()
