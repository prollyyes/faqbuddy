-- Inserisci libri di testo
INSERT INTO textbook (title, resources) VALUES
('Introduction to Computer Science', 'https://example.com/intro-cs'),
('Data Structures and Algorithms', 'https://example.com/dsa'),
('Database Systems', 'https://example.com/db-systems'),
('Machine Learning Fundamentals', 'https://example.com/ml-fundamentals');

-- Inserisci professori
INSERT INTO professor (name, lastname, room) VALUES
('John', 'Smith', 'A101'),
('Maria', 'Johnson', 'B203'),
('Robert', 'Williams', 'C305'),
('Sarah', 'Brown', 'D407');

-- Inserisci esami
INSERT INTO exam (year, professor_id, textbook_id) VALUES
(2023, 1, 1),
(2023, 2, 2),
(2024, 3, 3),
(2024, 4, 4),
(2023, 1, 2),
(2024, 2, 3);