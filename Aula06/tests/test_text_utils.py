from app.text_utils import ai_message_to_text, normalize_text, trim_text


class FakeMessage:
    def __init__(self, content, text=None):
        self.content = content
        if text is not None:
            self.text = text


def test_normalize_text_removes_accents_and_spaces():
    assert normalize_text("  Latência e Custo  ") == "latencia e custo"


def test_trim_text_limits_size():
    assert trim_text("a" * 100, 10).endswith("…")


def test_ai_message_to_text_prefers_text_property():
    assert ai_message_to_text(FakeMessage(content=[{"text": "bloco"}], text="texto")) == "texto"


def test_ai_message_to_text_handles_block_content():
    msg = FakeMessage(content=[{"type": "text", "text": "parte 1"}, {"type": "text", "text": "parte 2"}])
    assert ai_message_to_text(msg) == "parte 1\nparte 2"
