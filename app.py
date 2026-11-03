"""GastoClaro · ejecutar con streamlit run app.py."""
import os
from copy import deepcopy
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from gastoclaro import AI_MODELS, CATEGORIES, OTHER, classify, export_csv, grouped, process_files

st.set_page_config(page_title="GastoClaro · Control de gastos", page_icon="🌿", layout="wide")


def secret_key(name):
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, "")).strip()
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return ""


def money(value):
    return f"{value:,.2f}"


def table(rows):
    # Los cálculos permanecen en Decimal; la tabla usa texto para conservar precisión.
    return pd.DataFrame([{k: str(v) if isinstance(v, Decimal) else v for k, v in row.items()} for row in rows])


for name, value in {"invoices": [], "lines": [], "report": [], "cache": {}, "notice": "", "version": 0}.items():
    if name not in st.session_state:
        st.session_state[name] = value

with st.sidebar:
    st.title("🌿 GastoClaro")
    st.caption("MENOS REGISTRO. MÁS CLARIDAD.")
    st.divider()
    st.markdown("**Tu flujo de trabajo**\n\n1. Carga tus XML\n2. Revisa las categorías\n3. Consulta y descarga")
    st.divider()
    use_ai = st.toggle("Proponer categorías con IA", value=True)
    selection = st.selectbox("Modelo de IA", list(AI_MODELS), key="ai_selection")
    provider, model, key_name = AI_MODELS[selection]
    key = secret_key(key_name)
    st.caption(f"{provider}: clave configurada" if key else f"Falta {key_name}. Clasificación manual disponible.")
    st.caption("OpenAI consume créditos o saldo." if provider == "OpenAI" else
               "Gemini: la cuota gratuita depende del proyecto. Use un proyecto sin facturación para evitar cargos.")
    st.caption("El modelo elegido se usa al procesar o reintentar líneas pendientes. Cambiarlo conserva las categorías existentes.")
    st.info("Solo archivos sintéticos. La IA recibe las descripciones, nunca el XML completo.")

def classify_selected():
    # Nunca reutilizar categorías de un modelo como si provinieran de otro.
    cache = st.session_state.cache.setdefault((provider, model), {})
    return classify(st.session_state.lines, cache, key, provider=provider, model=model)

st.caption("CONTROL DE GASTOS PARA PEQUEÑOS NEGOCIOS")
st.title("Tus facturas, en claro.")
st.write("Reúne tus compras, revisa sus categorías y descubre en qué gastas. Cada moneda conserva su propio resumen.")

with st.container(border=True):
    st.subheader("1 · Carga tus facturas")
    st.caption("Factura electrónica Costa Rica v4.4 · Hasta 20 XML, 200 líneas en total y 2 MB por archivo.")
    uploads = st.file_uploader("Selecciona archivos XML de prueba", type=["xml"], accept_multiple_files=True)
    left, right = st.columns([1, 1])
    process = left.button("Procesar facturas", type="primary", disabled=not uploads)
    demo = right.button("Probar con tres facturas de ejemplo")
    st.caption("Cada procesamiento inicia un nuevo lote. Las correcciones se conservan durante la sesión; descarga el CSV antes de cambiar de lote.")

if process or demo:
    files = ([(p.name, p.read_bytes()) for p in sorted((Path(__file__).parent / "examples").glob("*.xml"))]
             if demo else [(f.name, f.getvalue()) for f in uploads])
    try:
        invoices, report = process_files(files)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.session_state.invoices = invoices
        st.session_state.report = report
        st.session_state.lines = [line for invoice in invoices for line in invoice.lines]
        st.session_state.version += 1
        with st.spinner("Extrayendo datos y proponiendo categorías…"):
            st.session_state.notice = (classify_selected()
                                       if use_ai else "Clasificación manual seleccionada.")
        st.session_state.editor_baseline = deepcopy(st.session_state.lines)

if st.session_state.report:
    counts = Counter(row["Estado"] for row in st.session_state.report)
    cols = st.columns(3)
    for col, label in zip(cols, ["Aceptado", "Duplicado", "Rechazado"]):
        col.metric({"Aceptado": "Archivos aceptados", "Duplicado": "Duplicados omitidos", "Rechazado": "Archivos rechazados"}[label], counts[label])
    with st.expander("Ver resultado de cada archivo", expanded=bool(counts["Rechazado"])):
        st.dataframe(st.session_state.report, hide_index=True, use_container_width=True)

if st.session_state.notice:
    st.warning(st.session_state.notice)

