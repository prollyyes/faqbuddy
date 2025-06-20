import re
from typing import Optional
from src.local_llm import llm_mistral

class TextToSQLConverter:
    def __init__(self):
        pass

    def create_prompt(self, question: str, schema: str) -> str:
        """
        per ora lo schema è statico, il modello lo capisce meglio cosi
        """
        prompt = f"""
You are an expert SQL assistant. Convert the following question into a valid SQL query, using ONLY the tables and columns provided in the schema below.

# DATABASE SCHEMA

CREATE TABLE Utente (
  id UUID PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  pwd_hash TEXT NOT NULL,
  nome TEXT NOT NULL,
  cognome TEXT NOT NULL
);

CREATE TABLE Insegnanti (
  id UUID PRIMARY KEY REFERENCES Utente(id),
  infoMail TEXT,
  sitoWeb TEXT,
  cv TEXT,
  ricevimento TEXT
);

CREATE TABLE Dipartimento (
  id UUID PRIMARY KEY,
  nome TEXT NOT NULL
);

CREATE TABLE Facolta (
  id UUID PRIMARY KEY,
  dipartimento_id UUID NOT NULL REFERENCES Dipartimento(id),
  presidente TEXT,
  nome TEXT NOT NULL,
  contatti TEXT
);

CREATE TABLE Corso_di_Laurea (
  id UUID PRIMARY KEY,
  id_facolta UUID NOT NULL REFERENCES Facolta(id),
  nome TEXT NOT NULL,
  descrizione TEXT,
  classe TEXT NOT NULL,
  tipologia tipoCorso NOT NULL,
  mail_segreteria TEXT,
  domanda_laurea TEXT,
  test BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE Studenti (
  id UUID PRIMARY KEY REFERENCES Utente(id),
  corso_laurea_id UUID NOT NULL REFERENCES Corso_di_Laurea(id),
  matricola INT NOT NULL
);

CREATE TABLE Corso (
  id UUID PRIMARY KEY,
  id_corso UUID NOT NULL REFERENCES Corso_di_Laurea(id),
  nome TEXT NOT NULL,
  cfu INT NOT NULL,
  idoneità BOOLEAN NOT NULL,
  prerequisiti TEXT,
  frequenza_obbligatoria TEXT
);

CREATE TABLE EdizioneCorso (
  id UUID PRIMARY KEY REFERENCES Corso(id),
  insegnante UUID NOT NULL REFERENCES Insegnanti(id),
  data semestre NOT NULL,
  orario TEXT,
  esonero BOOLEAN NOT NULL,
  mod_Esame TEXT NOT NULL
);

CREATE TABLE Corsi_seguiti (
  student_id UUID NOT NULL REFERENCES Studenti(id),
  edition_id UUID NOT NULL REFERENCES EdizioneCorso(id),
  stato attend_status NOT NULL,
  voto INT CHECK (voto BETWEEN 18 AND 31),
  PRIMARY KEY (student_id, edition_id)
);

CREATE TABLE Materiale_Didattico (
  id UUID PRIMARY KEY,
  Utente_id UUID NOT NULL REFERENCES Utente(id),
  course_id UUID NOT NULL REFERENCES Corso(id),
  path_file TEXT NOT NULL,
  tipo TEXT,
  verificato BOOLEAN NOT NULL DEFAULT false,
  data_caricamento TEXT NOT NULL DEFAULT to_char(CURRENT_DATE, 'DD/MM/YYYY'),
  rating_medio FLOAT,
  numero_voti INT
);

CREATE TABLE Valutazione (
  student_id UUID REFERENCES Studenti(id),
  id_materiale UUID REFERENCES Materiale_Didattico(id),
  voto INT NOT NULL CHECK (voto BETWEEN 1 AND 5),
  commento TEXT,
  data TEXT NOT NULL DEFAULT to_char(CURRENT_DATE, 'DD/MM/YYYY'),
  PRIMARY KEY (student_id, id_materiale)
);

CREATE TABLE Review (
  id UUID PRIMARY KEY,
  student_id UUID NOT NULL REFERENCES Studenti(id),
  edition_id UUID NOT NULL REFERENCES EdizioneCorso(id),
  descrizione TEXT,
  voto INT NOT NULL CHECK (voto BETWEEN 1 AND 5)
);

CREATE TABLE Piattaforme (
  Nome TEXT PRIMARY KEY,
  Codice TEXT
);

CREATE TABLE Tesi (
  id UUID PRIMARY KEY,
  student_id UUID NOT NULL REFERENCES Studenti(id),
  corso_laurea_id UUID NOT NULL REFERENCES Corso_di_Laurea(id),
  file TEXT NOT NULL
);

# RULES

1. Generate ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP, CREATE, ALTER)
2. Use EXACT table and column names as in the schema
3. Return ONLY the final SQL query, no explanations, comments, or extra text
4. If the question cannot be converted, return: INVALID_QUERY
5. Use table aliases (e.g., Utente u, Corso c, EdizioneCorso e)
6. For text search use LIKE with %
7. Use DISTINCT if needed
8. If the requested column does not exist, return INVALID_QUERY

# EXAMPLES

Question: "List all professors"
SQL: SELECT * FROM Insegnanti;

Question: "Show all degree courses"
SQL: SELECT * FROM Corso_di_Laurea;

Question: "Which students are enrolled in the degree course 'Ingegneria Informatica e Automatica'?"
SQL: SELECT s.* FROM Studenti s JOIN Corso_di_Laurea c ON s.corso_laurea_id = c.id WHERE c.nome LIKE '%Ingegneria Informatica e Automatica%';

Question: "Show all teaching materials for the course 'Fondamenti di Informatica'"
SQL: SELECT m.* FROM Materiale_Didattico m JOIN Corso c ON m.course_id = c.id WHERE c.nome LIKE '%Fondamenti di Informatica%';

# TASK

CONVERT THIS QUESTION:
Question: "{question}"
SQL:
"""
        return prompt

    def query_llm(self, prompt: str) -> str:
        # Usa il modello locale Mistral
        result = llm_mistral(prompt, max_tokens=150)
        # Compatibilità output (dict o string)
        if isinstance(result, dict):
            sql_response = result["choices"][0]["text"].strip()
        else:
            sql_response = result.strip() # why error?
        return sql_response

    
    
    def clean_sql_response(self, sql_response: str) -> str:
        import re
        # Cerca la query che inizia con SELECT e termina con ;
        match = re.search(r"(SELECT[\s\S]+?;)", sql_response, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Se manca il punto e virgola, prendi tutte le righe che iniziano con SELECT o continuano la query
        lines = []
        recording = False
        for line in sql_response.split('\n'):
            if line.strip().lower().startswith('select'):
                recording = True
            if recording:
                lines.append(line.strip())
        if lines:
            query = ' '.join(lines)
            if not query.endswith(';'):
                query += ';'
            return query
        return "INVALID_QUERY"