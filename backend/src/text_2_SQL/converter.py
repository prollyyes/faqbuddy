from api.model_manager import model_manager
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
        SQL: SELECT * FROM Insegnanti_Anagrafici;
    
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
        SQL: SELECT ir.infoMail FROM Insegnanti_Anagrafici ia LEFT JOIN Insegnanti_Registrati ir ON ia.id = ir.anagrafico_id WHERE ia.nome = 'Roberto' AND ia.cognome = 'Baldoni';
        
        Domanda: Elenca tutti i professori di nome Roberto.
        SQL: SELECT * FROM Insegnanti_Anagrafici WHERE nome = 'Roberto';
        
        Domanda: Quali sono i professori che insegnano il corso Fondamenti di algebra e geometria?
        SQL: SELECT ia.nome, ia.cognome FROM Insegnanti_Anagrafici ia JOIN EdizioneCorso e ON ia.id = e.insegnante_anagrafico JOIN Corso c ON e.id = c.id WHERE c.nome = 'Fondamenti di algebra e geometria';
    ### SCHEMA
    {schema}

    ### DOMANDA:
    {question}

    ### SQL:"""
        return prompt

    def query_llm(self, prompt: str) -> str:
        # Ensure Gemma model is loaded
        if not model_manager.load_gemma():
            return "INVALID_QUERY"
        
        # Import llm_gemma after ensuring it's loaded
        from utils.llm_gemma import llm_gemma
        
        # Check if llm_gemma is None
        if llm_gemma is None:
            return "INVALID_QUERY"
        
        try:
            # Gemma LLM for T2SQL (better for structured tasks)
            result = llm_gemma(prompt, max_tokens=150, temperature=0.01)
            
            # Handle None result
            if result is None:
                return "INVALID_QUERY"
            
            # Compatibilità output (dict o string)
            if isinstance(result, dict):
                if "choices" in result and len(result["choices"]) > 0:
                    sql_response = result["choices"][0]["text"].strip()
                else:
                    return "INVALID_QUERY"
            else:
                sql_response = result.strip()
            return sql_response
        except Exception as e:
            print(f"[ERROR] Error in query_llm: {e}")
            return "INVALID_QUERY"

    def clean_sql_response(self, sql_response: str) -> str:
        import re
        
        print(f"[SEARCH] T2SQL CLEANING - Raw response: {repr(sql_response)}")
        
        # First, try to find a complete SELECT query with semicolon
        match = re.search(r"(SELECT[\s\S]+?;)", sql_response, re.IGNORECASE)
        if match:
            clean_query = match.group(1).strip()
            print(f"[OK] T2SQL CLEANING - Found query with semicolon: {repr(clean_query)}")
            return clean_query
            
        # Try to find SELECT query that ends at common delimiters (before prompt contamination)
        # Look for SELECT...WHERE clause that ends before ### or similar prompt markers
        match = re.search(r"(SELECT[^#]*?)(?:\s*###|\s*\n\s*###|\s*DOMANDA:|\s*SQL:|\s*$)", sql_response, re.IGNORECASE)
        if match:
            clean_query = match.group(1).strip()
            if not clean_query.endswith(';'):
                clean_query += ';'
            print(f"[OK] T2SQL CLEANING - Found query before prompt markers: {repr(clean_query)}")
            return clean_query
            
        # Fallback: extract just the first line if it starts with SELECT
        first_line = sql_response.split('\n')[0].strip()
        if first_line.lower().startswith('select'):
            # Remove any trailing prompt contamination from the first line
            clean_first_line = re.sub(r'\s*###.*$', '', first_line).strip()
            if not clean_first_line.endswith(';'):
                clean_first_line += ';'
            print(f"[OK] T2SQL CLEANING - Using cleaned first line: {repr(clean_first_line)}")
            return clean_first_line
            
        print(f"[ERROR] T2SQL CLEANING - No valid SQL found")
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
        
    # da migliorare assolutamente, forse aggiungendo tanti pattern si riescono a coprire la maggior parte delle domande (?)
    def sql_results_to_text_pattern(self, question: str, results: list) -> Optional[str]:
        import re
        if not results or not isinstance(results, list) or len(results) == 0:
            return "Nessun risultato trovato per la tua richiesta. Prova a riformulare la domanda o a visitare la nostra sezione per la ricerca manuale di informazioni."
    
        match = re.search(
            r"(quali sono|dimmi|mostra|elenca)\s+(?:tutti i\s+|tutte le\s+)?([^\?]+)",
            question.lower()
        )
        if match and isinstance(results[0], dict):
            oggetto = match.group(2).strip()
            oggetto = re.sub(r"^(tutti i|tutte le)\s+", "", oggetto, flags=re.IGNORECASE)
    
            # Prendi la prima parola significativa (escludi articoli già presenti)
            parole = oggetto.split()
            prima = parole[0]
            maschili = {"corso", "corsi", "professore", "professori", "studente", "studenti", "materiale", "esame", "esami", "dipartimento", "docente", "docenti"}
            femminili = {"informazione", "informazioni", "tesi", "facolta", "piattaforma", "piattaforme", "edizione", "edizioni"}
    
            # Se l'oggetto inizia già con un articolo, non aggiungerlo
            articoli = {"i", "il", "gli", "le", "la", "l'"}
            if prima in articoli:
                articolo = ""
            elif prima in maschili:
                articolo = "I " if prima.endswith("i") else "Il "
            elif prima in femminili:
                articolo = "Le " if prima.endswith("i") or prima.endswith("e") else "La "
            else:
                articolo = ""
    
            # Ricostruisci l'oggetto senza doppio articolo
            oggetto_finale = oggetto if articolo == "" else articolo + oggetto
    
            # Extract values and format as markdown unordered list
            valori = []
            for row in results:
                for k, v in row.items():
                    if v is not None and 'id' not in k.lower():
                        valori.append(f"- **{v}**")
                        break  # Take only the first non-ID field
            
            if valori:
                return f"{oggetto_finale.capitalize()} sono:\n" + "\n".join(valori)
            else:
                return f"Nessun risultato trovato per {oggetto}."
        return None
    
    def sql_results_to_text_llm(self, question: str, results: list) -> str:
        # Ensure Gemma model is loaded
        if not model_manager.load_gemma():
            return "Errore nel caricamento del modello per la conversione dei risultati."
        
        # Import llm_gemma after ensuring it's loaded
        from utils.llm_gemma import llm_gemma
        
        # Check if llm_gemma is None
        if llm_gemma is None:
            return "Errore: modello non disponibile per la conversione dei risultati."
        
        prompt = (
            "Rispondi in italiano in modo sintetico e diretto alla seguente domanda, "
            "usando SOLO i dati forniti qui sotto. Non aggiungere spiegazioni o ringraziamenti.\n\n"
            "FORMATTAZIONE RICHIESTA:\n"
            "- Se la risposta contiene una lista di elementi, usa una lista puntata markdown\n"
            "- Ogni elemento deve essere su una riga separata con un trattino (-)\n"
            "- NON includere 'nome:' o altri prefissi di campo\n"
            "- Esempio:\n"
            "  - Nome Corso 1\n"
            "  - Nome Corso 2\n"
            "  - Nome Corso 3\n\n"
            f"Domanda: {question}\n"
            f"Dati:\n{results}\n\n"
            "Risposta formattata:"
        )
        
        try:
            print("Fallback LLM")
            output = llm_gemma(prompt, max_tokens=1024, stop=["</s>"])
            
            # Handle None result
            if output is None:
                return "Errore nella generazione della risposta."
            
            # Handle different output formats
            if isinstance(output, dict):
                if "choices" in output and len(output["choices"]) > 0:
                    return output["choices"][0]["text"].strip()
                else:
                    return "Errore nel formato della risposta del modello."
            else:
                return str(output).strip()
        except Exception as e:
            print(f"[ERROR] Error in sql_results_to_text_llm: {e}")
            return f"Errore nella conversione dei risultati: {str(e)}"


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