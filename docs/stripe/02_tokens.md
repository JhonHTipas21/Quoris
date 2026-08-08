# Stripe API — Tokenizacion y Metodos de Pago

Para interactuar con la API de Stripe de forma segura, se debe tokenizar la informacion de pago del cliente (como los numeros de tarjeta de credito) en el lado del cliente (frontend) y enviar el identificador de pago resultante a tu servidor (backend). Esto evita que los datos de la tarjeta toquen tu servidor directamente, cumpliendo con la certificacion PCI-DSS.

## 1. Tokenizacion mediante Stripe.js
El SDK de Stripe de frontend permite convertir los datos de la tarjeta de credito en un token temporal que expira en minutos.

### Endpoint de Tokenizacion
POST `https://api.stripe.com/v1/tokens`

### Request Body (URL-encoded)
El cuerpo debe enviarse en formato `application/x-www-form-urlencoded`.
- `card[number]`: Numero de tarjeta.
- `card[exp_month]`: Mes de expiracion (2 digitos).
- `card[exp_year]`: Anio de expiracion (4 digitos).
- `card[cvc]`: Codigo de seguridad.
- `card[name]`: Nombre del titular.

### Ejemplo de Respuesta (JSON)
```json
{
  "id": "tok_1Nxi98LkdJf...",
  "object": "token",
  "card": {
    "id": "card_1Nxi98LkdJf...",
    "object": "card",
    "brand": "Visa",
    "country": "US",
    "exp_month": 12,
    "exp_year": 2030,
    "last4": "4242",
    "name": "Juan Perez"
  },
  "client_ip": "127.0.0.1",
  "created": 1783456789,
  "livemode": false,
  "used": false
}
```

---

## 2. API de Metodos de Pago (PaymentMethods)
En el flujo moderno de Stripe (Payment Intents API), se prefiere el uso de `PaymentMethods` en lugar de los antiguos tokens (`tok_...`). Un `PaymentMethod` representa un metodo de pago especifico que se asocia con un cliente para cobros unicos o recurrentes.

### Creacion de un PaymentMethod de Tarjeta
POST `https://api.stripe.com/v1/payment_methods`

### Request Body (URL-encoded)
- `type`: `card`
- `card[token]`: El token de tarjeta generado en el paso anterior (`tok_...`).

### Ejemplo de Respuesta (JSON)
```json
{
  "id": "pm_1Nxi9ALkdJf...",
  "object": "payment_method",
  "billing_details": {
    "address": null,
    "email": null,
    "name": "Juan Perez",
    "phone": null
  },
  "card": {
    "brand": "visa",
    "checks": {
      "address_line1_check": null,
      "address_postal_code_check": null,
      "cvc_check": "pass"
    },
    "country": "US",
    "exp_month": 12,
    "exp_year": 2030,
    "funding": "credit",
    "last4": "4242"
  },
  "created": 1783456800,
  "customer": null,
  "livemode": false,
  "type": "card"
}
```

El identificador del metodo de pago (`pm_...`) se utiliza en tu servidor para iniciar o confirmar intenciones de pago.
