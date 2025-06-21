from src.utils.local_llm import llm_mistral
from typing import Optional

class TextToSQLConverter:
    def __init__(self):
        pass

    def create_prompt(self, question: str, schema: str) -> str:
        prompt = f"""
    Sei un assistente SQL esperto.

    Il tuo compito è: **convertire la domanda seguente in una query SQL valida e corretta**, utilizzando **solo** lo schema fornito.

    ### Regole
    - Solo query di tipo SELECT.
    - Usa solo colonne e tabelle presenti nello schema.
    - Non inventare nomi di colonne, ruoli, o filtri.
    - Se la domanda non è possibile, restituisci: INVALID_QUERY
    - Niente testo extra, commenti o spiegazioni.

    ### Esempi

    Domanda: Elenca tutti i professori
    SQL: SELECT * FROM Insegnanti;

    Domanda: Mostra tutti i corsi di laurea  
    SQL: SELECT * FROM Corso_di_Laurea;

    Domanda: Mostra tutti i corsi del primo semestre  
    SQL: SELECT c.nome FROM Corso c JOIN EdizioneCorso e ON c.id = e.id WHERE e.data LIKE 'S1/%';
    
    Domanda: Mostra tutte le informazioni sul corso Fondamenti di Informatica
    SQL: SELECT * FROM Corso WHERE nome = 'Fondamenti di Informatica';
    
    Domanda: Quali sono i corsi di Ingegneria Informatica ?  
    SQL: SELECT Corso.nome FROM Corso JOIN Corso_di_Laurea ON Corso.id_corso = Corso_di_Laurea.id WHERE Corso_di_Laurea.nome = 'Ingegneria Informatica' OR Corso_di_Laurea.nome = 'Ingegneria Informatica e Automatica';

    Domanda: Mostra i corsi offerti nel 2023  
    SQL: SELECT Corso.nome FROM Corso JOIN Corso_di_Laurea ON Corso.id_corso = Corso_di_Laurea.id WHERE Corso.semestre = 'S1/2023' OR Corso.semestre = 'S2/2023';

    Domanda: Qual'è la mail del professore 'Roberto Baldoni'?
    SQL: SELECT infoMail FROM Insegnanti JOIN Utente ON Insegnanti.id = Utente.id WHERE nome = 'Roberto' AND cognome = 'Baldoni';
    
    Domanda: Elenca tutti i professori di nome Roberto.
    SQL: SELECT * FROM Insegnanti JOIN Utente ON Insegnanti.id = Utente.id WHERE nome = 'Roberto';
    ### SCHEMA
    {schema}

    ### DOMANDA:
    {question}

    ### SQL:"""
        return prompt

    def query_llm(self, prompt: str) -> str:
        # Mistral LLM
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

    def from_sql_to_text(self, question: str, results: list) -> str:
        """
        Convert the SQL query to a natural language response.
        
        Args:
            question: The original question asked by the user
            schema: The database schema used for the SQL query
            
        Returns:
            A natural language response based on the SQL query results
        """
        risposta = self.sql_results_to_text_pattern(question, results)
        if risposta is not None:
            return risposta
        return self.sql_results_to_text_llm(question, results)
        
    # da migliorare assolutamente, forse agguingendo tanti pattern si riescono a coprire la maggior parte delle domande (?)
    def sql_results_to_text_pattern(self, question: str, results: list) -> Optional[str]:
        import re
        # Primo: pattern "quali sono ... di ..."
        match = re.search(r"(quali sono|dimmi|mostra|elenca)\s+([^\?]+?)\s+di\s+([\w\s']+)", question.lower())
        if match and results and isinstance(results[0], dict):
            oggetto = match.group(2).strip()
            ambito = match.group(3).strip()
            frasi = []
            for row in results:
                parti = [f"{k}: {v}" for k, v in row.items() if v is not None]
                frase = ", ".join(parti)
                if frase:
                    frasi.append(frase)
            if frasi:
                return f"I {oggetto} di {ambito} sono:\n- " + "\n- ".join(frasi)
            else:
                return f"Nessun risultato trovato per {oggetto} di {ambito}."
        # Secondo: pattern "mostra/elenca/dimmi/quali sono tutti i ..."
        match2 = re.search(r"(quali sono|dimmi|mostra|elenca)\s+tutti i\s+([^\?]+)", question.lower())
        if match2 and results and isinstance(results[0], dict):
            oggetto = match2.group(2).strip()
            frasi = []
            for row in results:
                parti = [f"{k}: {v}" for k, v in row.items() if v is not None]
                frase = ", ".join(parti)
                if frase:
                    frasi.append(frase)
            if frasi:
                return f"Tutti i {oggetto} sono:\n- " + "\n- ".join(frasi)
            else:
                return f"Nessun risultato trovato per {oggetto}."
        return None
    
    def sql_results_to_text_llm(self, question: str, results: list) -> str:
        prompt = (
            "Rispondi in italiano in modo sintetico e diretto alla seguente domanda, "
            "usando SOLO i dati forniti qui sotto. Non aggiungere spiegazioni o ringraziamenti.\n\n"
            f"Domanda: {question}\n"
            f"Dati:\n{results}\n\n"
            "Risposta breve:"
        )
        output = llm_mistral(prompt, max_tokens=60, stop=["</s>"])
        return output["choices"][0]["text"].strip()


    def is_sql_safe(self, sql_query: str) -> bool:
        """
        Check if the SQL query is safe to execute.
        Args:
            sql_query: The SQL query to check
        Returns:
            True if the query is safe, False otherwise
        """
        sql = sql_query.strip().upper()
        return sql.startswith("SELECT") or sql.startswith("WITH")