# Stripe API — Eventos y Estructura de Webhooks

Stripe utiliza una estructura de payload JSON estandarizada para todos los eventos enviados a tu endpoint de webhook. Esto permite manejar multiples tipos de eventos (por ejemplo, pagos exitosos, suscripciones canceladas, etc.) utilizando la misma estructura base.

## Estructura Base del Webhook (JSON Payload)

```json
{
  "id": "evt_1NxiAFJdJf...",
  "object": "event",
  "api_version": "2023-10-16",
  "created": 1783456805,
  "data": {
    "object": {
      "id": "pi_3NxiAEJdJf...",
      "object": "payment_intent",
      "amount": 5000,
      "amount_received": 5000,
      "currency": "usd",
      "payment_method": "pm_1Nxi9ALkdJf...",
      "status": "succeeded"
    }
  },
  "livemode": false,
  "pending_webhooks": 1,
  "request": {
    "id": "req_xxxxxxxxxx",
    "idempotency_key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  },
  "type": "payment_intent.succeeded"
}
```

### Campos Clave de la Estructura:
- `id`: Identificador unico del evento.
- `object`: Tipo de objeto, siempre `"event"`.
- `api_version`: La version de la API de Stripe utilizada para estructurar el objeto.
- `created`: Unix timestamp del momento en que se creo el evento.
- `data.object`: El recurso especifico afectado por el evento (en este caso, un objeto `payment_intent`).
- `type`: El tipo de evento (por ejemplo, `payment_intent.succeeded`).

---

## Tipos de Eventos Comunes en Integraciones de Pago

Es buena practica configurar tu webhook para escuchar solo los eventos especificos que tu negocio requiere procesar:

| Evento | Objeto en `data.object` | Descripcion |
|---|---|---|
| `payment_intent.created` | `payment_intent` | Se crea una intencion de pago. |
| `payment_intent.succeeded` | `payment_intent` | El pago fue exitoso y los fondos fueron capturados. |
| `payment_intent.payment_failed` | `payment_intent` | El pago fallo (por ejemplo, tarjeta rechazada o expirada). |
| `charge.refunded` | `charge` | Se realiza un reembolso total o parcial sobre un cargo. |

---

## Politicas de Reintento de Stripe
Si tu servidor no responde con un codigo HTTP `2xx` (por ejemplo, responde `500` o expira la conexion), Stripe intentara enviar la notificacion del evento de forma progresiva durante 3 dias (con backoff exponencial) antes de descartarlo.
