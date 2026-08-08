# Mercado Pago API — Validacion de Firmas de Webhooks

Mercado Pago firma cada peticion de webhook para permitirte validar la autenticidad y el origen de los datos del evento. Las notificaciones de eventos incluyen firmas criptograficas en los encabezados HTTP que debes validar utilizando tu **Client Secret** o la clave de firma asignada en tu Dashboard de aplicaciones.

## El Encabezado x-signature
El encabezado principal utilizado para la firma es `x-signature`. Adicionalmente, se puede incluir el encabezado `x-request-id` para identificar de forma unica la notificacion.

### Estructura de x-signature
El encabezado contiene pares clave-valor indicando la firma calculada en diferentes algoritmos:
`ts=1783456800,v1=9a8b7c6d...`
- `ts`: Unix timestamp del momento del envio.
- `v1`: Hash HMAC-SHA256 calculado por Mercado Pago.

---

## Algoritmo de Verificacion de Firma

1. **Extraer variables**: Obtener el timestamp (`ts`) y el checksum (`v1`) del encabezado `x-signature`.
2. **Obtener el identificador de recurso**: Obtener la query parameter `data.id` (o la ruta correspondiente en el request) y el `id` de la notificacion.
3. **Construir la cadena a firmar**: Concatenar los campos correspondientes a la notificacion en el formato especificado por Mercado Pago.
   Formato de cadena:
   `id-del-recurso + "." + ts`
4. **Calcular HMAC-SHA256**: Generar la firma digital utilizando el algoritmo HMAC con hash SHA256, utilizando tu **Webhook Secret (Client Secret)** como llave y la cadena construida como datos.
5. **Comparacion segura**: Comparar el hash obtenido con el valor `v1` utilizando un validador de tiempo constante.

---

## Ejemplo de Validacion en Python

```python
import hmac
import hashlib

def verificar_firma_mercadopago(recurso_id: str, ts: str, x_signature_v1: str, webhook_secret: str) -> bool:
    # 1. Crear el payload de validacion concatenando el id del recurso y el timestamp
    payload = f"id:{recurso_id};request-id:{recurso_id};ts:{ts};"
    
    # 2. Calcular HMAC SHA256 usando el Webhook Secret
    signature_calculada = hmac.new(
        webhook_secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # 3. Comparacion de hashes en tiempo constante
    return hmac.compare_digest(signature_calculada, x_signature_v1)
```
