#!/bin/bash

# Script para inicializar los datos de seed en todos los microservicios
# Ejecutar después de levantar docker-compose up -d

set -e
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "  📦 PASO 1: Catalog Service - Cargando productos"
echo "═══════════════════════════════════════════════════════════════════════════"
docker-compose exec -T catalog-service python seed_data.py
echo "✅ Catalog service: Datos cargados"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "  📦 PASO 2: Logistics Service - Cargando inventarios"
echo "═══════════════════════════════════════════════════════════════════════════"
docker-compose exec -T logistics-service python seed_data.py
echo "✅ Logistics service: Datos cargados"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "  📦 PASO 3: Sales Service - Cargando clientes"
echo "═══════════════════════════════════════════════════════════════════════════"
docker-compose exec -T sales-service python seed_data.py
echo "✅ Sales service: Datos cargados"