------------------------------------------------
-- CLEAN SCHEMA WITH DROP STATEMENTS
------------------------------------------------

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS Tesi CASCADE;
DROP TABLE IF EXISTS Review CASCADE;
DROP TABLE IF EXISTS Valutazione CASCADE;
DROP TABLE IF EXISTS Materiale_Didattico CASCADE;
DROP TABLE IF EXISTS Corsi_seguiti CASCADE;
DROP TABLE IF EXISTS EdizioneCorso CASCADE;
DROP TABLE IF EXISTS Piattaforme CASCADE;
DROP TABLE IF EXISTS Corso CASCADE;
DROP TABLE IF EXISTS Studenti CASCADE;
DROP TABLE IF EXISTS Corso_di_Laurea CASCADE;
DROP TABLE IF EXISTS Facolta CASCADE;
DROP TABLE IF EXISTS Dipartimento CASCADE;
DROP TABLE IF EXISTS Insegnanti CASCADE;
DROP TABLE IF EXISTS Utente CASCADE;

-- Drop types and domains
DROP TYPE IF EXISTS attend_status CASCADE;
DROP TYPE IF EXISTS tipoCorso CASCADE;
DROP DOMAIN IF EXISTS semestre CASCADE;

------------------------------------------------
-- CREAZIONE TIPI
------------------------------------------------

CREATE TYPE attend_status AS ENUM ('attivo','completato','abbandonato');
CREATE TYPE tipoCorso AS ENUM ('triennale','magistrale','ciclo unico');
CREATE DOMAIN semestre AS TEXT 
  CHECK (VALUE ~ '^(S[12])/[0-9]{4}$');

------------------------------------------------
-- 1. Utente (studenti/insegnanti)
------------------------------------------------
CREATE TABLE Utente (
  id           UUID PRIMARY KEY  DEFAULT gen_random_uuid(),
  email        TEXT  NOT NULL UNIQUE,
  pwd_hash     TEXT  NOT NULL,
  nome         TEXT  NOT NULL,
  cognome      TEXT  NOT NULL
);

CREATE TABLE Insegnanti (
  id           UUID PRIMARY KEY REFERENCES Utente(id),
  infoMail     TEXT,
  sitoWeb      TEXT,
  cv           TEXT,
  ricevimento  TEXT
);

-- Student vedi dopo causa Foreign key


------------------------------------------------
-- 2. CORSI-FACOLTA-DIPARTIMENTO
------------------------------------------------

CREATE TABLE Dipartimento (
    id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome   TEXT NOT NULL
);

CREATE TABLE Facolta (
    id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dipartimento_id UUID NOT NULL REFERENCES Dipartimento(id),
    presidente TEXT,
    nome   TEXT NOT NULL,
    contatti TEXT
);

CREATE TABLE Corso_di_Laurea (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_facolta UUID NOT NULL REFERENCES Facolta(id),
    nome    TEXT NOT NULL,
    descrizione TEXT,
    classe  TEXT NOT NULL,
    tipologia tipoCorso NOT NULL,
    mail_segreteria TEXT,
    domanda_laurea TEXT,
    test    BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE Studenti (
  id           UUID PRIMARY KEY REFERENCES Utente(id),
  corso_laurea_id UUID NOT NULL REFERENCES Corso_di_Laurea(id),
  matricola    INT NOT NULL
);

CREATE TABLE Corso (
    id         UUID PRIMARY KEY  DEFAULT gen_random_uuid(),
    id_corso   UUID NOT NULL REFERENCES Corso_di_Laurea(id),
    nome       TEXT NOT NULL,
    cfu        INT NOT NULL,
    idoneità   BOOLEAN NOT NULL,
    prerequisiti TEXT,
    frequenza_obbligatoria TEXT
);

-- Piattaforme must be created before EdizioneCorso due to foreign key reference
CREATE TABLE Piattaforme (
    Nome    TEXT PRIMARY KEY
);

CREATE TABLE EdizioneCorso (
    id         UUID NOT NULL REFERENCES Corso(id),
    insegnante UUID NOT NULL REFERENCES Insegnanti(id),
    data       semestre NOT NULL,
    orario     TEXT,
    esonero    BOOLEAN NOT NULL,
    mod_Esame  TEXT NOT NULL,
    PRIMARY KEY (id, data)
);

-- Collegamento tra EdizioneCorso e Piattaforme con il codice del corso su quella piattaforma
CREATE TABLE EdizioneCorso_Piattaforme (
    edizione_id UUID NOT NULL,
    edizione_data semestre NOT NULL,
    piattaforma_nome TEXT NOT NULL REFERENCES Piattaforme(Nome),
    codice TEXT,
    PRIMARY KEY (edizione_id, edizione_data, piattaforma_nome),
    FOREIGN KEY (edizione_id, edizione_data) REFERENCES EdizioneCorso(id, data)
);

CREATE TABLE Corsi_seguiti (
    student_id UUID NOT NULL REFERENCES Studenti(id),
    edition_id UUID NOT NULL REFERENCES EdizioneCorso(id),
    stato      attend_status NOT NULL,
    voto       INT CHECK (voto BETWEEN 18 AND 31),
    PRIMARY KEY (student_id,edition_id)
);

------------------------------------------------
-- 3. Materiali Didattici
------------------------------------------------

CREATE TABLE Materiale_Didattico (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    Utente_id    UUID NOT NULL REFERENCES Utente(id),
    course_id  UUID NOT NULL REFERENCES Corso(id),    
    path_file  TEXT NOT NULL,
    tipo       TEXT,
    verificato BOOLEAN NOT NULL DEFAULT false,
    data_caricamento TEXT NOT NULL DEFAULT to_char(CURRENT_DATE, 'DD/MM/YYYY'),
    rating_medio FLOAT,
    numero_voti INT
);

CREATE TABLE Valutazione (
    student_id UUID REFERENCES Studenti(id),
    id_materiale UUID REFERENCES Materiale_Didattico(id),
    voto       INT NOT NULL CHECK (voto BETWEEN 1 AND 5),
    commento   TEXT,
    data  TEXT NOT NULL DEFAULT to_char(CURRENT_DATE, 'DD/MM/YYYY'),      

    PRIMARY KEY (student_id, id_materiale)
);

CREATE TABLE Review (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES Studenti(id),
    edition_id UUID NOT NULL REFERENCES EdizioneCorso(id),
    descrizione TEXT,
    voto       INT NOT NULL CHECK (voto BETWEEN 1 AND 5)
);

CREATE TABLE Tesi (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES Studenti(id),
    corso_laurea_id UUID NOT NULL REFERENCES Corso_di_Laurea(id),
    titolo     TEXT NOT NULL,
    file       TEXT NOT NULL
); 