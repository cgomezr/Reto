# GastoClaro

Aplicación en Python y Streamlit para consolidar facturas XML sintéticas, proponer categorías con OpenAI o Gemini y exportar el detalle corregido en CSV.

## Ejecutar

Se recomienda Python 3.12 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m streamlit run app.py
```

Abra la dirección que Streamlit muestra en la terminal. Pulse **Probar con tres facturas de ejemplo** o cargue los XML de `examples/`.

Sin clave de IA, la extracción, las correcciones, los resúmenes y el CSV funcionan; las categorías quedan pendientes para revisión manual. No se simulan resultados de IA.

## Configurar los proveedores de IA

La integración utiliza la API Responses de OpenAI con `gpt-5.4-mini` y salida JSON restringida a las categorías admitidas. La API consume créditos o saldo según el uso; la aplicación no puede consultar el saldo de su cuenta. El cambio de Gemini a OpenAI fue solicitado por el usuario y sustituye el requisito original de cuota gratuita.

1. Cree una clave del proyecto en [OpenAI API Keys](https://platform.openai.com/api-keys) y compruebe los créditos en [Billing](https://platform.openai.com/settings/organization/billing/overview).
2. En local, copie `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y configure `OPENAI_API_KEY`. También puede definir esa variable de entorno.
3. En Streamlit Community Cloud, abra **Settings → Secrets** y guarde:

```toml
OPENAI_API_KEY = "su_clave_de_openai"
```

4. Suba los cambios de código al repositorio conectado y reinicie la app si continúa mostrando Gemini. Puede conservar `GEMINI_API_KEY` junto con `OPENAI_API_KEY` para elegir el proveedor en la barra lateral.
5. Procese los ejemplos con **Proponer categorías con IA** activado.

El selector **Modelo de IA** permite elegir **OpenAI · GPT-5.4 mini** o **Gemini · 3.1 Flash-Lite**. Configure solo la clave del proveedor que utilice, o ambas:

```toml
OPENAI_API_KEY = "su_clave_de_openai"
GEMINI_API_KEY = "su_clave_de_gemini"
```

OpenAI es la opción inicial. Gemini utiliza `gemini-3.1-flash-lite` con `GEMINI_API_KEY`, creada en Google AI Studio. Para evitar cargos en Gemini, use un proyecto sin facturación; la cuota gratuita y la disponibilidad dependen del proveedor. Si no está la clave del modelo elegido, puede trabajar manualmente. No se cambia de proveedor automáticamente ante errores.

Cambiar el selector no envía solicitudes ni elimina datos. El modelo elegido se aplica al siguiente procesamiento o al reintento de líneas pendientes. Las líneas completadas y las correcciones manuales se conservan; para comparar la misma factura entre modelos, descargue su CSV y procese un nuevo lote. La caché se separa por proveedor y modelo. La columna **Modelo IA** conserva el origen de la propuesta en el detalle y CSV; una corrección manual se identifica en **Estado**.

La API recibe únicamente descripciones de líneas, instrucciones y categorías. No recibe XML, claves de factura, proveedores, fechas ni importes. En OpenAI se usa `store=false`; no se habilitan herramientas externas en ningún proveedor. Las descripciones idénticas reutilizan su categoría durante la sesión. Las correcciones manuales no entrenan el modelo ni modifican esa caché. Use solamente XML sintéticos.

