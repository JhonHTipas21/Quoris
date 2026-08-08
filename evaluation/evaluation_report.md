# RAG Evaluation Report — Quoris

Generado el: 2026-08-08 01:06:54

## Métricas Globales
| Métrica | Valor | Objetivo | Estado |
|---|---|---|---|
| **Casos de prueba** | 30 | - | - |
| **Recall@3** | 100.0% | > 85% | ✅ Aprobado |
| **Mean Reciprocal Rank (MRR)** | 0.950 | > 0.70 | ✅ Aprobado |
| **Latencia Promedio (Retrieval)** | 0.088s | < 1.0s | ✅ Aprobado |

## Resultados por Caso de Uso
| ID | Pregunta | Sección Objetivo | Recall Hit | MRR | Latencia (s) | Citas |
|---|---|---|---|---|---|---|
| q1 | ¿Cuáles son las URLs base para la API de Wompi en sandbox y producción? | Introducción y Autenticación | ✅ | 1.00 | 0.247s | 0 |
| q2 | ¿Cuál es la diferencia de uso entre la llave pública y la llave privada en Wompi? | Introducción y Autenticación | ✅ | 1.00 | 0.072s | 0 |
| q3 | ¿Cómo debo pasar mi Llave Privada en los headers para autenticarme en la API de Wompi? | Introducción y Autenticación | ✅ | 1.00 | 0.05s | 0 |
| q4 | ¿Por qué es obligatorio el token de aceptación (Acceptance Token) en la API de Wompi? | Tokens de Aceptación | ✅ | 1.00 | 0.075s | 0 |
| q5 | ¿Qué endpoint y método HTTP debo usar para obtener el token de aceptación de Wompi? | Tokens de Aceptación | ✅ | 0.50 | 0.074s | 0 |
| q6 | ¿Qué campos contiene el objeto presigned_acceptance que retorna el endpoint de comercios? | Tokens de Aceptación | ✅ | 0.50 | 0.089s | 0 |
| q7 | ¿Qué ocurre si no envío el token de aceptación al crear una transacción en Wompi? | Tokens de Aceptación | ✅ | 0.50 | 0.11s | 0 |
| q8 | ¿Cómo se tokeniza una tarjeta de crédito en Wompi? | Tokenización | ✅ | 1.00 | 0.153s | 0 |
| q9 | ¿Cuál es el formato del ID del token de tarjeta que retorna Wompi al tokenizar? | Tokenización | ✅ | 1.00 | 0.079s | 0 |
| q10 | ¿Cómo se tokeniza una cuenta de Nequi en la API de Wompi? | Tokenización | ✅ | 1.00 | 0.094s | 0 |
| q11 | ¿Qué endpoint se utiliza para crear una transacción directa en Wompi? | Creación de Transacciones | ✅ | 1.00 | 0.063s | 0 |
| q12 | ¿Cómo se especifica un monto de 50.000 COP en la petición de creación de transacción de Wompi? | Creación de Transacciones | ✅ | 1.00 | 0.087s | 0 |
| q13 | ¿Cuáles son los campos obligatorios para el cuerpo JSON de una transacción de Wompi? | Creación de Transacciones | ✅ | 1.00 | 0.05s | 0 |
| q14 | ¿Cómo se estructura el objeto payment_method para un pago con tarjeta de crédito en Wompi? | Creación de Transacciones | ✅ | 1.00 | 0.084s | 0 |
| q15 | ¿Cómo se estructura el objeto payment_method para un pago con Nequi? | Creación de Transacciones | ✅ | 1.00 | 0.091s | 0 |
| q16 | ¿Cuáles son los estados posibles de una transacción en la respuesta de Wompi? | Creación de Transacciones | ✅ | 1.00 | 0.065s | 0 |
| q17 | ¿Qué es la firma de integridad en Wompi y para qué sirve? | Firmas de Integridad | ✅ | 1.00 | 0.084s | 0 |
| q18 | ¿Dónde se obtiene el secreto de integridad para firmar transacciones en Wompi? | Firmas de Integridad | ✅ | 1.00 | 0.055s | 0 |
| q19 | ¿Cuál es el orden estricto de los campos para calcular la firma de integridad de transacciones? | Firmas de Integridad | ✅ | 1.00 | 0.057s | 0 |
| q20 | ¿Qué algoritmo de hash y formato se usa para la firma de integridad de Wompi? | Firmas de Integridad | ✅ | 1.00 | 0.058s | 0 |
| q21 | Escribe un ejemplo de cómo calcular la firma de integridad de Wompi en Python. | Firmas de Integridad | ✅ | 1.00 | 0.081s | 0 |
| q22 | ¿Qué es un webhook en Wompi y cuándo se envía? | Webhooks y Notificación de Eventos | ✅ | 1.00 | 0.116s | 0 |
| q23 | ¿Cómo viene estructurado el JSON del payload de un webhook de Wompi? | Webhooks y Notificación de Eventos | ✅ | 1.00 | 0.101s | 0 |
| q24 | ¿Cómo se calcula la firma (checksum) para validar la integridad de un webhook recibido? | Webhooks y Notificación de Eventos | ✅ | 1.00 | 0.099s | 0 |
| q25 | ¿Qué propiedades se usan típicamente en signature.properties de un webhook de transacciones? | Webhooks y Notificación de Eventos | ✅ | 1.00 | 0.09s | 0 |
| q26 | ¿Cuál debe ser la respuesta de mi servidor al recibir un webhook de Wompi y cuál es el tiempo de timeout? | Webhooks y Notificación de Eventos | ✅ | 1.00 | 0.129s | 0 |
| q27 | ¿Cuántas veces reintenta Wompi el envío de un webhook si mi servidor no responde exitosamente? | Webhooks y Notificación de Eventos | ✅ | 1.00 | 0.105s | 0 |
| q28 | Escribe una función de validación de webhook de Wompi en Python. | Webhooks y Notificación de Eventos | ✅ | 1.00 | 0.081s | 0 |
| q29 | ¿Qué ocurre si una transacción de Nequi queda en estado PENDING? | Creación de Transacciones | ✅ | 1.00 | 0.052s | 0 |
| q30 | ¿Es posible tokenizar tarjetas o Nequi desde el backend (servidor)? | Tokenización | ✅ | 1.00 | 0.052s | 0 |
