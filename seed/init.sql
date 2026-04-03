-- Sample source database: e-commerce system
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT UNSIGNED DEFAULT 0,
    category VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    status ENUM('pending','processing','shipped','delivered','cancelled') DEFAULT 'pending',
    total_amount DECIMAL(12,2) NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    shipped_at DATETIME NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Sample stored procedure
DELIMITER //
CREATE DEFINER='migration'@'%' PROCEDURE calc_customer_totals()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE cid INT;
    DECLARE cur CURSOR FOR SELECT id FROM customers;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    DROP TEMPORARY TABLE IF EXISTS customer_totals;
    CREATE TEMPORARY TABLE customer_totals (
        customer_id INT,
        total_spent DECIMAL(12,2),
        order_count INT
    );

    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO cid;
        IF done THEN LEAVE read_loop; END IF;
        INSERT INTO customer_totals
        SELECT cid, COALESCE(SUM(total_amount),0), COUNT(*)
        FROM orders WHERE customer_id = cid;
    END LOOP;
    CLOSE cur;

    SELECT * FROM customer_totals;
END //
DELIMITER ;

-- Seed data
INSERT INTO customers (name, email, phone) VALUES
('Alice Tan', 'alice@example.com', '+6591234567'),
('Bob Lee', 'bob@example.com', '+60123456789'),
('Charlie Wong', 'charlie@example.com', '+66812345678'),
('Diana Kumar', 'diana@example.com', '+919876543210'),
('Eve Chen', 'eve@example.com', '+6598765432');

INSERT INTO products (name, description, price, stock, category) VALUES
('Laptop Pro', '15-inch high performance laptop', 2499.99, 50, 'electronics'),
('Wireless Mouse', 'Ergonomic bluetooth mouse', 39.99, 200, 'accessories'),
('USB-C Hub', '7-port USB-C docking station', 89.99, 150, 'accessories'),
('Monitor 4K', '27-inch 4K IPS display', 599.99, 75, 'electronics'),
('Keyboard Mech', 'Mechanical keyboard RGB', 129.99, 100, 'accessories');

INSERT INTO orders (customer_id, status, total_amount, order_date) VALUES
(1, 'delivered', 2539.98, '2026-01-15 10:30:00'),
(2, 'shipped', 689.98, '2026-02-20 14:00:00'),
(3, 'pending', 39.99, '2026-03-10 09:15:00'),
(1, 'processing', 129.99, '2026-03-25 16:45:00'),
(4, 'delivered', 2499.99, '2026-01-05 11:00:00');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 2499.99),
(1, 2, 1, 39.99),
(2, 4, 1, 599.99),
(2, 3, 1, 89.99),
(3, 2, 1, 39.99),
(4, 5, 1, 129.99),
(5, 1, 1, 2499.99);

-- Grant permissions for Debezium CDC and schema discovery
GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'migration'@'%';
GRANT ALL PRIVILEGES ON source_db.* TO 'migration'@'%';
GRANT SELECT ON information_schema.* TO 'migration'@'%';
FLUSH PRIVILEGES;
