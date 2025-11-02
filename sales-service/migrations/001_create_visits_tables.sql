-- Migración 001: Crear tablas para módulo de visitas
-- Fecha: 2025-10-28
-- Descripción: Crear tablas visits y visit_files para gestión de visitas comerciales

-- ========================================
-- Tabla principal de visitas
-- ========================================
CREATE TABLE visits (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id BIGINT NOT NULL,
    salesperson_id BIGINT NOT NULL,
    visit_date DATE NOT NULL,
    visit_time TIME NOT NULL,
    contacted_persons TEXT,
    clinical_findings TEXT,
    additional_notes TEXT,
    address VARCHAR(500),
    latitude DECIMAL(10, 8),               -- Precisión para coordenadas GPS
    longitude DECIMAL(11, 8),              -- Precisión para coordenadas GPS
    status ENUM('PROGRAMADA', 'COMPLETADA', 'ELIMINADA') DEFAULT 'PROGRAMADA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Claves foráneas
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (salesperson_id) REFERENCES salespersons(id) ON DELETE SET NULL,
    
    -- Índices para optimizar consultas comunes
    INDEX idx_customer_visit (customer_id),
    INDEX idx_salesperson_visit (salesperson_id),
    INDEX idx_visit_date (visit_date),
    INDEX idx_visit_status (status),
    INDEX idx_visit_date_status (visit_date, status)  -- Índice compuesto para filtros combinados
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- Tabla para archivos adjuntos de visitas
-- ========================================
CREATE TABLE visit_files (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    visit_id BIGINT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,                      -- Tamaño en bytes
    mime_type VARCHAR(100),
    description TEXT,                      -- Descripción opcional del archivo
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Claves foráneas con eliminación en cascada
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE,
    
    -- Índices
    INDEX idx_visit_files (visit_id),
    INDEX idx_file_upload_date (uploaded_at),
    INDEX idx_file_type (mime_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- Comentarios de documentación
-- ========================================

-- Tabla visits:
-- - Almacena información de visitas comerciales a clientes
-- - Incluye coordenadas GPS para tracking de ubicación
-- - Estados: scheduled (programada), completed (completada), cancelled (cancelada)
-- - Relación muchos-a-uno con customers (un cliente puede tener muchas visitas)

-- Tabla visit_files:
-- - Almacena metadatos de archivos adjuntos a visitas
-- - Soporta múltiples archivos por visita
-- - Eliminación en cascada cuando se elimina una visita
-- - Incluye información de tamaño y tipo MIME para validaciones