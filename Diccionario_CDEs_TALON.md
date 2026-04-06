# 📖 Diccionario de Datos Críticos (CDEs) - T.A.L.O.N

Motor de Reglas y DAMA DMBOK

Este documento define las reglas de calidad de datos, pesos por dimensión y penalizaciones aplicadas por el agente T.A.L.O.N. a los diferentes dominios y tipos de materiales en SAP.

---

📦 1. MAESTRO DE MATERIALES (Reglas Específicas)

ZFER (Producto Terminado)
Pesos DAMA: Completitud (50%), Validez (30%), Unicidad (10%), Consistencia (10%)

| Dimensión | Campo (CDE) | Tipo de Regla | Pts | Mensaje / Condición |
| :--- | :--- | :--- | :--- | :--- |
| Completitud | `EAN13` | No Nulo | -100 | Falta EAN13 |
| Completitud | `cod_UEN` | No Nulo | -100 | Falta UEN |
| Validez | `UoM_peso` | Catálogo | -50 | UoM Inválida (Ref: unidades) |
| Consistencia | `peso_bruto` | Mayor/Igual | -100 | Peso Bruto menor al Neto (Ref: peso_neto) |

ZROH (Materia Prima)
Pesos DAMA: Validez (50%), Completitud (30%), Consistencia (10%), Unicidad (10%)

| Dimensión | Campo (CDE) | Tipo de Regla | Pts | Mensaje / Condición |
| :--- | :--- | :--- | :--- | :--- |
| Validez | `peso_neto` | Mayor a (0) | -100 | Peso Neto en 0 |
| Validez | `UoM_peso` | Catálogo | -100 | UoM Inválida (Ref: unidades) |

ZHAL (Semielaborado)
Pesos DAMA: Consistencia (40%), Completitud (30%), Validez (20%), Unicidad (10%)

| Dimensión | Campo (CDE) | Tipo de Regla | Pts | Mensaje / Condición |
| :--- | :--- | :--- | :--- | :--- |
| Completitud | `centro_produccion` | No Nulo | -100 | Falta Centro de Producción |
| Validez | `UoM_salida` | Catálogo | -80 | UoM de salida inválida |
| Consistencia | `cantidad_base` | Mayor a (0) | -100 | Cantidad base de formulación en 0 |

ZVER (Envase / Embalaje)
Pesos DAMA:** Completitud (40%), Validez (40%), Consistencia (10%), Unicidad (10%)

| Dimensión | Campo (CDE) | Tipo de Regla | Pts | Mensaje / Condición |
| :--- | :--- | :--- | :--- | :--- |
| Completitud | `grupo_articulos_empaque` | No Nulo | -100 | Falta Grupo de Empaque |
| Validez | `volumen` | Mayor a (0) | -100 | Volumen en 0 o negativo |
| Validez | `unidad_volumen` | Catálogo | -100 | Unidad de volumen inválida |

ZIUC (Material Controlado / Químicos)
Pesos DAMA: Completitud (40%), Validez (40%), Consistencia (10%), Unicidad (10%)

| Dimensión | Campo (CDE) | Tipo de Regla | Pts | Mensaje / Condición |
| :--- | :--- | :--- | :--- | :--- |
| Completitud | `sujeto_lote` | No Nulo | -100 | Falta indicador de gestión de lotes |
| Validez | `clase_riesgo` | Catálogo | -100 | Clase de riesgo inválida para material controlado |

ZERS (Piezas de Recambio)
Pesos DAMA: Completitud (40%), Consistencia (30%), Validez (20%), Unicidad (10%)

| Dimensión | Campo (CDE) | Tipo de Regla | Pts | Mensaje / Condición |
| :--- | :--- | :--- | :--- | :--- |
| Completitud | `num_pieza_fabricante` | No Nulo | -80 | Falta número de pieza del fabricante (MPN) |
| Consistencia | `stock_seguridad` | Mayor a (0) | -50 | Pieza de recambio sin stock de seguridad |

ZSER (Servicios)
Pesos DAMA: Completitud (40%), Validez (30%), Consistencia (20%), Unicidad (10%)

| Dimensión | Campo (CDE) | Tipo de Regla | Pts | Mensaje / Condición |
| :--- | :--- | :--- | :--- | :--- |
| Validez | `UoM_servicio` | Catálogo | -100 | UoM inválida (Debe ser Horas, Días, Actividad) |
| Consistencia | `peso_neto` | Igual a (0) | -100 | Un servicio es intangible, el peso debe ser 0 |

ZHAW (Mercadería de Reventa)
Pesos DAMA: Completitud (50%), Validez (30%), Consistencia (10%), Unicidad (10%)

| Dimensión | Campo (CDE) | Tipo de Regla | Pts | Mensaje / Condición |
| :--- | :--- | :--- | :--- | :--- |
| Completitud | `EAN13` | No Nulo | -100 | Falta EAN13 para mercadería de reventa |
| Completitud | `jerarquia_producto` | No Nulo | -100 | Falta jerarquía de producto para reportes |
| Validez | `grupo_compras` | Catálogo | -80 | Grupo de compras inválido |

---

🌐 2. MAESTRO DE MATERIALES (Reglas Transversales / Generales)
Pesos DAMA: Distribución equitativa al 25% por dimensión.

| Dimensión | Campo (CDE) | Tipo de Regla | Pts | Mensaje / Condición |
| :--- | :--- | :--- | :--- | :--- |
| Unicidad | `SKU_num` | Duplicado | -100 | SKU Duplicado |
| Unicidad | `Desc_Material` | Duplicado | -50 | Descripción Duplicada |

---

🏢 3. DIRECTORIO COMERCIAL (Clientes y Proveedores)
Pesos DAMA: Validez (40%), Completitud (30%), Unicidad (30%), Consistencia (0%)

| Dimensión | Campo (CDE) | Tipo de Regla | Pts | Mensaje / Condición |
| :--- | :--- | :--- | :--- | :--- |
| Completitud | `Nombre` | No Nulo | -40 | Nombre o Razón Social Vacío |
| Completitud | `Clave de país/región` | No Nulo | -30 | Falta la Clave de País |
| Validez | `Correo electrónico` | Formato Correo | -50 | Formato de Correo Inválido |
| Validez | `Teléfono` | Teléfono Región | -50 | Estructura Inválida (Ref: Clave país) |
| Validez | `Clave de país/región` | Longitud (2) | -40 | No es formato ISO (Debe tener 2 letras) |
| Unicidad | `Cliente` | Duplicado | -100 | ID de Cliente/Proveedor Duplicado |
| Unicidad | `Correo electrónico` | Duplicado Múltiple | -100 | Contacto Clonado (Evalúa: Correo, Dirección, Región y Población)* |

Nota: La regla de unicidad de correo contiene excepciones configuradas (Whitelist: <controldedatos@brinsa.com.co> | Blacklist: <remediacion_correo@brinsa.com.co>).
