import re
from typing import Optional
from src.local_llm import llm_mistral

class TextToSQLConverter:
    def __init__(self):
        pass

    def create_prompt(self, question: str, schema: str) -> str:
        prompt = f"""
# RUOLO

Sei un esperto di SQL specializzato nella conversione di domande in linguaggio naturale in query SQL precise e corrette.

# SCHEMA DEL DATABASE

{schema}

# REGOLE

1. Genera ESCLUSIVAMENTE query SELECT - sono VIETATE query INSERT, UPDATE, DELETE, DROP, CREATE, ALTER
2. Usa ESATTAMENTE i nomi delle tabelle e colonne come mostrati nello schema sopra
3. Restituisci SOLO la query SQL finale, senza spiegazioni, commenti o testo aggiuntivo
4. Se la domanda non può essere convertita in SQL valido, restituisci esattamente: INVALID_QUERY
5. Usa sempre alias per le tabelle (es: professor p, textbook t, exam e)
6. Per ricerche testuali usa LIKE con % quando appropriato
7. Usa DISTINCT quando necessario per evitare duplicati

# PATTERN COMUNI:
- Elenco di tutti i professori: SELECT * FROM professor;
- Elenco di tutti i libri: SELECT * FROM textbook;
- Esami di un certo anno: SELECT * FROM exam WHERE year = 2024;
- Nome e cognome dei professori che hanno tenuto esami nel 2024: SELECT DISTINCT p.name, p.lastname FROM professor p JOIN exam e ON p.id = e.professor_id WHERE e.year = 2024;
- Titolo dei libri usati negli esami del 2023: SELECT DISTINCT t.title FROM textbook t JOIN exam e ON t.id = e.textbook_id WHERE e.year = 2023;

# ESEMPI:
Domanda: "Elenca tutti i professori"
SQL: SELECT * FROM professor;

Domanda: "Mostra tutti i libri"
SQL: SELECT * FROM textbook;

Domanda: "Quali esami ci sono nel 2024?"
SQL: SELECT * FROM exam WHERE year = 2024;

Domanda: "Quali professori hanno tenuto esami nel 2024?"
SQL: SELECT DISTINCT p.name, p.lastname FROM professor p JOIN exam e ON p.id = e.professor_id WHERE e.year = 2024;

Domanda: "Quali libri sono stati usati negli esami del 2023?"
SQL: SELECT DISTINCT t.title FROM textbook t JOIN exam e ON t.id = e.textbook_id WHERE e.year = 2023;

# OBIETTIVO

CONVERTI QUESTA DOMANDA:
Domanda: "{question}"
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