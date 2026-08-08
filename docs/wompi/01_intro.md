# Wompi API — Introducción y Autenticación

Wompi es la pasarela de pagos líder que permite recibir pagos de forma fácil y segura. Esta documentación técnica está diseñada para guiarte en el proceso de integración directa mediante nuestra API REST.

## Entornos (API Base URLs)

Wompi ofrece dos entornos para interactuar con la plataforma:

1. **Sandbox (Pruebas)**: Permite simular transacciones completas sin procesar dinero real.
   - URL Base: `https://sandbox.wompi.co/v1`
2. **Producción**: Para transacciones reales de tu negocio.
   - URL Base: `https://production.wompi.co/v1`

> [!IMPORTANT]
> Todos los endpoints de la API deben invocarse bajo el protocolo seguro HTTPS. Wompi rechazará de forma automática cualquier petición entrante no cifrada (HTTP).

## Credenciales de Autenticación

Para interactuar con la API de Wompi, necesitas dos tipos de llaves criptográficas que puedes encontrar en tu Dashboard de comercio (Sección *Desarrolladores > Llaves de integración*):

| Llave | Prefijo | Uso principal | Ámbito |
|---|---|---|---|
| **Llave Pública** | `pub_test_...` o `pub_prod_...` | Inicializar widgets, obtener tokens de aceptación y tokenizar tarjetas de crédito o cuentas Nequi. | Cliente (Frontend) o Servidor (Backend) |
| **Llave Privada** | `prv_test_...` o `prv_prod_...` | Crear transacciones directas, consultar estados y crear fuentes de pago recurrentes. | **Únicamente Servidor (Backend)** |

### Cabecera de Autenticación
Cuando realices peticiones que requieran tu Llave Privada, debes pasarla en el header HTTP `Authorization` usando el formato estándar Bearer Token:

```http
Authorization: Bearer prv_test_xxxxxxxxxxxxxxxxxxxxxxxx
```

> [!CAUTION]
> Tu Llave Privada (`prv_...`) da acceso total a tus transacciones y configuraciones. NUNCA la expongas en el frontend (aplicaciones móviles, javascript de navegador, etc.) o repositorios públicos.
