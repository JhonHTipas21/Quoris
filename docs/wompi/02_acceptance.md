# Wompi API — Tokens de Aceptación (Acceptance Tokens)

De acuerdo con la legislación colombiana (Ley 1581 de 2012 de Habeas Data y protección de datos), es de carácter **obligatorio** que el pagador acepte de forma explícita los Términos y Condiciones, así como la Autorización de Tratamiento de Datos Personales de Wompi antes de realizar cualquier pago o registrar una fuente de pago.

Para facilitar esto en integraciones directas vía API, Wompi implementa el flujo de **Acceptance Token**.

## Paso 1: Consultar los términos vigentes
Debes realizar una petición `GET` al endpoint de comercios utilizando tu **Llave Pública** (`pub_...`) en la URL:

```http
GET https://sandbox.wompi.co/v1/merchants/pub_test_Qz8R2...
```

### Respuesta del Servidor (JSON)
```json
{
  "data": {
    "id": 1234,
    "name": "Mi Comercio Ejemplo",
    "email": "contacto@micomercio.com",
    "contact_name": "Juan Perez",
    "phone_number": "573000000000",
    "active": true,
    "presigned_acceptance": {
      "acceptance_token": "ap_test_acceptance_token_1a2b3c...",
      "permalink": "https://wompi.co/terminos-y-condiciones-de-uso-para-comercios-y-pagadores/"
    },
    "presigned_personal_data_auth": {
      "acceptance_token": "ap_test_personal_data_auth_4d5e6f...",
      "permalink": "https://wompi.co/autorizacion-de-tratamiento-de-datos-personales-pagadores/"
    }
  }
}
```

## Paso 2: Presentar los contratos al usuario
En tu frontend, debes obligatoriamente mostrar dos enlaces correspondientes a los links en `permalink`:
1. El enlace a los Términos y Condiciones.
2. El enlace a la Autorización de Tratamiento de Datos.

El usuario debe marcar un control (tipo *checkbox*) indicando que acepta voluntariamente ambos documentos.

## Paso 3: Almacenar los tokens de aceptación
Cuando el usuario presiona "Pagar", debes capturar los tokens que obtuviste en el Paso 1:
- `presigned_acceptance.acceptance_token` (términos generales).
- `presigned_personal_data_auth.acceptance_token` (tratamiento de datos personales).

Estos tokens deben enviarse en el cuerpo del request al crear una transacción o registrar un método de pago. La ausencia de estos tokens causará un error de validación `422 Unprocessable Entity`.
