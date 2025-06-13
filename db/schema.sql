CREATE TABLE IF NOT EXISTS textbook (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    resources TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS professor (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    room VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS exam (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    professor_id INTEGER NOT NULL,
    textbook_id INTEGER NOT NULL,
    FOREIGN KEY (professor_id) REFERENCES professor(id),
    FOREIGN KEY (textbook_id) REFERENCES textbook(id)
);