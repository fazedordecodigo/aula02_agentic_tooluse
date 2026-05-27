import pytest


def test_langgraph_runtime_optional_imports_are_available_when_installed():
    pytest.importorskip("langgraph")
    pytest.importorskip("langchain_core")