if not st.session_state.lines:
    st.info("Carga facturas o utiliza los ejemplos para ver el detalle y los resúmenes.")
    st.stop()

st.subheader("2 · Revisa las categorías")
st.write("Edita la categoría y marca «Revisada» para confirmar cada línea. El resumen y el CSV se actualizan automáticamente.")
baseline = table(st.session_state.editor_baseline)
baseline["Revisada"] = [line.get("Revisada", False) for line in st.session_state.editor_baseline]
edited = st.data_editor(
    baseline, key=f"editor_{st.session_state.version}", hide_index=True, use_container_width=True,
    disabled=[c for c in baseline.columns if c not in ["Categoría", "Revisada"]],
    column_config={"Categoría": st.column_config.SelectboxColumn("Categoría", options=CATEGORIES, required=True),
                   "Revisada": st.column_config.CheckboxColumn("Revisada", required=True)},
    column_order=["Descripción", "Categoría", "Revisada", "Proveedor", "Moneda", "Gasto sin impuestos",
                  "Impuesto de línea", "Estado", "Modelo IA", "Revisión", "Archivo", "Línea", "Clave", "Fecha", "Cantidad"],
)
for line, (_, row) in zip(st.session_state.lines, edited.iterrows()):
    if row["Categoría"] in CATEGORIES and row["Categoría"] != line["Categoría"]:
        line["Categoría"] = row["Categoría"]
        line["Estado"] = "Manual"
    line["Revisada"] = bool(row["Revisada"])
    if line["Revisada"]:
        line["Estado"] = "Manual"

pending = [x for x in st.session_state.lines if not x.get("Revisada") and
           (x["Categoría"] == OTHER or x["Estado"] == "Pendiente" or x["Revisión"])]
st.caption(f"{len(st.session_state.lines)} líneas · {len(pending)} requieren revisión")
if pending:
    with st.expander("Líneas que requieren revisión"):
        st.dataframe(table(pending), hide_index=True, use_container_width=True)
if use_ai and st.button("Reintentar IA en líneas pendientes", disabled=not any(x["Estado"] == "Pendiente" for x in st.session_state.lines)):
    with st.spinner("Consultando IA…"):
        st.session_state.notice = classify_selected()
    st.session_state.version += 1
    st.session_state.editor_baseline = deepcopy(st.session_state.lines)
    st.rerun()

st.subheader("3 · Entiende tus gastos")
currencies = sorted({x["Moneda"] for x in st.session_state.lines})
currency = st.selectbox("Moneda del resumen", currencies, key="summary_currency")
lines = [x for x in st.session_state.lines if x["Moneda"] == currency]
invoices = [x for x in st.session_state.invoices if x.currency == currency]
cols = st.columns(3)
cols[0].metric(f"Gasto clasificado · {currency}", money(sum((x["Gasto sin impuestos"] for x in lines), Decimal(0))))
cols[1].metric(f"Impuestos de facturas · {currency}", money(sum((x.tax for x in invoices), Decimal(0))))
cols[2].metric(f"Total de facturas · {currency}", money(sum((x.total for x in invoices), Decimal(0))))
st.caption("Gasto clasificado = SubTotal de las líneas, después de descuentos y antes de impuestos. El total de factura puede incluir otros cargos y devolución de IVA.")
category_tab, supplier_tab, invoice_tab = st.tabs(["Por categoría", "Por proveedor", "Facturas y monedas"])
with category_tab:
    data = grouped(lines, "Categoría")
    st.dataframe(table(data), hide_index=True, use_container_width=True)
    chart = pd.DataFrame(data)
    chart["Gasto sin impuestos"] = chart["Gasto sin impuestos"].astype(float)
    st.bar_chart(chart, x="Categoría", y="Gasto sin impuestos", color="#167D71", horizontal=True)
with supplier_tab:
    st.dataframe(table(grouped(lines, "Proveedor")), hide_index=True, use_container_width=True)
with invoice_tab:
    st.dataframe(table([{"Archivo": x.filename, "Proveedor": x.supplier, "Moneda": x.currency,
                         "Neto declarado": x.net, "Impuestos": x.tax, "Total factura": x.total,
                         "Revisión": " · ".join(x.warnings)} for x in st.session_state.invoices]),
                 hide_index=True, use_container_width=True)
    st.caption("Cada fila conserva su moneda. No se suman importes entre monedas distintas.")
st.download_button("Descargar detalle en CSV", export_csv(st.session_state.lines),
                   file_name="gastoclaro_detalle.csv", mime="text/csv", type="primary")
st.caption("El CSV incluye todas las monedas, las categorías corregidas y los indicadores de revisión.")
