#!/bin/bash

# Script para aplicar migración de salespersons y actualizar visits
# Uso: ./apply_salespersons_migration.sh

echo "🔄 Aplicando migración de salespersons y actualización de visits..."

# Verificar si el contenedor está corriendo
if ! docker ps | grep -q "medisupply-sales-db"; then
    echo "⚠️  El contenedor de base de datos no está corriendo."
    echo "Por favor ejecuta: docker-compose up -d"
    exit 1
fi

# Aplicar migración en el contenedor de base de datos
docker exec medisupply-sales-db mysql -u sales_user -psales_password sales_db < migrations/002_create_salespersons_update_visits.sql

if [ $? -eq 0 ]; then
    echo "✅ Migración aplicada exitosamente"
    echo ""
    echo "Tablas actualizadas:"
    echo "  - salespersons (nueva)"
    echo "  - visits (actualizada con FK a salespersons)"
    echo "  - visit_files (recreada)"
    echo ""
    echo "Datos de ejemplo insertados:"
    echo "  - 5 vendedores de ejemplo"
    echo ""
    echo "Para verificar las tablas:"
    echo "docker exec medisupply-sales-db mysql -u sales_user -psales_password sales_db -e 'SHOW TABLES;'"
    echo ""
    echo "Para verificar vendedores:"
    echo "docker exec medisupply-sales-db mysql -u sales_user -psales_password sales_db -e 'SELECT employee_id, CONCAT(first_name, \" \", last_name) as name, territory FROM salespersons;'"
else
    echo "❌ Error al aplicar la migración"
    exit 1
fi