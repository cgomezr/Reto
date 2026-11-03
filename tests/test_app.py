from pathlib import Path
import json
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest


def test_demo_and_currency_switch():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    app.run(timeout=30)
    assert not app.exception
    app.toggle[0].set_value(False).run()
    app.button[1].click().run(timeout=30)
    assert not app.exception
    assert len(app.session_state["lines"]) == 5
    assert app.metric[3].value == "25,000.00"
    app.selectbox(key="summary_currency").select("USD").run()
    assert not app.exception
    assert app.metric[3].value == "40.00"
    # Simula la edición que el navegador envía al widget de Streamlit.
    editor = f'editor_{app.session_state["version"]}'
    app.session_state[editor] = {"edited_rows": {0: {"Categoría": "Alimentación", "Revisada": True}},
                                 "added_rows": [], "deleted_rows": []}
    app.run()
    assert not app.exception
    assert app.session_state["lines"][0]["Categoría"] == "Alimentación"
    assert app.session_state["lines"][0]["Revisada"]
    app.selectbox(key="summary_currency").select("CRC").run()
    assert not app.exception
    assert app.session_state["lines"][0]["Categoría"] == "Alimentación"


def test_openai_secret_and_demo_classification(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    response = Mock(status_code=200)
    response.json.return_value = {"status": "completed", "output": [{"type": "message", "content": [{
        "type": "output_text", "text": json.dumps({"categories": [
            "Transporte y combustible", "Transporte y combustible", "Suministros de oficina",
            "Suministros de oficina", "Servicios y suscripciones"]})}]}]}
    with patch("gastoclaro.requests.post", return_value=response) as post:
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
        app.button[1].click().run(timeout=30)
        assert not app.exception
        assert all(line["Estado"] == "IA" for line in app.session_state["lines"])
        assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-openai-key"


def test_switch_models_keeps_results_and_separates_cache(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    response = Mock(status_code=200)
    response.json.return_value = {"status": "completed", "output": [{"type": "message", "content": [{
        "type": "output_text", "text": json.dumps({"categories": ["Tecnología"] * 5})}]}]}
    with patch("gastoclaro.requests.post", return_value=response) as post:
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
        app.button[1].click().run(timeout=30)
        assert not app.exception
        assert post.call_count == 1
        app.selectbox(key="ai_selection").select("Gemini · 3.1 Flash-Lite").run()
        assert not app.exception
        assert post.call_count == 1
        assert all(x["Categoría"] == "Tecnología" for x in app.session_state["lines"])
        response.json.return_value = {"candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"text": json.dumps(["Alimentación"] * 5)}]}}]}
        app.button[1].click().run(timeout=30)
        assert not app.exception
        assert post.call_count == 2
        assert post.call_args.kwargs["headers"] == {"x-goog-api-key": "gemini-test"}
        assert all(x["Categoría"] == "Alimentación" for x in app.session_state["lines"])
        assert len(app.session_state["cache"]) == 2
        app.selectbox(key="ai_selection").select("OpenAI · GPT-5.4 mini").run()
        app.button[1].click().run(timeout=30)
        assert not app.exception
        assert post.call_count == 2
        assert all(x["Categoría"] == "Tecnología" for x in app.session_state["lines"])
