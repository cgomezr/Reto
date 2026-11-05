# Entrega final GastoClaro

Nombre y apellidos: Carlos Gómez Rodríguez

GastoClaro consolida facturas electrónicas XML de prueba y propone categorías de gasto con IA. Esta entrega describe el alcance, la implementación y su verificación para la Actividad Sesión 4 del Módulo 01 de OBS Business School.

## 1. Enlaces

- App desplegada: https://reto-cgomezr.streamlit.app/
- Repositorio: https://github.com/cgomezr/Reto

## 2. Problema y usuario

La persona responsable de los gastos de un pequeño negocio recibe facturas electrónicas XML y debe abrirlas individualmente para registrar y clasificar compras en una hoja de cálculo. Este proceso consume tiempo y dificulta conocer los gastos por categoría y proveedor. GastoClaro automatiza la extracción y consolidación, mientras la IA interpreta las descripciones y propone categorías que el usuario puede corregir. Quedan fuera la validación tributaria, la autenticidad de las facturas, la conversión de monedas y la integración contable.

## 3. Especificación

Especificación completa: https://github.com/cgomezr/Reto/blob/HEAD/especificacion.md

- Funcionalidades: cargar y validar XML; proponer y corregir categorías; consultar resúmenes y exportar CSV.
- Entradas: hasta 20 archivos FacturaElectronica de Costa Rica v4.4 por lote, hasta 200 líneas aceptadas y 2 MB por archivo. Se emplean datos sintéticos.
- Salidas: detalle con categorías y estado de revisión, informe de archivos aceptados, duplicados y rechazados, gráfico y resúmenes por categoría, proveedor y moneda; CSV con las correcciones vigentes.
- Caso normal: tres facturas de ejemplo producen cinco líneas. CRC: gasto 25000.00, impuestos 3250.00 y total 28250.00. USD: gasto 40.00, impuestos 5.20 y total 45.20.
- Corrección: cambiar una categoría debe actualizar el resumen y el CSV. Los cálculos utilizan Decimal; las monedas se mantienen separadas.
- Casos límite: una clave repetida se cuenta una vez; un XML inválido se rechaza sin interrumpir los válidos; una descripción ambigua queda en Otros / requiere revisión.
- Fallo de IA: conservar los datos y las categorías completadas, explicar el error y permitir revisión manual o reintento de líneas pendientes.
- Sesión: cada procesamiento reemplaza el lote visible; se descarga el CSV antes de cerrar la sesión o cambiar de lote.

## 4. La pieza de IA

- Qué usa: APIs HTTP mediante requests. OpenAI con gpt-5.4-mini es la selección inicial; Gemini con gemini-3.1-flash-lite es una alternativa elegible. Estos identificadores corresponden a la configuración del código del proyecto.
- Por qué esa opción: un LLM permite interpretar descripciones variadas, abreviadas o ambiguas sin disponer de un conjunto de entrenamiento etiquetado. Su propuesta se limita a siete categorías y queda sujeta a revisión del usuario.
- Qué recibe: únicamente descripciones, instrucciones y categorías. Python extrae el XML, valida y calcula importes e impuestos. No se envían XML completos, proveedores ni importes.
- Qué pasa si falla: se informa de errores de conexión, acceso, modelo o cuota; se conservan las clasificaciones completadas y se permite clasificar manualmente. Los fallos temporales HTTP 500/502/503/504 tienen hasta tres intentos; los errores de cuota o acceso no se reintentan automáticamente. No se cambia de proveedor automáticamente.
- Dónde está la clave: OPENAI_API_KEY y/o GEMINI_API_KEY en secretos de Streamlit o variables de entorno; nunca en el código. En local, secrets.toml está excluido de Git.
- Consumo: caché por proveedor y modelo y lotes de hasta 25 descripciones. OpenAI requiere saldo. La alternativa Gemini puede usar cuota gratuita según el proveedor; hay que confirmar la adecuación al requisito docente de coste cero antes de entregar.

## 5. Proceso con IA

- Herramientas: Codex como agente de asistencia en el repositorio; Python, Streamlit y pytest para implementación y comprobación.
- Fichero de contexto del agente: https://github.com/cgomezr/Reto/blob/HEAD/AGENTS.md

Prompts clave utilizados durante el desarrollo, copiados literalmente:

1. [PENDIENTE: pegar el prompt original de creación a partir de la especificación].
2. [PENDIENTE: pegar el prompt original de una mejora o corrección relevante].
3. [PENDIENTE: pegar el prompt original de las pruebas o del manejo de errores].

