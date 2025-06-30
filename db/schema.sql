------------------------------------------------
-- CREAZIONE TIPI
------------------------------------------------

CREATE TYPE attend_status AS ENUM ('attivo','completato','abbandonato');
CREATE TYPE tipoCorso AS ENUM ('Triennale','Magistrale','Ciclo unico');
CREATE DOMAIN semestre AS TEXT 
  CHECK (VALUE ~ '^(S[12])/[0-9]{4}$');
CREATE TYPE statoEdizioneCorso AS ENUM ('attivo', 'archiviato', 'annullato');

------------------------------------------------
-- 1. Utente (studenti/insegnanti)
------------------------------------------------
CREATE TABLE Utente (
  id           UUID PRIMARY KEY  DEFAULT gen_random_uuid(),
  email        TEXT  NOT NULL UNIQUE,
  pwd_hash     TEXT  NOT NULL,
  nome         TEXT  NOT NULL,
  cognome      TEXT  NOT NULL,
  email_verificata BOOLEAN NOT NULL DEFAULT FALSE -- serve per sapere se l'utente ha verificato la sua email
);

-- è una tabella con record temporanei, appena un utente è registrato viene inserito un record in questa tabella
-- e poi viene cancellato quando l'utente verifica la sua email
CREATE TABLE EmailVerification (
    user_id UUID REFERENCES Utente(id) ON DELETE CASCADE,
    token TEXT PRIMARY KEY
);

-- ho la necessità di avere sia una tabella per gli insegnanti registrati che una per gli insegnanti anagrafici,
-- perché alcuni insegnanti potrebbero non essere registrati al sito, ma avere comunque un'anagrafica.
-- e quindi voglio poter assegnare un corso anche a insegnanti non registrati.
CREATE TABLE Insegnanti_Anagrafici (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    email TEXT,
    utente_id UUID REFERENCES Utente(id) -- NULL se non registrato
);


CREATE TABLE Insegnanti_Registrati (
    id UUID PRIMARY KEY REFERENCES Utente(id) ON DELETE CASCADE,
    anagrafico_id UUID REFERENCES Insegnanti_Anagrafici(id),
    infoMail TEXT,
    sitoWeb TEXT,
    cv TEXT,
    ricevimento TEXT
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
    classe  TEXT,
    tipologia tipoCorso NOT NULL,
    mail_segreteria TEXT,
    domanda_laurea TEXT,
    test    BOOLEAN NOT NULL DEFAULT false,
    cfu_totali INT NOT NULL DEFAULT 180
);

CREATE TABLE Studenti (
  id           UUID PRIMARY KEY REFERENCES Utente(id) ON DELETE CASCADE,
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

-- Creo prima Piattaforme altrimenti EdizioneCorso non può fare riferimento

CREATE TABLE Piattaforme (
    Nome    TEXT PRIMARY KEY
);

CREATE TABLE EdizioneCorso (
    id         UUID NOT NULL REFERENCES Corso(id),
    insegnante_anagrafico UUID NOT NULL REFERENCES Insegnanti_Anagrafici(id),
    data       semestre NOT NULL,
    orario     TEXT,
    esonero    BOOLEAN NOT NULL,
    mod_Esame  TEXT NOT NULL,
    stato      statoEdizioneCorso NOT NULL DEFAULT 'attivo',
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
    edition_id UUID NOT NULL,
    edition_data semestre NOT NULL,
    stato      attend_status NOT NULL,
    voto       INT CHECK (voto BETWEEN 18 AND 31),
    PRIMARY KEY (student_id, edition_id, edition_data),
    FOREIGN KEY (edition_id, edition_data) REFERENCES EdizioneCorso(id, data) ON UPDATE CASCADE
);

------------------------------------------------
-- 3. Materiali Didattici
------------------------------------------------

CREATE TABLE Materiale_Didattico (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utente_id       UUID NOT NULL REFERENCES Utente(id),
    edition_id      UUID NOT NULL, -- (edition_id, edition_data) REFERENCES EdizioneCorso(id, data)
    edition_data    semestre NOT NULL, -- FK composta per coerenza con la PK di EdizioneCorso
    path_file       TEXT NOT NULL,
    tipo            TEXT,
    verificato      BOOLEAN NOT NULL DEFAULT false,
    data_caricamento TEXT NOT NULL DEFAULT to_char(CURRENT_DATE, 'DD/MM/YYYY'),
    rating_medio    FLOAT,
    numero_voti     INT,
    FOREIGN KEY (edition_id, edition_data) REFERENCES EdizioneCorso(id, data)
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
    edition_id UUID NOT NULL,
    edition_data semestre NOT NULL,
    descrizione TEXT,
    voto       INT NOT NULL CHECK (voto BETWEEN 1 AND 5),
    FOREIGN KEY (edition_id, edition_data) REFERENCES EdizioneCorso(id, data)
);


CREATE TABLE Tesi (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES Studenti(id),
    corso_laurea_id UUID NOT NULL REFERENCES Corso_di_Laurea(id),
    titolo     TEXT NOT NULL,
    file       TEXT NOT NULL
);

------------------------------------------------
-- Definizione Trigger
------------------------------------------------

-- Aggiorna rating_medio e numero_voti dopo INSERT o UPDATE su Valutazione
CREATE OR REPLACE FUNCTION aggiorna_rating_materiale()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Materiale_Didattico
    SET 
        rating_medio = (
            SELECT AVG(voto)::FLOAT FROM Valutazione WHERE id_materiale = NEW.id_materiale
        ),
        numero_voti = (
            SELECT COUNT(*) FROM Valutazione WHERE id_materiale = NEW.id_materiale
        )
    WHERE id = NEW.id_materiale;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Trigger per aggiornare lo stato del corso a completato se il voto è >= 18
CREATE TRIGGER trigger_aggiorna_rating_materiale
AFTER INSERT OR UPDATE OR DELETE ON Valutazione
FOR EACH ROW
EXECUTE FUNCTION aggiorna_rating_materiale();

CREATE OR REPLACE FUNCTION aggiorna_stato_corso()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.voto IS NOT NULL AND NEW.voto >= 18 THEN
        NEW.stato := 'completato';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_aggiorna_stato_corso
BEFORE INSERT OR UPDATE ON Corsi_seguiti
FOR EACH ROW
EXECUTE FUNCTION aggiorna_stato_corso();


CREATE OR REPLACE FUNCTION set_email_verificata_true()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Utente SET email_verificata = TRUE WHERE id = OLD.user_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_email_verificata_true
AFTER DELETE ON EmailVerification
FOR EACH ROW
EXECUTE FUNCTION set_email_verificata_true();

CREATE OR REPLACE FUNCTION normalize_text_fields()
RETURNS TRIGGER AS $$
BEGIN
    NEW.nome := INITCAP(LOWER(NEW.nome));
    IF NEW.cognome IS NOT NULL THEN
        NEW.cognome := INITCAP(LOWER(NEW.cognome));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_normalize_insegnanti
BEFORE INSERT OR UPDATE ON Insegnanti_Anagrafici
FOR EACH ROW
EXECUTE FUNCTION normalize_text_fields();