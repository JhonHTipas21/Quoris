# Stripe API — Introducción y Autenticación

Stripe es una pasarela de pagos global. Esta documentación describe el proceso de integración directa mediante la API de Stripe.

## Entornos y API Base URL

Stripe no utiliza URLs diferentes para sandbox y producción. En su lugar, el entorno se determina por la llave API (Key) que utilices:

- URL Base Única: `https://api.stripe.com/v1`

## Credenciales de Autenticación

Stripe utiliza dos tipos de llaves:

1. **Llave Publicable (Publishable Key)** (`pk_test_...` / `pk_live_...`): Se utiliza en el cliente (frontend) para tokenizar tarjetas utilizando Stripe.js.
2. **Llave Secreta (Secret Key)** (`sk_test_...` / `sk_live_...`): Se utiliza en el servidor (backend) para realizar cargos, reembolsos y administrar suscripciones.

### Cabecera de Autenticación
Todas las peticiones a la API desde el servidor deben incluir la llave secreta en la cabecera `Authorization` como Bearer token:

```http
Authorization: Bearer sk_test_51Nx...
```

> [!CAUTION]
> Tu Llave Secreta (`sk_...`) da control total a tus fondos. Nunca la expongas en clientes frontend ni repositorios de código abiertos.
