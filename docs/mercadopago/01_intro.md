# MercadoPago API — Introducción y Autenticación

Mercado Pago es la pasarela de pagos líder en América Latina. Esta documentación describe el proceso de integración directa mediante la API de Mercado Pago.

## Entorno y API Base URL

Mercado Pago ofrece un entorno de pruebas (Sandbox) y un entorno de producción que se controlan mediante las credenciales utilizadas.

- URL Base Única: `https://api.mercadopago.com`

## Credenciales de Autenticación

Mercado Pago utiliza dos credenciales clave:

1. **Llave Pública (Public Key)** (`APP_USR-...`): Se utiliza en el frontend para inicializar el checkout y capturar los datos de pago de forma segura.
2. **Token de Acceso (Access Token)** (`APP_USR-...` o `TEST-...`): Se utiliza en el backend (servidor) para crear pagos, consultar reembolsos y configurar webhooks.

### Cabecera de Autenticación
Todas las peticiones a la API desde el servidor deben incluir tu Access Token en la cabecera `Authorization` como Bearer token:

```http
Authorization: Bearer TEST-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

> [!CAUTION]
> El Access Token da control total a tus cobros y transferencias. Nunca lo expongas en el cliente (frontend) ni en repositorios de código.
