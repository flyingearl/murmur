-- Runs once, the first time the data volume is created.
-- The test suite gets its own database so tests never touch your dev data.
CREATE DATABASE murmur_test OWNER murmur;
