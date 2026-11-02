from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gastoclaro import (AIError, CATEGORIES, OTHER, QUOTA_MESSAGE, ask_gemini,
                       classify, export_csv, grouped, process_files)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def files():
    return [(p.name, p.read_bytes()) for p in sorted(EXAMPLES.glob("*.xml"))]


def test_normal_and_separate_currencies():
    invoices, report = process_files(files())
    lines = [line for invoice in invoices for line in invoice.lines]
    assert len(lines) == 5
    assert all(row["Estado"] == "Aceptado" for row in report)
    assert not any(x.warnings for x in invoices)
    totals = {row["Moneda"]: row["Gasto sin impuestos"] for row in grouped(lines, "Categoría")}
    assert totals == {"CRC": Decimal("25000"), "USD": Decimal("40")}
    assert sum(x.total for x in invoices if x.currency == "CRC") == Decimal("28250")
    assert invoices[2].tax == Decimal("5.20")


def test_duplicates_and_invalid_files_do_not_stop_batch():
    data = files()
    invoices, report = process_files([data[0], ("copy.xml", data[0][1]), ("bad.xml", b"<"), data[1]])
    assert len(invoices) == 2
    assert [x["Estado"] for x in report] == ["Aceptado", "Duplicado", "Rechazado", "Aceptado"]


def test_reject_other_document_and_entities():
    for data in [b"<NotaCreditoElectronica/>", b'<!DOCTYPE a [<!ENTITY x "abc">]><a>&x;</a>']:
        assert process_files([("bad.xml", data)])[1][0]["Estado"] == "Rechazado"


def test_file_and_line_limits():
    with pytest.raises(ValueError):
        process_files(files() * 7)
    data = files()[0][1]
    start = data.index(b"<LineaDetalle>")
    end = data.index(b"</LineaDetalle>") + len(b"</LineaDetalle>")
    block = data[start:end]
    expanded = b"".join(block.replace(b"<NumeroLinea>1</NumeroLinea>", f"<NumeroLinea>{n}</NumeroLinea>".encode()) for n in range(1, 202))
    data = data[:data.index(b"<DetalleServicio>")] + b"<DetalleServicio>" + expanded + data[data.index(b"</DetalleServicio>"):]
    assert process_files([("large.xml", data)])[1][0]["Estado"] == "Rechazado"


def test_invalid_amount_and_reconciliation():
    name, data = files()[0]
    bad = data.replace(b"<SubTotal>15000</SubTotal>", b"<SubTotal>NaN</SubTotal>")
    assert process_files([(name, bad)])[1][0]["Estado"] == "Rechazado"
    mismatch = data.replace(b"<TotalVentaNeta>20000</TotalVentaNeta>", b"<TotalVentaNeta>20001</TotalVentaNeta>")
    assert process_files([(name, mismatch)])[0][0].warnings


def test_ai_cache_manual_edits_and_export():
    invoices, _ = process_files(files())
    lines = [x for i in invoices for x in i.lines]
    lines.append(dict(lines[0]))
    requester = Mock(return_value=[CATEGORIES[1], CATEGORIES[1], CATEGORIES[4], CATEGORIES[4], OTHER])
    cache = {}
    assert classify(lines, cache, "test", requester) == ""
    assert len(requester.call_args.args[0]) == 5
    assert lines[-1]["Categoría"] == CATEGORIES[1]
    lines[0]["Categoría"] = CATEGORIES[0]
    lines[0]["Estado"] = "Manual"
    classify(lines, cache, "test", requester)
    assert requester.call_count == 1
    assert lines[0]["Categoría"] == CATEGORIES[0]
    assert "Alimentación" in export_csv(lines).decode("utf-8-sig")
    assert any(x["Categoría"] == CATEGORIES[0] for x in grouped(lines, "Categoría"))


def test_quota_retains_completed_batches():
    lines = [{"Descripción": f"Producto {n}", "Categoría": OTHER, "Estado": "Pendiente", "Revisión": ""} for n in range(26)]
    request = Mock(side_effect=[[CATEGORIES[0]] * 25, AIError(QUOTA_MESSAGE)])
    cache = {}
    assert classify(lines, cache, "test", request) == QUOTA_MESSAGE
    assert sum(x["Estado"] == "IA" for x in lines) == 25
    assert lines[-1]["Estado"] == "Pendiente"
    request = Mock(return_value=[OTHER])
    assert classify(lines, cache, "test", request) == ""
    assert request.call_args.args[0] == ["Producto 25"]


def test_provider_privacy_and_response_validation():
    response = Mock(status_code=200)
    response.json.return_value = {"candidates": [{"content": {"parts": [{"text": '["Tecnología"]'}]}}]}
    with patch("gastoclaro.requests.post", return_value=response) as post:
        assert ask_gemini(["Monitor"], "secret") == ["Tecnología"]
        payload = post.call_args.kwargs["json"]
        assert payload["contents"] == [{"parts": [{"text": '["Monitor"]'}]}]
        assert "secret" not in str(payload)
        response.status_code = 429
        with pytest.raises(AIError, match="Se agotó"):
            ask_gemini(["Monitor"], "secret")
        response.status_code = 200
        response.json.return_value = {"candidates": [{"content": {"parts": [{"text": '["Inventada"]'}]}}]}
        with pytest.raises(AIError, match="inválida"):
            ask_gemini(["Monitor"], "secret")


def test_csv_formula_protection():
    assert "'=HYPERLINK" in export_csv([{"Descripción": "=HYPERLINK()"}]).decode("utf-8-sig")
