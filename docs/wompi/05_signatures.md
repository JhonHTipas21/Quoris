# Wompi API — Firmas de Integridad (Integrity Signature)

Para evitar la alteración de datos sensibles en tránsito (como cambiar el monto o la moneda en el frontend antes de enviarlo a Wompi), es obligatorio firmar digitalmente cada transacción.

## El Secreto de Integridad
El Secreto de Integridad es un valor único asignado a tu comercio que nunca debes exponer públicamente.
Puedes encontrarlo en tu Dashboard bajo *Desarrolladores > Secretos para integración técnica > Secreto de integridad (o Llave de integridad)*.

---

## Generación de la Firma de Integridad para Transacciones

Para generar la firma (`signature`) requerida en la creación de transacciones, debes seguir la siguiente fórmula:

1. **Concatenar los valores en el siguiente orden estricto sin separadores**:
   - `referencia`: La referencia de pago única generada por tu sistema.
   - `monto_en_centavos`: El valor del pago expresado en centavos de la moneda.
   - `moneda`: Código ISO de la moneda (usualmente `COP`).
   - `secreto_de_integridad`: Tu secreto de integridad obtenido del dashboard.

   Fórmula:
   `Cadena = Referencia + MontoEnCentavos + Moneda + SecretoDeIntegridad`

2. **Calcular el hash SHA256** de la cadena resultante. El resultado debe expresarse en formato hexadecimal en minúsculas.

---

## Ejemplo Práctico

### Datos de Entrada:
- Referencia: `pedido-10043`
- Monto: `5000000` ($50.000 COP)
- Moneda: `COP`
- Secreto de Integridad: `prod_integrity_XYZ123456789abcde`

### Cadena a Hashing:
`pedido-100435000000COPprod_integrity_XYZ123456789abcde`

### Código de Ejemplo en Python:
```python
import hashlib

def generar_firma_wompi(referencia, monto_centavos, moneda, secreto_integridad):
    # 1. Concatenar variables en orden estricto
    cadena = f"{referencia}{monto_centavos}{moneda}{secreto_integridad}"
    
    # 2. Calcular SHA-256 en formato hexadecimal
    firma = hashlib.sha256(cadena.encode('utf-8')).hexdigest()
    
    return firma

# Uso
firma = generar_firma_wompi("pedido-10043", 5000000, "COP", "prod_integrity_XYZ123456789abcde")
print(firma) # Imprime el hash SHA-256 de 64 caracteres hexadecimales
```

### Código de Ejemplo en Node.js (JavaScript):
```javascript
const crypto = require('crypto');

function generarFirmaWompi(referencia, montoCentavos, moneda, secretoIntegridad) {
  const cadena = `${referencia}${montoCentavos}${moneda}${secretoIntegridad}`;
  return crypto.createHash('sha256').update(cadena, 'utf8').digest('hex');
}
```
