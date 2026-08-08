# Mercado Pago API — Eventos y Estructura de Webhooks

Mercado Pago utiliza notificaciones instantaneas de pago (IPN) o notificaciones Webhook para informar a tu sistema cuando hay cambios en el estado de un recurso (como pagos, suscripciones o disputas).

## Estructura del Webhook (JSON Payload)
A diferencia de otras pasarelas, Mercado Pago no envia los detalles completos del recurso cobrado en el body del webhook. En su lugar, envia el identificador del recurso (`data.id`) y el tipo de recurso (`type`). Tu servidor backend debe utilizar este identificador para consultar la API de Mercado Pago (`GET /v1/payments/{id}`) y verificar el estado real de la transaccion.

### Ejemplo de Webhook (JSON)
```json
{
  "action": "payment.created",
  "api_version": "v1",
  "data": {
    "id": "9988223344"
  },
  "date_created": "2026-08-08T12:35:00Z",
  "id": 1122334455,
  "live_mode": false,
  "type": "payment",
  "user_id": 123456789
}
```

### Campos Clave del Payload:
- `action`: La accion especifica que provoco el evento (por ejemplo, `payment.created` o `payment.updated`).
- `type`: El tipo de recurso afectado (por ejemplo, `payment`, `plan`, `subscription`).
- `data.id`: El identificador unico del recurso en la base de datos de Mercado Pago. Debes usar este ID para consultar el estado del cobro.
- `id`: Identificador unico del evento de notificacion.

---

## Tipos de Eventos de Webhook Comunes
- `payment.created`: Se genera cuando se crea un intento de pago (util en PSE o efectivo).
- `payment.updated`: Se genera cuando el pago cambia de estado (de `pending` a `approved` o `rejected`).
- `subscription.created`: Se registra una nueva suscripcion recurrente.
- `subscription.updated`: Se actualiza la suscripcion (por ejemplo, cobro mensual exitoso o cancelacion).

---

## Flujo de Procesamiento Recomendado
1. **Recibir la notificacion HTTP POST** en tu servidor.
2. **Validar la firma** de la notificacion utilizando la cabecera `x-signature`.
3. **Retornar inmediatamente un codigo HTTP 200 OK** para confirmar a Mercado Pago la recepcion exitosa (el timeout de respuesta es de 20 segundos).
4. **Consultar la API de Mercado Pago** de forma asincrona utilizando el identificador `data.id` obtenido.
5. **Actualizar el estado del pedido** en tu base de datos local en base al estado retornado por la API (`approved`, `rejected`, etc.).
