# Wompi API — Webhooks y Notificación de Eventos

Cuando una transacción pasa a un estado final (por ejemplo, de `PENDING` a `APPROVED` o `DECLINED`), Wompi enviará una petición HTTP POST (Webhook) a la URL de eventos que hayas configurado en tu Dashboard de comercio.

## Estructura del Webhook (JSON Payload)

El payload del webhook enviado por Wompi tiene el siguiente formato JSON estandarizado:

```json
{
  "event": "transaction.updated",
  "data": {
    "transaction": {
      "id": "142385-1718001-998822",
      "created_at": "2026-08-08T05:50:00.000Z",
      "amount_in_cents": 5000000,
      "reference": "pedido-10043",
      "currency": "COP",
      "payment_method_type": "CARD",
      "payment_method": {
        "type": "CARD",
        "extra": {
          "brand": "VISA",
          "card_holder": "JUAN PEREZ",
          "last_four": "1111"
        },
        "installments": 1
      },
      "status": "APPROVED",
      "status_message": null,
      "billing_data": null
    }
  },
  "sent_at": "2026-08-08T05:54:10.000Z",
  "environment": "test",
  "signature": {
    "properties": [
      "transaction.id",
      "transaction.status",
      "transaction.amount_in_cents"
    ],
    "timestamp": 1783456789,
    "checksum": "d50a2b8e39f60bc93aa4d5e90...checksum-hex-string..."
  }
}
```

---

## Verificación de Integridad de Webhooks

Para garantizar que el webhook proviene de Wompi y no de un tercero malintencionado, **debes verificar la firma** (`checksum`) recibida dentro del objeto `signature`.

### Algoritmo de Validación:
1. **Identificar las propiedades** listadas en `signature.properties`. En el ejemplo:
   - `transaction.id` -> Valor: `"142385-1718001-998822"`
   - `transaction.status` -> Valor: `"APPROVED"`
   - `transaction.amount_in_cents` -> Valor: `5000000` (convertido a string: `"5000000"`)
2. **Concatenar en orden** estos valores junto con el timestamp (`signature.timestamp`) y el **Secreto de Integridad**:
   `Cadena = "142385-1718001-998822" + "APPROVED" + "5000000" + "1783456789" + SecretoIntegridad`
3. **Calcular el hash SHA256** de la cadena (en minúsculas hexadecimal).
4. **Comparar** el hash calculado con el valor en `signature.checksum`. Si coinciden, el webhook es auténtico.

---

## Ejemplo de Verificación en Python:

```python
import hashlib

def verificar_webhook(payload, secreto_integridad):
    signature_data = payload.get("signature", {})
    properties = signature_data.get("properties", [])
    timestamp = signature_data.get("timestamp")
    checksum_recibido = signature_data.get("checksum")
    
    # 1. Obtener valores correspondientes de data.transaction
    transaction = payload.get("data", {}).get("transaction", {})
    
    cadena_concatenada = ""
    for prop in properties:
        # Resolver ruta del campo (ej. "transaction.id" -> transaction["id"])
        field = prop.split(".")[1]
        val = transaction.get(field)
        cadena_concatenada += str(val)
        
    # 2. Concatenar timestamp y secreto de integridad
    cadena_concatenada += f"{timestamp}{secreto_integridad}"
    
    # 3. Calcular hash SHA256
    checksum_calculado = hashlib.sha256(cadena_concatenada.encode('utf-8')).hexdigest()
    
    # 4. Validar coincidencia
    return checksum_calculado == checksum_recibido
```

## Respuestas del Servidor
Tu servidor debe retornar un código de estado HTTP `200` o `201` en menos de 10 segundos. Si retorna un código de error o expira, Wompi intentará reenviar la notificación hasta 3 veces.
