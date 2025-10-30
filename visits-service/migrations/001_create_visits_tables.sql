-- Migración 001: Crear tablas base para visits-service (PostgreSQL)
-- Fecha: 2025-10-29
-- Descripción: Crear tablas de visitas, vendedores y archivos de visitas

-- 1. Crear enum para status de visits
DO $$ BEGIN
    CREATE TYPE visit_status AS ENUM ('SCHEDULED', 'COMPLETED', 'CANCELLED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Crear tabla salespersons
CREATE TABLE IF NOT EXISTS salespersons (
    id BIGSERIAL PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    territory VARCHAR(100),
    hire_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para salespersons
CREATE INDEX IF NOT EXISTS idx_employee_id ON salespersons (employee_id);
CREATE INDEX IF NOT EXISTS idx_active_salespersons ON salespersons (is_active);

-- 3. Crear tabla visits
CREATE TABLE IF NOT EXISTS visits (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL, -- FK a sales-service (sin constraint)
    salesperson_id BIGINT NOT NULL,
    visit_date DATE NOT NULL,
    visit_time TIME NOT NULL,
    contacted_persons TEXT,
    clinical_findings TEXT,
    additional_notes TEXT,
    address VARCHAR(500),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    status visit_status DEFAULT 'SCHEDULED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (salesperson_id) REFERENCES salespersons(id) ON DELETE RESTRICT
);

-- Crear índices para visits
CREATE INDEX IF NOT EXISTS idx_customer_visit ON visits (customer_id);
CREATE INDEX IF NOT EXISTS idx_salesperson_visit ON visits (salesperson_id);
CREATE INDEX IF NOT EXISTS idx_visit_date ON visits (visit_date);
CREATE INDEX IF NOT EXISTS idx_visit_status ON visits (status);

-- 4. Crear tabla visit_files
CREATE TABLE IF NOT EXISTS visit_files (
    id BIGSERIAL PRIMARY KEY,
    visit_id BIGINT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100),
    file_data BYTEA,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE
);

-- Crear índice para visit_files
CREATE INDEX IF NOT EXISTS idx_visit_files ON visit_files (visit_id);

-- 5. Insertar datos de ejemplo para salespersons
INSERT INTO salespersons (employee_id, first_name, last_name, email, phone, territory, hire_date, is_active) VALUES
('SELLER-001', 'Juan', 'Pérez', 'juan.perez@medisupply.com', '+57 300 1234567', 'Bogotá Norte', '2023-01-15', TRUE),
('SELLER-002', 'María', 'González', 'maria.gonzalez@medisupply.com', '+57 300 2345678', 'Bogotá Sur', '2023-03-20', TRUE),
('SELLER-003', 'Carlos', 'Rodríguez', 'carlos.rodriguez@medisupply.com', '+57 300 3456789', 'Medellín', '2023-06-10', TRUE),
('SELLER-004', 'Ana', 'López', 'ana.lopez@medisupply.com', '+57 300 4567890', 'Cali', '2023-08-05', TRUE),
('SELLER-005', 'Diego', 'Martínez', 'diego.martinez@medisupply.com', '+57 300 5678901', 'Barranquilla', '2024-01-12', TRUE)
ON CONFLICT (employee_id) DO NOTHING;

-- Confirmar migración exitosa
SELECT 'Migración 001 completada exitosamente para visits-service PostgreSQL' as status;