El procesamiento usa lotes de hasta 25 descripciones, un máximo de 2000 tokens de salida por solicitud y razonamiento desactivado en OpenAI. Estos límites reducen consumo, pero no constituyen un presupuesto monetario global. Consulte las [tarifas del modelo](https://developers.openai.com/api/docs/models/gpt-5.4-mini) y el [consumo de la cuenta](https://platform.openai.com/usage).

HTTP 401/403 indica problemas de acceso; 404 indica un modelo no disponible; 429 informa sobre cuota, saldo o límite de solicitudes. Si OpenAI devuelve `insufficient_quota`, se indica que revise Billing. Los datos y las clasificaciones completadas se conservan y puede continuar manualmente. Las pruebas usan respuestas simuladas y no consumen créditos; la llamada real debe comprobarse en el despliegue con su clave.

## XML admitido

Ante errores temporales HTTP 500/502/503/504, se realizan como máximo tres intentos, con esperas de uno y dos segundos. Si el servicio sigue sin estar disponible, los datos y las clasificaciones completadas permanecen en la sesión y el usuario puede reintentar las líneas pendientes o clasificarlas manualmente. No se reintentan automáticamente errores de cuota ni de acceso.

Se admite exclusivamente raíz `FacturaElectronica` y espacio de nombres:

```text
https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica
```

Referencia: [Anexos y estructuras v4.4 de Hacienda](https://www.hacienda.go.cr/docs/ANEXOS_Y_ESTRUCTURAS_V4.4.pdf).

Se extraen `Clave` (50 dígitos), `FechaEmision`, `Emisor/Nombre`, `DetalleServicio/LineaDetalle` y `ResumenFactura`. Cada línea debe contener `NumeroLinea`, `Cantidad` y `SubTotal`; una descripción ausente se marca para revisión. La moneda se obtiene de `ResumenFactura/CodigoTipoMoneda/CodigoMoneda`; se requieren `TotalVentaNeta` y `TotalComprobante`. Se admite `TotalImpuesto` ausente como cero.

El gasto clasificado es `SubTotal`, después de descuentos y antes de impuestos. Se extrae `ImpuestoNeto` de la línea o, si falta, se suman sus impuestos menos exoneraciones. Se muestran por separado los impuestos y el total declarado de cada factura. Se revisan las diferencias entre líneas y resumen con una tolerancia de 0,01 unidades; las discrepancias se informan sin alterar los importes. Otros cargos y devolución de IVA se consideran en la comprobación del total, pero no se clasifican como líneas de gasto.

Los cálculos y CSV usan `Decimal`; solamente el gráfico convierte sus valores a números de visualización. Ningún resumen suma monedas diferentes. La pantalla muestra dos decimales; el detalle y CSV conservan hasta cinco.

Esto es una validación de los campos necesarios para extracción, **no una validación completa contra XSD, tributaria ni de firma**. Los ejemplos contienen datos ficticios y no son comprobantes fiscales utilizables. No se aceptan notas de crédito, débito, tiquetes ni facturas de otras versiones.

## Límites y sesión

- Máximo 20 archivos por lote, 200 líneas aceptadas y 2 MB por archivo.
- Un archivo inválido se rechaza y los demás continúan. Si un archivo supera el cupo restante de líneas, se rechaza entero con el motivo correspondiente.
- La misma clave se contabiliza una sola vez en el lote.
- Cada procesamiento reemplaza el lote visible. Las correcciones y los datos solo viven durante la sesión; descargue el CSV antes de cambiar de lote o cerrar la sesión.
- El CSV incluye las categorías vigentes y el estado de revisión. Se neutralizan textos que podrían interpretarse como fórmulas al abrirlos en una hoja de cálculo.

## Ejemplos y resultados esperados

Los tres XML de `examples/` contienen cinco líneas:

| Moneda | Líneas | Gasto sin impuestos | Impuestos | Total facturas |
| --- | ---: | ---: | ---: | ---: |
| CRC | 4 | 25000.00 | 3250.00 | 28250.00 |
| USD | 1 | 40.00 | 5.20 | 45.20 |

Las categorías son propuestas por el modelo y deben revisarse. Para probar duplicados, cargue una copia de cualquier ejemplo junto con el original. Para probar rechazo, incluya un XML mal formado. Una descripción ambigua debe permanecer en **Otros / requiere revisión**; también puede seleccionarse manualmente.

## Pruebas

```powershell
.\.venv\Scripts\python -m pip install pytest
.\.venv\Scripts\python -m pytest -q
```

Se verifican extracción, importes esperados, monedas separadas, duplicados, XML inválido, límites, conciliación, caché, corrección y CSV, privacidad del payload, respuesta inválida y recuperación de cuota con resultados parciales.

## Desplegar en Streamlit Community Cloud

1. Suba este proyecto a un repositorio de GitHub sin incluir secretos ni `.venv`.
2. En [Streamlit Community Cloud](https://share.streamlit.io/) seleccione el repositorio y `app.py` como archivo principal.
3. Configure `OPENAI_API_KEY` en los secretos de la aplicación y verifique los créditos disponibles.
4. Verifique los ejemplos y las cuotas del proveedor antes de utilizarla.

## Archivos

- `app.py`: interfaz y estado de la sesión.
- `gastoclaro.py`: extracción, validaciones, integración de IA y exportación.
- `examples/`: tres facturas sintéticas.
- `tests/`: pruebas locales sin consumo de cuota de IA.
