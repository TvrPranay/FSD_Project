CREATE DATABASE IF NOT EXISTS id_users;
USE id_users;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    password VARCHAR(255) NOT NULL,
    pin VARCHAR(4) NOT NULL,
    barcode VARCHAR(20) NOT NULL,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS otp_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email VARCHAR(255) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    method VARCHAR(50) NOT NULL,
    date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    issue_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Open',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- NEW TABLES/COLUMNS FOR UPI ID-CARD SYSTEM
ALTER TABLE users ADD COLUMN id_card_number VARCHAR(20) UNIQUE AFTER barcode;

CREATE TABLE IF NOT EXISTS id_cards (
    id_number VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE transactions ADD COLUMN sender_id INT AFTER user_id,
ADD COLUMN receiver_id INT AFTER sender_id,
ADD COLUMN receiver_id_number VARCHAR(20) AFTER receiver_id,
ADD COLUMN status ENUM('pending', 'success', 'failed') DEFAULT 'success' AFTER method;

-- Sample data for testing
INSERT IGNORE INTO id_cards (id_number, name, verified) VALUES 
('ID123456789', 'John Doe', TRUE),
('ID987654321', 'Jane Smith', TRUE),
('ID555555555', 'Test User', FALSE);

