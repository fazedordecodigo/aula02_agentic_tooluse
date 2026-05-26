import unittest

from porto_rag_agent.pure_agent import run_agent
from porto_rag_agent.vector_store import SimpleVectorStore
from porto_rag_agent.knowledge_base import build_knowledge_base


class RetrievalTests(unittest.TestCase):
    def test_retrieve_sla_whatsapp(self):
        store = SimpleVectorStore(build_knowledge_base())
        ctx = store.retrieve("matriz SLA alta whatsapp sinistro", domain="sla", k=2)
        self.assertGreaterEqual(len(ctx.documents), 1)
        self.assertIn("KB-SLA-001", [doc.metadata["source_id"] for doc in ctx.documents])
        self.assertIn("4 horas úteis", ctx.serialized_context)

    def test_retrieve_returns_metadata_artifacts(self):
        store = SimpleVectorStore(build_knowledge_base())
        ctx = store.retrieve("cobertura seguro auto guincho", domain="apolice", k=2)
        self.assertGreaterEqual(len(ctx.documents), 1)
        self.assertIn("source_id", ctx.documents[0].metadata)


class AgentTests(unittest.TestCase):
    def test_incrementa_exercicio_anterior_com_rag(self):
        state = run_agent(
            "Qual o status do sinistro SIN-1001? Calcule o SLA urgente via whatsapp e abrir ticket.",
            customer_id="C001",
        )
        self.assertFalse(state.blocked)
        self.assertEqual(state.route, "sinistro_rag")
        self.assertIn("SIN-1001", state.final_answer)
        self.assertIn("4 horas úteis", state.final_answer)
        self.assertIn("Ticket criado", state.final_answer)
        self.assertGreaterEqual(len(state.sources), 1)
        self.assertIn("KB-SINISTRO-1001", state.sources)

    def test_apolice_rag_cobertura_guincho(self):
        state = run_agent("O seguro auto cobre guincho?", customer_id="C001")
        self.assertFalse(state.blocked)
        self.assertEqual(state.route, "apolice_rag")
        self.assertIn("KB-AUTO-COBERTURA-001", state.sources)
        self.assertIn("guincho", state.final_answer.lower())

    def test_fraude_sem_customer_id_escala(self):
        state = run_agent("Suspeita de fraude: login incomum na conta")
        self.assertEqual(state.route, "fraude_rag")
        self.assertTrue(state.needs_human)
        self.assertIn("Protocolo", state.final_answer)

    def test_fraude_com_customer_id_responde(self):
        state = run_agent("Suspeita de fraude: login incomum na conta", customer_id="C001")
        self.assertFalse(state.needs_human)
        self.assertIn("risco alto", state.final_answer.lower())
        self.assertIn("KB-FRAUDE-001", state.sources)

    def test_guardrail_bloqueia_dados_sensiveis(self):
        state = run_agent("Quero saber o CPF do cliente do sinistro SIN-1001", customer_id="C001")
        self.assertTrue(state.blocked)
        self.assertEqual(state.route, "bloqueado")
        self.assertEqual(state.sources, [])
        self.assertIn("dado sensível", state.final_answer)


if __name__ == "__main__":
    unittest.main()
