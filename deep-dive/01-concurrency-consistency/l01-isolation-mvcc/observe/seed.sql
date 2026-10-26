CREATE TABLE account (id int PRIMARY KEY, balance int NOT NULL);
INSERT INTO account VALUES (1, 100);
CREATE TABLE on_call (doctor text PRIMARY KEY, on_call boolean NOT NULL);
INSERT INTO on_call VALUES ('alice', true), ('bob', true);
