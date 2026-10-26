CREATE TABLE jobs (id int PRIMARY KEY, status text NOT NULL DEFAULT 'pending', claimed_by text);
INSERT INTO jobs (id) VALUES (1), (2), (3);
CREATE TABLE account (id int PRIMARY KEY, balance bigint NOT NULL CHECK (balance >= 0));
INSERT INTO account VALUES (1, 100), (2, 100);
CREATE TABLE parent (id int PRIMARY KEY, name text NOT NULL);
INSERT INTO parent VALUES (1, 'orig');
CREATE TABLE child (id int PRIMARY KEY, parent_id int NOT NULL REFERENCES parent (id));
