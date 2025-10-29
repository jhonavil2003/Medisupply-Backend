#!/bin/bash

# Script para aplicar migración de tablas de visitas
# Uso: ./apply_visits_migration.sh

echo "🔄 Aplicando migración de tablas de visitas..."

# Aplicar migración en el contenedor de base de datos
docker exec medisupply-sales-db mysql -u sales_user -psales_password sales_db < migrations/001_create_visits_tables.sql

if [ $? -eq 0 ]; then
    echo "✅ Migración aplicada exitosamente"
    echo ""
    echo "Tablas creadas:"
    echo "  - visits"
    echo "  - visit_files"
    echo ""
    echo "Para verificar las tablas:"
    echo "docker exec medisupply-sales-db mysql -u sales_user -psales_password sales_db -e 'SHOW TABLES;'"
else
    echo "❌ Error al aplicar la migración"
    exit 1
fi