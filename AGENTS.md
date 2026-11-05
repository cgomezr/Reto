# Instrucciones para agentes

## Contexto

Este directorio corresponde al reto del Módulo 01 de OBS Business School.
La fuente de requisitos del reto es `especificacion.md`.
La aplicación GastoClaro está implementada en Python y Streamlit siguiendo esa especificación.
`app.py` contiene la interfaz; `gastoclaro.py` contiene la extracción, clasificación y exportación.
El formato admitido es FacturaElectronica de Costa Rica v4.4, documentado en `README.md`.
La entrega académica está en `entrega_final.docx`, con fuente editable en `entrega_final.md`.
Mantener sus ocho apartados en el orden de la plantilla. No inventar nombres, URL de despliegue, prompts históricos ni pruebas personales; marcar los datos pendientes y reservar cuatro espacios para capturas.

## Antes de trabajar

- Leer `especificacion.md` y las instrucciones aplicables antes de realizar cambios.
- Revisar los archivos existentes y el estado de Git para respetar el trabajo del usuario.
- Si faltan requisitos necesarios, solicitar la información concreta que permita continuar. No inventar el enunciado, los entregables ni los criterios de evaluación.
- Cuando se complete la especificación, usarla para orientar la implementación y actualizar el contexto de este archivo si resulta necesario.

## Forma de trabajo

- Comunicarse en español y explicar brevemente los cambios realizados.
- Mantener los cambios enfocados en la solicitud y en los requisitos del reto.
- Respetar la estructura, las convenciones y las tecnologías existentes cuando se incorporen al proyecto.
- No añadir dependencias ni herramientas sin una necesidad concreta del trabajo solicitado.
- No sobrescribir cambios del usuario ni eliminar archivos ajenos a la tarea.
- No incluir contraseñas, tokens, credenciales ni datos sensibles en los archivos del proyecto.

## Validación y entrega

- Ejecutar las comprobaciones pertinentes para los archivos modificados, cuando estén disponibles.
- No afirmar que una validación pasó si no se ejecutó; informar las limitaciones encontradas.
- Al finalizar, indicar qué se cambió, cómo se verificó y si queda algún requisito pendiente.
- No crear commits ni publicar cambios salvo que el usuario lo solicite.

## Comandos del proyecto

- Instalar: `python -m pip install -r requirements.txt` dentro del entorno virtual.
- Ejecutar: `python -m streamlit run app.py`.
- Probar: `python -m pytest -q` (requiere instalar `pytest`).
- Mantener los cálculos monetarios en `Decimal` y las monedas separadas.
- Enviar a la IA únicamente descripciones y categorías; nunca el XML completo ni importes o proveedores.
- No incluir secretos; configurar `OPENAI_API_KEY` y/o `GEMINI_API_KEY` en el entorno o en los secretos de Streamlit.
- Las pruebas no deben consumir cuota real de IA.

- Mantener la caché separada por proveedor y modelo. No cambiar de proveedor automáticamente ante errores.
