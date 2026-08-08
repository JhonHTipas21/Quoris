# Wompi API — Tokenización (Tarjetas y Nequi)

Para realizar cargos directos sobre tarjetas de crédito o cuentas de billeteras virtuales como Nequi de forma segura (sin que los datos de pago pasen de forma desprotegida por tus servidores), debes tokenizar la información del método de pago.

## 1. Tokenización de Tarjetas de Crédito
Envía los datos de la tarjeta directamente a Wompi. Este request debe realizarse preferiblemente desde el cliente usando tu **Llave Pública** (`pub_...`) en las cabeceras.

### Endpoint
`POST https://sandbox.wompi.co/v1/tokens/cards`

### Body (JSON)
```json
{
  "number": "4111111111111111",
  "cvc": "123",
  "exp_month": "12",
  "exp_year": "30",
  "card_holder": "JUAN PEREZ"
}
```

### Respuesta del Servidor (JSON)
```json
{
  "status": "CREATED",
  "data": {
    "id": "tok_test_card_1234_abcde...",
    "created_at": "2026-08-08T05:50:00.000Z",
    "brand": "VISA",
    "last_four": "1111",
    "exp_month": "12",
    "exp_year": "30",
    "card_holder": "JUAN PEREZ",
    "valid": true
  }
}
```

El campo `data.id` (`tok_test_card_...`) es el token que pasarás en la creación de la transacción.

---

## 2. Tokenización de Nequi
Permite a los pagadores pagar usando su número de celular asociado a Nequi.

### Endpoint
`POST https://sandbox.wompi.co/v1/tokens/nequi`

### Body (JSON)
```json
{
  "phone_number": "3991112233"
}
```

### Respuesta del Servidor (JSON)
```json
{
  "status": "CREATED",
  "data": {
    "id": "tok_test_nequi_3991112233...",
    "created_at": "2026-08-08T05:50:00.000Z",
    "phone_number": "3991112233",
    "valid": true
  }
}
```

El token generado (`tok_test_nequi_...`) se debe usar inmediatamente en la creación de transacciones.
