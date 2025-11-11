# 🌱 Guía de Poblado de Datos - Medisupply Backend

Esta guía explica cómo poblar las bases de datos de todos los microservicios con datos de prueba consistentes.

## 📋 Prerrequisitos

1. **Docker Desktop** debe estar corriendo
2. **Contenedores levantados** con `docker-compose up -d`
3. Verificar que los contenedores estén activos:
   ```powershell
   docker ps
   ```
   Debes ver: `medisupply-catalog-service`, `medisupply-logistics-service`, `medisupply-sales-service`

## 📦 Estructura de Archivos

```
Medisupply-Backend/
├── shared_seed_data.py           # Datos compartidos entre servicios
├── catalog-service/
│   └── seed_data.py              # Script de seed para catalog
├── logistics-service/
│   └── seed_data.py              # Script de seed para logistics
└── sales-service/
    └── seed_data.py              # Script de seed para sales
```

## 🎯 Datos Disponibles en `shared_seed_data.py`

### Proveedores (3)
- MedEquip Solutions (Colombia)
- PharmaTech International (USA)
- BioMedical Supplies (Perú)

### Productos (14)
- Jeringas (3 tipos)
- Guantes (2 tipos)
- Vacunas e insulinas (con cadena de frío)
- Equipos médicos (oxímetros, tensiómetros, termómetros)
- Protección personal (mascarillas N95)
- Material de curación (gasas, vendajes, alcohol)

### Centros de Distribución (3)
- CEDIS-BOG (Bogotá) - Con cadena de frío
- CEDIS-MED (Medellín) - Con cadena de frío
- CEDIS-CALI (Cali) - Sin cadena de frío

### Clientes (5)
- Hospitales (San Ignacio, Pablo Tobón Uribe)
- Clínicas (El Bosque)
- Farmacias (Cruz Verde)
- Distribuidores (Dismeva)

### Vendedores (8)
- 7 activos distribuidos en 4 regiones (Norte, Sur, Este, Oeste)
- 1 inactivo (para pruebas)

### Metas de Vendedores (19)
- Distribuidas en Q1, Q2, Q3
- Tipos: monetarias (8) y unidades (11)
- Por región: Norte (6), Sur (5), Este (3), Oeste (5)

## 🚀 Opción 1: Poblado Manual por Servicio

### 1️⃣ Poblar Catalog Service (Productos)

```powershell
# Copiar archivos al contenedor
docker cp shared_seed_data.py medisupply-catalog-service:/app/shared_seed_data.py
docker cp catalog-service/seed_data.py medisupply-catalog-service:/app/seed_data.py

# Ejecutar seed
docker exec medisupply-catalog-service python seed_data.py
```

**Resultado esperado:**
```
✅ 3 proveedores creados
✅ 14 productos creados
```

---

### 2️⃣ Poblar Logistics Service (Inventario)

```powershell
# Copiar archivos al contenedor
docker cp shared_seed_data.py medisupply-logistics-service:/app/shared_seed_data.py
docker cp logistics-service/seed_data.py medisupply-logistics-service:/app/seed_data.py

# Ejecutar seed
docker exec medisupply-logistics-service python seed_data.py
```

**Resultado esperado:**
```
✅ 3 centros de distribución creados
✅ 28 registros de inventario creados
✅ 16 ubicaciones de bodega creadas
✅ 58 lotes de productos creados
✅ 9 vehículos creados
```

---

### 3️⃣ Poblar Sales Service (Ventas y Vendedores)

```powershell
# Copiar archivos al contenedor
docker cp shared_seed_data.py medisupply-sales-service:/app/shared_seed_data.py
docker cp sales-service/seed_data.py medisupply-sales-service:/app/seed_data.py

# Ejecutar seed
docker exec medisupply-sales-service python seed_data.py
```

**Resultado esperado:**
```
✅ 5 clientes creados
✅ 8 vendedores creados
✅ 19 metas de vendedores creadas
```

---

## 🎬 Opción 2: Poblado Automatizado (Todos los Servicios)

### Usando Git Bash (Recomendado)

```bash
./run_seeds_docker.sh
```

### Usando PowerShell (Comandos Manuales)

```powershell
# Ejecutar seeds en orden
docker exec medisupply-catalog-service python seed_data.py
docker exec medisupply-logistics-service python seed_data.py
docker exec medisupply-sales-service python seed_data.py
```

---

## ✅ Verificación de Datos

### Verificar Catalog Service
```powershell
# Ver productos
docker exec medisupply-catalog-service sh -c "python -c 'from src.main import create_app; from src.models.product import Product; app = create_app(); app.app_context().push(); print(f\"Productos: {Product.query.count()}\")'"
```

