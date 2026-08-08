# Mercado Pago API — Creacion de Pagos

Para realizar cargos monetarios a tus clientes, debes invocar la API de Pagos desde tu servidor utilizando tu **Token de Acceso** (`APP_USR-...`) en las cabeceras HTTP de autorizacion.

## Endpoint
POST `https://api.mercadopago.com/v1/payments`

## Headers Requeridos
- `Authorization: Bearer APP_USR-...`
- `X-Idempotency-Key`: Clave de idempotencia unica (UUID v4) para prevenir cargos duplicados en caso de reintentos por fallas de red.

## Request Body (JSON)

```json
{
  "transaction_amount": 50000.00,
  "token": "8a7b8c9d0e1f...",
  "description": "Pago de Orden 10043",
  "installments": 1,
  "payment_method_id": "visa",
  "payer": {
    "email": "juan.perez@example.com",
    "identification": {
      "type": "CC",
      "number": "1002345678"
    }
  }
}
```

### Campos Clave de la Transaccion:
- `transaction_amount`: Monto total a cobrar (tipo float).
- `token`: El token de tarjeta generado en el frontend (`card_token`).
- `description`: Descripcion corta del pago.
- `installments`: Numero de cuotas en las que se financiara el cobro.
- `payment_method_id`: Identificador del procesador o marca (por ejemplo, `visa`, `master`, `pse`).
- `payer.email`: Correo del usuario pagador (requerido para notificaciones).

---

## Ejemplo de Respuesta (JSON)
```json
{
  "id": 9988223344,
  "date_created": "2026-08-08T12:35:00.000-04:00",
  "status": "approved",
  "status_detail": "accredited",
  "transaction_amount": 50000.00,
  "description": "Pago de Orden 10043",
  "payment_method_id": "visa",
  "installments": 1
}
```

---

## Estados de Pago en Mercado Pago
El campo `status` en la respuesta define el resultado del cobro:

- `pending`: El pago esta pendiente de aprobacion o de acreditacion (comun en metodos en efectivo como Efecty o transferencias PSE).
- `approved`: El cobro fue exitoso y el dinero fue acreditado en tu cuenta.
- `in_process`: El pago esta en analisis de prevencion de fraude (puede pasar a aprobado o rechazado en unas horas).
- `rejected`: El pago fue rechazado por el banco, falta de saldo o alerta de fraude.
- `cancelled`: El pago fue cancelado por el comprador o el comercio antes de completarse.
