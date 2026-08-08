# Mercado Pago API — Tokenizacion de Tarjetas

Para procesar cobros directos utilizando tarjetas de credito o debito, es obligatorio generar un token de tarjeta (Card Token) desde el frontend utilizando tu **Llave Publica** (`APP_USR-...`). Este token almacena los datos de la tarjeta de forma cifrada en los servidores de Mercado Pago, reduciendo el alcance de los requerimientos PCI-DSS de tu comercio.

## 1. Tokenizacion de Tarjeta
El frontend del comercio utiliza el script MercadoPago.js para tokenizar. Los servidores envian una solicitud HTTPS POST directa a la API de Mercado Pago.

### Endpoint
POST `https://api.mercadopago.com/v1/card_tokens`

### Query Parameters
- `public_key`: Tu llave publica de integracion (`APP_USR-...` o `TEST-...`).

### Request Body (JSON)
```json
{
  "card_number": "4509950000000001",
  "expiration_month": 12,
  "expiration_year": 2030,
  "security_code": "123",
  "cardholder": {
    "name": "Juan Perez",
    "identification": {
      "type": "CC",
      "number": "1002345678"
    }
  }
}
```

### Ejemplo de Respuesta (JSON)
```json
{
  "id": "8a7b8c9d0e1f...",
  "object": "card_token",
  "expiration_month": 12,
  "expiration_year": 2030,
  "first_six_digits": "450995",
  "last_four_digits": "0001",
  "cardholder": {
    "name": "Juan Perez",
    "identification": {
      "type": "CC",
      "number": "1002345678"
    }
  },
  "status": "active",
  "date_created": "2026-08-08T12:30:00.000-04:00",
  "date_due": "2026-08-15T12:30:00.000-04:00"
}
```

El campo `id` (`8a7b8c9d0e1f...`) es el token de tarjeta que debe enviarse inmediatamente al backend para procesar el pago.

---

## 2. Vigencia del Token de Tarjeta
Los tokens de tarjeta generados en Mercado Pago son de un solo uso y tienen una validez de 7 dias (especificado en `date_due`). Una vez que el token es utilizado en una solicitud de pago (`/v1/payments`), el token es marcado como inactivo y no puede volver a usarse. Si no es utilizado dentro de la vigencia, expira de forma automatica.
