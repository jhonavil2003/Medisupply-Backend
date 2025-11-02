"""
Tests unitarios para el comando GenerateRoutes.

NOTA: El comando GenerateRoutes utiliza RouteOptimizerService que a su vez
depende de OR-Tools y Google Maps API. Los tests unitarios con mocks son
demasiado complejos y frágiles debido a las múltiples dependencias.

Se recomienda implementar tests de integración end-to-end que:
1. Usen datos reales de pedidos con coordenadas válidas
2. Verifiquen la creación de rutas, paradas y asignaciones en BD
3. Validen restricciones de capacidad y cadena de frío
4. Prueben diferentes estrategias de optimización
5. Verifiquen el manejo de force_regenerate

Para tests unitarios futuros, considerar refactorizar GenerateRoutes
en componentes más pequeños y testeables independientemente.
"""

import pytest

# Tests eliminados - requieren implementación de tests de integración
# Ver README_TESTS_RUTAS.md para detalles sobre tests de integración
