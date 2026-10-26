CREATE TABLE stock (sku text PRIMARY KEY, qty int NOT NULL, version int NOT NULL DEFAULT 0);
INSERT INTO stock VALUES ('A', 1, 0), ('B', 1, 0);
