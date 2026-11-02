# GastoClaro

Aplicación en Python y Streamlit para consolidar facturas XML sintéticas, proponer categorías con Gemini y exportar el detalle corregido en CSV.

## Ejecutar

Se recomienda Python 3.12 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m streamlit run app.py
```

Abra la dirección que Streamlit muestra en la terminal. Pulse **Probar con tres facturas de ejemplo** o cargue los XML de `examples/`.

Sin clave de IA, la extracción, las correcciones, los resúmenes y el CSV funcionan; las categorías quedan pendientes para revisión manual. No se simulan resultados de IA.

## Configurar la IA gratuita

Se seleccionó `gemini-2.5-flash-lite`. La [tabla oficial de precios](https://ai.google.dev/gemini-api/docs/pricing#gemini-2.5-flash-lite) ofrece entrada y salida gratuitas en el nivel gratuito. Los [límites efectivos](https://ai.google.dev/gemini-api/docs/rate-limits) dependen del proyecto y se consultan en Google AI Studio. La disponibilidad debe revisarse antes de desplegar.

1. Cree una clave en [Google AI Studio](https://aistudio.google.com/apikey) para un proyecto **sin facturación habilitada**. No active servicios de pago.
2. Copie `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y complete `GEMINI_API_KEY`. También puede definir esa variable de entorno.
3. Reinicie Streamlit y active **Proponer categorías con IA**.

La aplicación no puede comprobar el nivel de facturación del proyecto; el requisito de coste cero depende de usar esa configuración gratuita. No cambia de modelo ni activa servicios de pago ante errores. HTTP 429 muestra el mensaje de cuota de la especificación y conserva las extracciones y clasificaciones completadas. Puede reintentar las líneas pendientes.

La API recibe únicamente descripciones de líneas, instrucciones de clasificación y las categorías permitidas. No recibe XML, claves de factura, proveedores, fechas ni importes. Se reutilizan descripciones idénticas dentro de la sesión. Las correcciones manuales no entrenan el modelo ni modifican esa caché. Google indica que los datos del nivel gratuito pueden utilizarse para mejorar sus productos: use solo datos sintéticos.

La documentación pública del proveedor se comprobó durante la implementación. La llamada real requiere una clave del usuario; las pruebas automatizadas del adaptador utilizan respuestas simuladas.

## XML admitido

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
3. Configure `GEMINI_API_KEY` en los secretos de la aplicación, usando un proyecto sin facturación.
4. Verifique los ejemplos y las cuotas del proveedor antes de utilizarla.

## Archivos

- `app.py`: interfaz y estado de la sesión.
- `gastoclaro.py`: extracción, validaciones, integración de IA y exportación.
- `examples/`: tres facturas sintéticas.
- `tests/`: pruebas locales sin consumo de cuota de IA.
