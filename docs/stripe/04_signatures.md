# Stripe API — Validacion de Firmas de Webhooks

Para garantizar la seguridad de tu sistema, Stripe firma digitalmente las peticiones de webhook enviadas a tu servidor. Esto evita que terceros malintencionados simulen transacciones o actualicen estados de pago de manera fraudulenta.

## El Encabezado Stripe-Signature
Cada peticion de webhook incluye un header HTTP llamado `Stripe-Signature`. Este header contiene un timestamp y una o mas firmas que debes verificar.

### Estructura del Header
El header tiene el siguiente formato:
`t=1783456800,v1=6a7b8c...`
- `t`: Timestamp Unix de la peticion.
- `v1`: Firma hexadecimal calculada por Stripe.

---

## Proceso de Validacion de Firma

Para validar la autenticidad del webhook, debes seguir estos pasos:

1. **Extraer el timestamp** (`t`) y la firma (`v1`) del header `Stripe-Signature`.
2. **Crear la cadena a firmar**: Concatenar el timestamp, el caracter punto `.` y el cuerpo completo del request JSON recibido (exactamente en formato binario/raw string, sin espacios ni formateos adicionales).
   `Cadena = Timestamp + "." + RawJSONBody`
3. **Calcular el HMAC-SHA256**: Generar la firma utilizando el algoritmo HMAC con hash SHA256, pasando la **Llave del Webhook (Webhook Secret)** (`whsec_...`) como clave y la Cadena creada en el paso anterior como datos.
4. **Comparar las firmas**: Comparar de forma segura el valor calculado con la firma `v1` extraida en el paso 1.

---

## Ejemplo de Codigo en Python

Se recomienda utilizar una funcion de comparacion de tiempo constante (evitando ataques de sincronizacion temporales).

```python
import hmac
import hashlib
import time

def verificar_firma_stripe(raw_body: bytes, stripe_signature: str, webhook_secret: str, max_age_seconds: int = 300) -> bool:
    # 1. Analizar el encabezado Stripe-Signature
    parts = dict(pair.split('=') for pair in stripe_signature.split(','))
    timestamp = parts.get('t')
    signature_v1 = parts.get('v1')
    
    if not timestamp or not signature_v1:
        return False
        
    # 2. Validar que el timestamp no sea muy antiguo (evitar ataques de repeticion)
    current_time = int(time.time())
    if current_time - int(timestamp) > max_age_seconds:
        return False
        
    # 3. Construir la firma localmente
    payload = f"{timestamp}.".encode('utf-8') + raw_body
    signature_calculada = hmac.new(
        webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # 4. Comparacion segura en tiempo constante
    return hmac.compare_digest(signature_calculada, signature_v1)
```
