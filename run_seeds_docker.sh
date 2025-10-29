#!/bin/bash
# Script para ejecutar seeds dentro de contenedores Docker
# Ejecuta: catalog-service, logistics-service, sales-service

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                   MEDISUPPLY - SEED DE DATOS MAESTROS                     ║"
echo "║          Ejecutando seeds dentro de contenedores Docker                   ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Verificar que Docker está corriendo
echo -e "${YELLOW}🔍 Verificando Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker no está corriendo. Inicia Docker y vuelve a intentar.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker está corriendo${NC}\n"

# Verificar que los contenedores están corriendo
echo -e "${YELLOW}🔍 Verificando contenedores...${NC}"
containers=("medisupply-catalog-service" "medisupply-logistics-service" "medisupply-sales-service")

for container in "${containers[@]}"; do
    if [ "$(docker inspect -f '{{.State.Running}}' $container 2>/dev/null)" != "true" ]; then
        echo -e "${RED}❌ Contenedor $container no está corriendo.${NC}"
        echo -e "${YELLOW}   Ejecuta: docker-compose up -d${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ Todos los contenedores están corriendo${NC}\n"

# Servicios a procesar (formato: nombre|contenedor)
services=(
    "Catalog Service|medisupply-catalog-service"
    "Logistics Service|medisupply-logistics-service"
    "Sales Service|medisupply-sales-service"
)

# Variables para tracking de resultados
catalog_result=""
logistics_result=""
sales_result=""

for service in "${services[@]}"; do
    IFS='|' read -r name container <<< "$service"
    
    echo ""
    echo "================================================================================"
    echo -e "${YELLOW}🌱 Ejecutando seed para $name...${NC}"
    echo "================================================================================"
    echo ""
    
    if docker exec $container python seed_data.py; then
        echo -e "${GREEN}✅ Seed completado para $name${NC}"
        case "$name" in
            "Catalog Service") catalog_result="success" ;;
            "Logistics Service") logistics_result="success" ;;
            "Sales Service") sales_result="success" ;;
        esac
    else
        echo -e "${RED}❌ Error ejecutando seed para $name${NC}"
        case "$name" in
            "Catalog Service") catalog_result="failed" ;;
            "Logistics Service") logistics_result="failed" ;;
            "Sales Service") sales_result="failed" ;;
        esac
    fi
done

# Resumen final
echo ""
echo "================================================================================"
echo -e "${CYAN}📊 RESUMEN DE EJECUCIÓN${NC}"
echo "================================================================================"
echo ""

all_success=true

if [ "$catalog_result" == "success" ]; then
    echo -e "  Catalog Service: ${GREEN}✅ EXITOSO${NC}"
else
    echo -e "  Catalog Service: ${RED}❌ FALLIDO${NC}"
    all_success=false
fi

if [ "$logistics_result" == "success" ]; then
    echo -e "  Logistics Service: ${GREEN}✅ EXITOSO${NC}"
else
    echo -e "  Logistics Service: ${RED}❌ FALLIDO${NC}"
    all_success=false
fi

if [ "$sales_result" == "success" ]; then
    echo -e "  Sales Service: ${GREEN}✅ EXITOSO${NC}"
else
    echo -e "  Sales Service: ${RED}❌ FALLIDO${NC}"
    all_success=false
fi

echo ""
echo "================================================================================"

if [ "$all_success" = true ]; then
    echo -e "${GREEN}✅ Todos los seeds se ejecutaron exitosamente!${NC}"
    echo ""
    echo "Los siguientes datos están ahora disponibles:"
    echo "  • Catalog Service: proveedores, productos, certificaciones"
    echo "  • Logistics Service: centros de distribución, inventarios"
    echo "  • Sales Service: clientes, órdenes con items reales"
    echo ""
    echo -e "${CYAN}Puedes acceder a los servicios en:${NC}"
    echo "  • Catalog Service:   http://localhost:3001"
    echo "  • Logistics Service: http://localhost:3002"
    echo "  • Sales Service:     http://localhost:3003"
    exit_code=0
else
    echo -e "${RED}❌ Algunos seeds fallaron. Revisa los errores arriba.${NC}"
    exit_code=1
fi

echo "================================================================================"
echo ""

exit $exit_code
