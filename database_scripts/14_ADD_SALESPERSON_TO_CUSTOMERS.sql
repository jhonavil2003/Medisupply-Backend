-- Add salesperson_id column to customers table
ALTER TABLE customers 
ADD COLUMN salesperson_id INTEGER;

-- Add foreign key constraint
ALTER TABLE customers 
ADD CONSTRAINT fk_customer_salesperson 
FOREIGN KEY (salesperson_id) 
REFERENCES salespersons(id) 
ON DELETE SET NULL;

-- Add index for performance
CREATE INDEX idx_customers_salesperson_id ON customers(salesperson_id);

-- Add comment to column
COMMENT ON COLUMN customers.salesperson_id IS 'Vendedor asignado al cliente';

-- ============================================================================
-- Optional: Update existing customers with a default salesperson
-- Uncomment and modify if you want to assign a default salesperson
-- ============================================================================
-- UPDATE customers 
-- SET salesperson_id = (SELECT id FROM salespersons WHERE employee_id = 'DEFAULT-SELLER' LIMIT 1)
-- WHERE salesperson_id IS NULL;

-- ============================================================================
-- Verification Query
-- ============================================================================
-- SELECT 
--     c.id,
--     c.business_name,
--     c.salesperson_id,
--     s.employee_id,
--     s.first_name || ' ' || s.last_name as salesperson_name
-- FROM customers c
-- LEFT JOIN salespersons s ON c.salesperson_id = s.id
-- LIMIT 10;
