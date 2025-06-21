import re
from typing import Optional
from src.utils.local_llm import llm_mistral
from src.utils.utils_llm import sql_results_to_text

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

    Domanda: Quali studenti sono iscritti a 'Ingegneria Informatica'?  
    SQL: SELECT s.* FROM Studenti s JOIN Corso_di_Laurea c ON s.corso_laurea_id = c.id WHERE c.nome ILIKE '%Ingegneria Informatica%';

    Domanda: Mostra i corsi offerti nel 2023  
    SQL: SELECT nome FROM Corso JOIN Corso_di_Laurea ON Corso.corso_laurea_id = Corso_di_Laurea.id WHERE Corso.semestre = 'S1/2023' OR Corso.semestre = 'S2/2023';

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
    
    
    def from_sql_to_text(self, question: str, results: list) -> str:
        """
        Convert the SQL query to a natural language response.
        
        Args:
            question: The original question asked by the user
            schema: The database schema used for the SQL query
            
        Returns:
            A natural language response based on the SQL query results
        """
        return sql_results_to_text(question, results)