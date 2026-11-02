from pathlib import Path

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
    app.selectbox[0].select("USD").run()
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
    app.selectbox[0].select("CRC").run()
    assert not app.exception
    assert app.session_state["lines"][0]["Categoría"] == "Alimentación"