### Verificar Logistics Service
```powershell
# Ver inventarios
docker exec medisupply-logistics-service sh -c "python -c 'from src.main import create_app; from src.models.inventory import Inventory; app, _ = create_app(); app.app_context().push(); print(f\"Inventarios: {Inventory.query.count()}\")'"
```

### Verificar Sales Service
```powershell
# Ver vendedores y metas
docker exec medisupply-sales-service sh -c "python -c 'from src.main import create_app; from src.entities.salesperson import Salesperson; from src.entities.salesperson_goal import SalespersonGoal; app = create_app(); app.app_context().push(); print(f\"Vendedores: {Salesperson.query.count()}, Metas: {SalespersonGoal.query.count()}\")'"
```

---

## 🔄 Re-poblar Datos (Limpiar y Volver a Cargar)

Si necesitas limpiar y volver a poblar los datos:

```powershell
# Los scripts seed_data.py automáticamente limpian datos existentes antes de crear nuevos
docker exec medisupply-catalog-service python seed_data.py
docker exec medisupply-logistics-service python seed_data.py
docker exec medisupply-sales-service python seed_data.py
```

Cada script ejecuta un `clear_data()` que elimina registros anteriores antes de insertar nuevos.

---

## 🌐 Acceso a los Servicios

Después del poblado, los servicios estarán disponibles en:

- **Catalog Service**: http://localhost:3001
- **Logistics Service**: http://localhost:3002
- **Sales Service**: http://localhost:3003

### Endpoints de Prueba

```bash
# Listar productos
curl http://localhost:3001/api/products

# Listar inventarios
curl http://localhost:3002/api/inventory

# Listar vendedores
curl http://localhost:3003/api/salespersons

# Listar metas de vendedores
curl http://localhost:3003/api/salesperson-goals
```

---

## 📊 Resumen de Datos Poblados

| Servicio | Entidad | Cantidad |
|----------|---------|----------|
| **Catalog** | Proveedores | 3 |
| **Catalog** | Productos | 14 |
| **Logistics** | Centros de Distribución | 3 |
| **Logistics** | Registros de Inventario | 28 |
| **Logistics** | Ubicaciones de Bodega | 16 |
| **Logistics** | Lotes de Productos | 58 |
| **Logistics** | Vehículos | 9 |
| **Sales** | Clientes | 5 |
| **Sales** | Vendedores | 8 |
| **Sales** | Metas de Vendedores | 19 |

---

## 🐛 Troubleshooting

### Error: "Docker no está corriendo"
```bash
# Solución: Iniciar Docker Desktop y esperar a que esté completamente activo
```

### Error: "Contenedor no está corriendo"
```powershell
# Solución: Levantar los contenedores
docker-compose up -d
```

### Error: "No such file or directory: seed_data.py"
```powershell
# Solución: Copiar los archivos primero
docker cp shared_seed_data.py medisupply-<servicio>:/app/
docker cp <servicio>/seed_data.py medisupply-<servicio>:/app/
```

### Error: "Import Error" o "Module not found"
```powershell
# Solución: Verificar que shared_seed_data.py esté copiado en el contenedor
docker exec medisupply-<servicio> ls -la /app/shared_seed_data.py
```

---

## 📝 Notas Importantes

1. **Orden de ejecución**: Se recomienda poblar en este orden:
   - Primero: Catalog (productos)
   - Segundo: Logistics (inventarios)
   - Tercero: Sales (vendedores y metas)

2. **Consistencia de datos**: El archivo `shared_seed_data.py` garantiza que los SKUs de productos, IDs de centros de distribución y employee_ids sean consistentes entre servicios.

3. **Datos de prueba**: Todos los datos son ficticios y diseñados para pruebas de desarrollo.

4. **Cadena de frío**: Los productos `VAC-COVID-PF` e `INS-HUMAN-R` requieren cadena de frío y solo se almacenan en centros que la soportan (Bogotá y Medellín).

5. **Metas de vendedores**: Las metas están vinculadas a:
   - Vendedores existentes (employee_id)
   - Productos existentes (SKU)
   - Regiones válidas (Norte, Sur, Este, Oeste)
   - Trimestres (Q1, Q2, Q3, Q4)

---

## 🎯 Próximos Pasos

Después de poblar los datos:

1. ✅ Probar endpoints de la API
2. ✅ Verificar integración entre servicios
3. ✅ Ejecutar tests automatizados
4. ✅ Validar consultas de productos desde sales-service a catalog-service

---

**Última actualización**: Noviembre 2025
**Autor**: Equipo Medisupply
