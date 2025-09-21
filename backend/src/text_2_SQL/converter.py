from api.model_manager import model_manager
from typing import Optional


class TextToSQLConverter:
    def __init__(self):
        pass

    def create_prompt(self, question: str, schema: str) -> str:
        prompt = f"""Sei un assistente SQL esperto per database universitari.

TASK: Converti la domanda in una query SQL valida usando SOLO lo schema fornito.

REGOLE CRITICHE:
- Solo query SELECT
- Usa SOLO tabelle e colonne presenti nello schema
- NON inventare nomi, colonne o relazioni
- Se impossibile: restituisci INVALID_QUERY
- Una sola query SQL, niente commenti o spiegazioni
- Termina sempre con punto e virgola (;)

RELAZIONI CHIAVE (per JOIN):
- insegnanti_anagrafici.id → edizionecorso.insegnante_anagrafico
- corso.id → edizionecorso.id
- studenti.corso_laurea_id → corso_di_laurea.id
- studenti.id → utente.id (stesso utente)
- insegnanti_anagrafici.utente_id → utente.id
- corso_di_laurea.id_facolta → facolta.id
- facolta.dipartimento_id → dipartimento.id
- materiale_didattico.edition_id → edizionecorso.id
- review.edition_id → edizionecorso.id

ESEMPI CORRETTI (basati su schema reale):

Domanda: Elenca tutti i professori
SQL: SELECT * FROM insegnanti_anagrafici;

Domanda: Mostra tutti i corsi di laurea
SQL: SELECT * FROM corso_di_laurea;

Domanda: Mostra tutti i corsi del primo semestre
SQL: SELECT c.* FROM corso c JOIN edizionecorso e ON c.id = e.id WHERE e.data LIKE 'S1/%';

Domanda: Chi insegna il corso di Programmazione?
SQL: SELECT ia.nome, ia.cognome FROM insegnanti_anagrafici ia JOIN edizionecorso e ON ia.id = e.insegnante_anagrafico JOIN corso c ON e.id = c.id WHERE c.nome ILIKE '%programmazione%';

Domanda: Mostra le informazioni sui materiali didattici verificati
SQL: SELECT * FROM materiale_didattico WHERE verificato = true;

Domanda: Quali studenti sono iscritti a Ingegneria Informatica?
SQL: SELECT u.nome, u.cognome, s.matricola FROM studenti s JOIN utente u ON s.id = u.id JOIN corso_di_laurea cdl ON s.corso_laurea_id = cdl.id WHERE cdl.nome ILIKE '%informatica%';

Domanda: Mostra tutte le recensioni con voto superiore a 7
SQL: SELECT r.*, ia.nome, ia.cognome FROM review r JOIN edizionecorso e ON r.edition_id = e.id JOIN insegnanti_anagrafici ia ON e.insegnante_anagrafico = ia.id WHERE r.voto > 7;

SCHEMA DISPONIBILE:
{schema}

DOMANDA: {question}

SQL:"""
        return prompt

    def query_llm(self, prompt: str) -> str:
        # Ensure Gemma model is loaded
        if not model_manager.load_gemma():
            print("[ERROR] T2SQL - Failed to load Gemma model")
            return "INVALID_QUERY"
        
        # Import llm_gemma after ensuring it's loaded
        from utils.llm_gemma import llm_gemma
        
        # Check if llm_gemma is None
        if llm_gemma is None:
            print("[ERROR] T2SQL - Gemma model is None after loading")
            return "INVALID_QUERY"
        
        try:
            print(f"[SEARCH] T2SQL - Generating SQL with prompt length: {len(prompt)}")
            
            # Gemma LLM for T2SQL (better for structured tasks)
            # Use slightly higher max_tokens for complex queries
            result = llm_gemma(prompt, max_tokens=200, temperature=0.05, top_p=0.9)
            
            # Handle None result
            if result is None:
                print("[ERROR] T2SQL - LLM returned None")
                return "INVALID_QUERY"
            
            print(f"[SEARCH] T2SQL - LLM result type: {type(result)}")
            
            # Compatibilità output (dict o string)
            if isinstance(result, dict):
                if "choices" in result and len(result["choices"]) > 0:
                    sql_response = result["choices"][0]["text"].strip()
                    print(f"[OK] T2SQL - Extracted response from choices: {repr(sql_response[:100])}")
                else:
                    print(f"[ERROR] T2SQL - Invalid dict structure: {result.keys() if hasattr(result, 'keys') else 'no keys'}")
                    return "INVALID_QUERY"
            else:
                sql_response = str(result).strip()
                print(f"[OK] T2SQL - Direct string response: {repr(sql_response[:100])}")
            
            if not sql_response:
                print("[ERROR] T2SQL - Empty response from LLM")
                return "INVALID_QUERY"
                
            return sql_response
            
        except Exception as e:
            print(f"[ERROR] Error in query_llm: {e}")
            import traceback
            traceback.print_exc()
            return "INVALID_QUERY"

    def clean_sql_response(self, sql_response: str) -> str:
        import re
        
        print(f"[SEARCH] T2SQL CLEANING - Raw response: {repr(sql_response)}")
        
        # Remove common prefixes that might confuse parsing
        sql_response = re.sub(r'^(SQL:\s*|Query:\s*|Risposta:\s*)', '', sql_response.strip(), flags=re.IGNORECASE)
        
        # Strategy 1: Find complete SELECT query with semicolon (most reliable)
        match = re.search(r"(SELECT[\s\S]*?;)", sql_response, re.IGNORECASE | re.DOTALL)
        if match:
            clean_query = match.group(1).strip()
            # Remove any trailing prompt contamination after semicolon
            clean_query = re.sub(r';[\s\S]*$', ';', clean_query)
            print(f"[OK] T2SQL CLEANING - Found complete query: {repr(clean_query)}")
            return clean_query
        
        # Strategy 2: Find SELECT query that ends before prompt markers
        prompt_markers = [
            r'\s*###', r'\s*DOMANDA:', r'\s*SQL:', r'\s*SCHEMA:', 
            r'\s*REGOLE:', r'\s*ESEMPI:', r'\s*TASK:'
        ]
        for marker in prompt_markers:
            pattern = rf"(SELECT[\s\S]*?)(?:{marker}|$)"
            match = re.search(pattern, sql_response, re.IGNORECASE | re.DOTALL)
            if match:
                clean_query = match.group(1).strip()
                # Clean up and add semicolon if missing
                clean_query = re.sub(r'\s+', ' ', clean_query)  # Normalize whitespace
                if not clean_query.endswith(';'):
                    clean_query += ';'
                print(f"[OK] T2SQL CLEANING - Found query before marker: {repr(clean_query)}")
                return clean_query
        
        # Strategy 3: Multi-line SELECT (handle JOINs and complex queries)
        match = re.search(r"(SELECT[\s\S]*?)(?:\n\s*\n|\Z)", sql_response, re.IGNORECASE | re.DOTALL)
        if match:
            clean_query = match.group(1).strip()
            # Remove common trailing contamination
            clean_query = re.sub(r'\s*(DOMANDA|SQL|###).*$', '', clean_query, flags=re.IGNORECASE | re.DOTALL)
            clean_query = re.sub(r'\s+', ' ', clean_query)  # Normalize whitespace
            if not clean_query.endswith(';'):
                clean_query += ';'
            # Validate it's still a proper SELECT
            if clean_query.lower().startswith('select') and len(clean_query) > 10:
                print(f"[OK] T2SQL CLEANING - Found multi-line query: {repr(clean_query)}")
                return clean_query
        
        # Strategy 4: Single line fallback
        lines = sql_response.split('\n')
        for line in lines:
            line = line.strip()
            if line.lower().startswith('select'):
                # Clean the line of any prompt contamination
                clean_line = re.sub(r'\s*(###|DOMANDA|SQL).*$', '', line, flags=re.IGNORECASE)
                clean_line = clean_line.strip()
                if not clean_line.endswith(';'):
                    clean_line += ';'
                if len(clean_line) > 10:  # Minimum viable query length
                    print(f"[OK] T2SQL CLEANING - Using single line: {repr(clean_line)}")
                    return clean_line
        
        # Check if response contains INVALID_QUERY
        if 'INVALID_QUERY' in sql_response.upper():
            print(f"[WARN] T2SQL CLEANING - Model returned INVALID_QUERY")
            return "INVALID_QUERY"
        
        print(f"[ERROR] T2SQL CLEANING - No valid SQL found in response")
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
        Check if the SQL query is safe to execute with enhanced validation.
        Args:
            sql_query: The SQL query to check
        Returns:
            True if the query is safe, False otherwise
        """
        if not sql_query or sql_query.strip() == "INVALID_QUERY":
            return False
            
        sql = sql_query.strip().upper()
        
        # Must start with SELECT or WITH
        if not (sql.startswith("SELECT") or sql.startswith("WITH")):
            return False
        
        # Must end with semicolon
        if not sql.endswith(";"):
            return False
            
        # Forbidden keywords that could indicate malicious intent
        forbidden_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", 
            "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE"
        ]
        
        for keyword in forbidden_keywords:
            if keyword in sql:
                print(f"[WARN] T2SQL SAFETY - Forbidden keyword detected: {keyword}")
                return False
        
        # Basic syntax validation
        # Check for balanced parentheses
        if sql.count("(") != sql.count(")"):
            print(f"[WARN] T2SQL SAFETY - Unbalanced parentheses")
            return False
        
        # Check for basic SQL structure (must contain FROM)
        if "FROM" not in sql:
            print(f"[WARN] T2SQL SAFETY - No FROM clause detected")
            return False
        
        # Check minimum length (avoid trivial/malformed queries)
        if len(sql.strip()) < 15:
            print(f"[WARN] T2SQL SAFETY - Query too short: {len(sql.strip())} chars")
            return False
            
        print(f"[OK] T2SQL SAFETY - Query passed safety checks")
        return True