# Stripe API — Flujo de Intenciones de Pago (PaymentIntents)

La API de PaymentIntents es el mecanismo recomendado por Stripe para gestionar y cobrar pagos de forma segura, adaptandose de manera automatica a regulaciones como la autenticacion reforzada de clientes (SCA) en Europa (3D Secure).

## 1. Crear un PaymentIntent
Para cobrar a un cliente, debes crear un `PaymentIntent` desde tu servidor secreto utilizando tu **Llave Secreta** (`sk_...`).

### Endpoint
POST `https://api.stripe.com/v1/payment_intents`

### Request Body (URL-encoded)
- `amount`: Monto total a cobrar expresado en la unidad minima de la moneda (por ejemplo, `5000` para cobrar 50.00 USD).
- `currency`: Codigo de moneda de 3 letras (por ejemplo, `usd`, `cop`).
- `payment_method_types[]`: Un array indicando los tipos de metodos de pago aceptados (por ejemplo, `card`).
- `payment_method`: (Opcional en la creacion) El ID del metodo de pago a utilizar (`pm_...`).
- `confirm`: (Opcional) Booleano. Si se establece como `true`, se intenta cobrar inmediatamente si el metodo de pago esta presente.

### Ejemplo de Respuesta (JSON)
```json
{
  "id": "pi_3NxiAEJdJf...",
  "object": "payment_intent",
  "amount": 5000,
  "amount_received": 0,
  "client_secret": "pi_3NxiAEJdJf_secret_xxxxxxxxxx",
  "currency": "usd",
  "customer": null,
  "payment_method": null,
  "payment_method_types": [
    "card"
  ],
  "status": "requires_payment_method"
}
```

---

## 2. Confirmar un PaymentIntent
Si creaste el `PaymentIntent` sin confirmar, debes confirmarlo pasando el metodo de pago.

### Endpoint
POST `https://api.stripe.com/v1/payment_intents/pi_3NxiAEJdJf.../confirm`

### Request Body (URL-encoded)
- `payment_method`: El identificador del metodo de pago (`pm_...`).

### Ejemplo de Respuesta de Confirmacion Exitosa (JSON)
```json
{
  "id": "pi_3NxiAEJdJf...",
  "object": "payment_intent",
  "amount": 5000,
  "amount_received": 5000,
  "currency": "usd",
  "payment_method": "pm_1Nxi9ALkdJf...",
  "status": "succeeded"
}
```

---

## 3. Estados del PaymentIntent
Durante el ciclo de vida del pago, el `status` del `PaymentIntent` puede tomar los siguientes valores principales:

- `requires_payment_method`: Estado inicial. Requiere asociar un `PaymentMethod`.
- `requires_confirmation`: El `PaymentMethod` esta asociado. Requiere confirmacion del servidor.
- `requires_action`: El pago requiere autenticacion del cliente (por ejemplo, validacion de contraseña 3D Secure). Stripe proporciona una URL de accion en la respuesta.
- `processing`: El cobro esta siendo procesado por la pasarela o banco.
- `succeeded`: El cobro fue exitoso y el dinero fue capturado.
- `canceled`: La intencion de pago fue cancelada.
