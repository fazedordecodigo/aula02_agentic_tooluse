import importlib.util
import unittest


class OptionalLangGraphTests(unittest.TestCase):
    def test_langgraph_module_is_importable_without_langgraph_installed(self):
        # O módulo não importa langgraph no topo; build_graph() orienta a instalação se necessário.
        import porto_rag_agent.langgraph_agent as langgraph_agent
        self.assertTrue(hasattr(langgraph_agent, "build_graph"))

    @unittest.skipUnless(importlib.util.find_spec("langgraph"), "langgraph não instalado neste ambiente")
    def test_langgraph_graph_runs_when_dependency_exists(self):
        from porto_rag_agent.langgraph_agent import run_graph
        result = run_graph("O seguro auto cobre guincho?", "C001")
        self.assertIn("KB-AUTO-COBERTURA-001", result["sources"])


if __name__ == "__main__":
    unittest.main()
