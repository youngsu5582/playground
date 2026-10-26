CREATE TABLE shipment (id text PRIMARY KEY, version int NOT NULL, status text NOT NULL, change_count int NOT NULL);
INSERT INTO shipment VALUES ('s1', 0, 'READY', 0);
CREATE TABLE inbox (message_id text PRIMARY KEY);
