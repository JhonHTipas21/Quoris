# Wompi API — Creación de Transacciones

Una vez obtenido el token del método de pago (tarjeta o Nequi) y los tokens de aceptación, puedes proceder a crear la transacción de cobro.

## Autenticación
Este endpoint requiere autenticación del lado del servidor. Debes incluir tu **Llave Privada** (`prv_...`) en las cabeceras HTTP:

```http
Authorization: Bearer prv_test_xxxxxxxxxxxxxxxxxxxxxxxx
```

## Endpoint
`POST https://sandbox.wompi.co/v1/transactions`

## Estructura del Body (JSON)

El cuerpo del JSON varía según el método de pago elegido, pero contiene campos base obligatorios:

```json
{
  "acceptance_token": "ap_test_acceptance_token_1a2b3c...",
  "accept_personal_auth": "ap_test_personal_data_auth_4d5e6f...",
  "amount_in_cents": 5000000,
  "currency": "COP",
  "signature": "calculated-integrity-signature-sha256",
  "customer_email": "juan.perez@example.com",
  "reference": "pago-pedido-100234",
  "payment_method": {
    "type": "CARD",
    "token": "tok_test_card_1234_abcde",
    "installments": 1
  },
  "customer_data": {
    "phone_number": "573000000000",
    "full_name": "Juan Perez"
  }
}
```

### Campos Base Obligatorios:
- `acceptance_token` (String): El token obtenido del GET Merchant que indica aceptación de términos.
- `accept_personal_auth` (String, Opcional/Recomendado): Token de autorización de datos personales.
- `amount_in_cents` (Integer): Monto a cobrar expresado en centavos de la moneda local (ej. 5000000 representa 50,000.00 COP).
- `currency` (String): Moneda de cobro, usualmente `COP`.
- `signature` (String): Firma de integridad (SHA256) calculada con la referencia, el monto, la moneda y tu secreto de integridad.
- `customer_email` (String): Correo electrónico del pagador.
- `reference` (String): ID de referencia único de tu comercio para identificar este pago.
- `payment_method` (Object): Detalles del método de pago a utilizar.

---

## Tipos de Métodos de Pago (`payment_method`)

### Tarjeta de Crédito (`CARD`)
```json
"payment_method": {
  "type": "CARD",
  "token": "tok_test_card_1234_abcde",
  "installments": 12
}
```

### Nequi (`NEQUI`)
```json
"payment_method": {
  "type": "NEQUI",
  "phone_number": "3991112233"
}
```
*Nota*: El pagador recibirá una notificación push en su celular con la app Nequi para aprobar la transacción.

### PSE (`PSE`)
El flujo PSE requiere datos adicionales y retorna una URL de redirección.
```json
"payment_method": {
  "type": "PSE",
  "user_type": 0,
  "user_legal_id_type": "CC",
  "user_legal_id": "1002345678",
  "financial_institution_code": "1022",
  "payment_description": "Pago Factura N. 100234"
}
```

---

## Estados de la Transacción en la Respuesta
La respuesta del endpoint contiene el estado inicial de la transacción en `data.status`:
- `PENDING`: La transacción está siendo procesada (común en Nequi, PSE o verificaciones 3D Secure).
- `APPROVED`: El cobro fue exitoso.
- `DECLINED`: La transacción fue rechazada por el procesador o banco.
- `ERROR`: Hubo un error de procesamiento interno o timeout.
