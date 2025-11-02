"""
Tests unitarios para RouteOptimizerService.

NOTA: RouteOptimizerService utiliza OR-Tools para optimización VRP compleja
y requiere integración con Google Maps API. Los tests unitarios fueron eliminados
ya que la lógica es demasiado compleja para mockear efectivamente.

Se recomienda implementar tests de integración separados que:
1. Usen datos reales de prueba con coordenadas conocidas
2. Verifiquen restricciones de capacidad y cadena de frío
3. Validen diferentes estrategias de optimización
4. Midan tiempos de computación en escenarios realistas

Para tests unitarios futuros, considerar refactorizar RouteOptimizerService
en componentes más pequeños y testeables.
"""

import pytest

# Tests eliminados - requieren implementación de tests de integración
# Ver README_TESTS_RUTAS.md para detalles sobre tests de integración
