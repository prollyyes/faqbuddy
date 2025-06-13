import requests
import re
from typing import Optional

class TextToSQLConverter:
    def __init__(self, ollama_url="http://localhost:11434", default_model="gemma3:4b"):
        self.ollama_url = ollama_url
        self.default_model = default_model

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

    def query_ollama(self, prompt: str, model: Optional[str] = None) -> str:
        if model is None:
            model = self.default_model
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 10,
                    "num_predict": 150,
                    "repeat_penalty": 1.1,
                    "stop": ["\n\n", "Domanda:", "SQL:", "```"]
                }
            },
            timeout=45
        )
        result = response.json()
        return result.get("response", "").strip()

    def clean_sql_response(self, sql_response: str) -> str:
        if not sql_response:
            return "INVALID_QUERY"
        sql_response = re.sub(r'```sql\s*', '', sql_response, flags=re.IGNORECASE)
        sql_response = re.sub(r'```\s*', '', sql_response)
        sql_response = re.sub(r'^(SQL:\s*|Query:\s*|Risposta:\s*)', '', sql_response, flags=re.IGNORECASE)
        sql_response = sql_response.strip()
        if "INVALID_QUERY" in sql_response.upper():
            return "INVALID_QUERY"
        if not sql_response.endswith(";"):
            sql_response += ";"
        return sql_response