Qué delegué al agente y qué revisé a mano:

- Delegación en esta preparación: revisar la correspondencia entre código y especificación, ejecutar las pruebas locales y preparar la documentación de entrega.
- Revisión personal: he usado la aplicación, pero no he realizado pruebas exhaustivas. Queda pendiente documentar los casos concretos revisados y cualquier mejora derivada de ese uso.

## 6. Prueba y mejora

Verificación automatizada del proyecto: 27 pruebas de extracción, clasificación y exportación superadas con `python -m pytest -q tests/test_gastoclaro.py` el 4 de noviembre de 2026. La ejecución de las pruebas de interfaz con AppTest no se completó en este entorno. Las llamadas de IA se simulan; esta ejecución no valida cuota, conexión ni acceso real a los modelos.

| Quién la probó | Qué probó | Qué pasó | Qué cambié |
| --- | --- | --- | --- |
| Agente mediante pytest | Extracción de tres XML y separación CRC/USD | Se contrastan cinco líneas y los importes esperados de cada moneda | Se documentan resultados esperados; no se modificó el código de la app en esta entrega |
| Agente mediante pytest | Duplicados, XML inválido y conservación ante fallo de IA | Se comprueban rechazo selectivo y conservación de resultados parciales | Se documenta el manejo de errores existente |
| Suite AppTest de Streamlit (ejecución pendiente) | Corrección de categoría y cambio de proveedor | Hay pruebas definidas; su ejecución no se completó en este entorno | Pendiente ejecutar y registrar el resultado de interfaz |
| Carlos Gómez Rodríguez | Uso personal de la aplicación, sin pruebas exhaustivas | He utilizado la aplicación; no se han documentado resultados específicos de prueba | No se ha documentado una mejora derivada de esta revisión |

Feedback a un compañero (opcional): [PENDIENTE: añadir el mensaje literal si corresponde, o eliminar esta línea].

## 7. Pitch escrito

1. La persona que controla los gastos de un pequeño negocio pierde tiempo revisando facturas XML y clasificando compras manualmente.
2. GastoClaro reúne las facturas, extrae sus líneas, permite corregir categorías y exporta un CSV con resúmenes separados por moneda.
3. La IA propone categorías a partir del significado de las descripciones, incluyendo abreviaturas y variaciones que exigirían muchas reglas manuales.
4. He usado la aplicación sin realizar pruebas exhaustivas; aún debo documentar un caso concreto, lo aprendido y una mejora basada en esa prueba.
5. Como siguiente paso, mediría la calidad de las propuestas sobre las cinco líneas sintéticas de ejemplo, comparando cada modelo con una clasificación manual y registrando cuántas categorías requieren corrección.

## 8. Capturas

### 1 La app funcionando

Se ven las tres facturas sintéticas procesadas, sus cinco líneas y el resumen de gastos de la moneda seleccionada.

[INSERTAR CAPTURA 1 AQUÍ]

Cómo obtenerla: ejecutar la app, pulsar «Probar con tres facturas de ejemplo» y mostrar el detalle junto al resumen. Si se presenta como clasificación por IA, usar una respuesta real y comprobar las categorías; sin clave, indicar que la clasificación es manual.

### 2 La app ante un caso límite o error

Se ve el aviso de archivo rechazado junto con las facturas válidas que siguen disponibles.

[INSERTAR CAPTURA 2 AQUÍ]

Cómo obtenerla: cargar un XML de ejemplo junto con un archivo .xml cuyo contenido sea <FacturaElectronica> sin cierre y pulsar «Procesar facturas». Capturar el informe con el rechazo y su motivo.

### 3 Trabajo con la IA

Se ve un prompt original de desarrollo y la respuesta del agente que ayudó a implementar o mejorar GastoClaro.

[INSERTAR CAPTURA 3 AQUÍ]

Cómo obtenerla: localizar una conversación real de desarrollo y capturar uno de los prompts transcritos en el apartado 5 junto con su respuesta.

### 4 La prueba

Se verá una prueba personal documentada o el comentario de un compañero sobre la app.

[INSERTAR CAPTURA 4 AQUÍ]

Cómo obtenerla: realizar y documentar una prueba concreta, por ejemplo corregir una categoría y comprobar el CSV, y capturar el resultado. Si motiva una mejora, registrar el cambio en el apartado 6; alternativamente, capturar el comentario real de un compañero en el debate del hito.

Antes de insertar las cuatro capturas, comprobar que no aparecen claves de API, secretos ni datos personales reales de facturas.
