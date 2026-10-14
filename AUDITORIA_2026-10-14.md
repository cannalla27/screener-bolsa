# Auditoría técnica — 14/10/2026

## Fallo corregido

Cuando el proveedor rechazaba un campo, el escáner eliminaba tanto la columna como los filtros y el orden asociados. Podía devolver valores que no cumplían la selección pedida. Además, recordaba el campo excluido y omitía condiciones en consultas posteriores.

Ahora se conserva siempre la selección solicitada. Si el proveedor rechaza un filtro, un criterio de orden, la restricción de cotización principal o un campo esencial, se muestra un error sin resultados. Solo se pueden retirar columnas informativas opcionales, con aviso visible. Las exclusiones de sesiones anteriores tampoco pueden suprimir condiciones.

Se rechazan respuestas HTTP correctas pero con estructura básica inválida. Se distingue hora de consulta de hora de cotización, y la etiqueta streaming se identifica como declaración del proveedor, sin prometer una latencia comprobada.

## Verificación

Ocho pruebas sin red en `test_integridad.py`: filtro izquierdo, filtro derecho, orden, columna opcional, exclusiones previas, cotización principal, respuesta inválida y columna esencial. Sintaxis de `app.py` comprobada. Ejecutar `python test_integridad.py`.

No se ha verificado una sesión desplegada ni se ha certificado la disponibilidad del servicio externo. El widget gráfico y el escáner son consultas diferentes: no se demuestra sincronización ni datos de menos de 15 segundos. Las dependencias no están congeladas como las demos de otros proyectos.

## Interpretación

Es un buscador con indicadores y clasificaciones del proveedor, no un motor de cartera ni un backtest. No hay rentabilidad anual ni caída esperable calculable con este código. Combinar filtros y ver un valor que después sube no valida una estrategia. Los resultados y resúmenes corresponden a la selección y al límite de filas, no necesariamente al mercado completo.
