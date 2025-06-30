import pytest
from ..src.text_2_SQL import TextToSQLConverter
from ..src.utils.db_handler import DBHandler
from ..src.utils.db_utils import get_connection, MODE
import time

@pytest.fixture(scope="module")
def t2sql():
    return TextToSQLConverter()

@pytest.fixture(scope="module")
def db():
    conn = get_connection(mode=MODE)
    dbh = DBHandler(conn)
    yield dbh
    dbh.close_connection()

@pytest.fixture(scope="module")
def schema(db):
    return db.get_schema()

# --- TEST SOLO T2SQL (Text → SQL) ---
# python -m pytest -s backend/tests/test_t2sql.py::test_t2sql
@pytest.mark.parametrize("question,expected_start", [
    # ("Mostra tutte le informazioni sul corso Fondamenti di Informatica", "SELECT"),
    ("Elenca i professori che ricevono il lunedì", "SELECT"),
    ("Quali sono le tesi disponibili nel dipartimento di Informatica?", "SELECT"),
])
def test_t2sql(t2sql, schema, question, expected_start, benchmark):
    prompt = t2sql.create_prompt(question, schema)
    def generate():
        sql = t2sql.query_llm(prompt)
        cleaned = t2sql.clean_sql_response(sql)
        return cleaned

    cleaned = benchmark(generate)
    print(f"\nDomanda: {question}\nSQL generata: {cleaned}")
    assert cleaned.strip().upper().startswith(expected_start), f"La query non inizia con {expected_start}"
    assert "INVALID_QUERY" not in cleaned
    assert len(cleaned.strip()) > 10

# --- TEST SOLO SQL2T (SQL → Testo) ---
# python -m pytest -s backend/tests/test_t2sql.py::test_sql2t
@pytest.mark.parametrize("question,sql", [
    (
        "Mostra tutte le informazioni sul corso Fondamenti di Informatica",
        "SELECT * FROM Corso WHERE nome = 'Fondamenti di Informatica';"
    ),
    (
        "Elenca i professori che ricevono il lunedì",
        "SELECT u.nome, u.cognome FROM Insegnanti i JOIN Utente u ON i.id = u.id WHERE i.ricevimento ILIKE '%lunedì%';"
    ),
    (
        "Quali sono le tesi disponibili nel dipartimento di Informatica?",
        "SELECT t.* FROM Tesi t JOIN Corso_di_Laurea cl ON t.corso_laurea_id = cl.id JOIN Facolta f ON cl.id_facolta = f.id JOIN Dipartimento d ON f.dipartimento_id = d.id WHERE d.nome = 'Informatica';"
    ),
    (
        "Elenca tutti gli studenti iscritti al corso di laurea in Ingegneria Informatica",
        "SELECT u.nome, u.cognome FROM Studenti s JOIN Utente u ON s.id = u.id JOIN Corso_di_Laurea cl ON s.corso_laurea_id = cl.id WHERE cl.nome = 'Ingegneria Informatica';"
    ),
    (
        "Mostra tutti i corsi del primo semestre",
        "SELECT * FROM Corso WHERE id IN (SELECT id FROM EdizioneCorso WHERE data LIKE 'S1/%');"
    ),
    (
        "Quali corsi prevedono la frequenza obbligatoria?",
        "SELECT * FROM Corso WHERE frequenza_obbligatoria ILIKE 'si';"
    ),
    (
        "Mostra i materiali didattici verificati per il corso Fondamenti di Informatica",
        "SELECT m.* FROM Materiale_Didattico m JOIN Corso c ON m.course_id = c.id WHERE c.nome = 'Fondamenti di Informatica' AND m.verificato = TRUE;"
    ),
    (
        "Quali sono i corsi che utilizzano Moodle come piattaforma?",
        "SELECT c.nome AS corso, p.nome AS piattaforma, ep.codice FROM EdizioneCorso e JOIN Corso c ON e.id = c.id JOIN EdizioneCorso_Piattaforme ep ON e.id = ep.edizione_id JOIN Piattaforme p ON ep.piattaforma_nome = p.nome WHERE p.nome = 'Moodle';"
    ),
    (
        "Qual è la valutazione media di ogni materiale didattico verificato?",
        "SELECT m.path_file, AVG(v.voto) AS media_voti FROM Materiale_Didattico m JOIN Valutazione v ON m.id = v.id_materiale WHERE m.verificato = TRUE GROUP BY m.path_file;"
    ),
    (
        "Mostra tutti i corsi tenuti dal professor Rossi",
        "SELECT c.* FROM Corso c JOIN EdizioneCorso e ON c.id = e.id JOIN Insegnanti i ON e.insegnante = i.id JOIN Utente u ON i.id = u.id WHERE u.cognome = 'Rossi';"
    ),
])
def test_sql2t(t2sql, db, question, sql):
    time.sleep(0.25) # giusto per simulare un ritardo
    try:
        rows, columns = db.run_query(sql, fetch=True, columns=True)
        results = [dict(zip(columns, row)) for row in rows]
        print(f"\nDomanda: {question}\nSQL: {sql}\nRisultati: {results}")

        risposta = t2sql.from_sql_to_text(question, results)
        print("Risposta in linguaggio naturale:", risposta)
        assert isinstance(risposta, str)
        assert len(risposta.strip()) > 0
    except Exception as e:
        db.connection_rollback()  # Usa il metodo del tuo DBHandler
        pytest.fail(f"Errore SQL per la domanda '{question}': {e}")