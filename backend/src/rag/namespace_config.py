"""
Configuration file for namespace balancing in the RAG system.
Adjust these parameters to control how the system balances between documents and database namespaces.
"""

# Default namespace boost (when no specific keywords are detected)
DEFAULT_DOCS_BOOST = 1.1  # 10% boost for documents namespace
DEFAULT_DB_BOOST = 1.0    # No boost for database namespace

# Strong boost when document keywords are detected
STRONG_DOCS_BOOST = 1.2   # 20% boost for documents
STRONG_DB_BOOST = 1.0     # No boost for database

# Strong boost when database keywords are detected  
STRONG_DB_BOOST_WHEN_DB = 1.1  # 10% boost for database
STRONG_DOCS_BOOST_WHEN_DB = 1.0  # No boost for documents

# Keywords that suggest document content (regulations, procedures, etc.)
DOCUMENT_KEYWORDS = [
    'regolamento', 'norme', 'procedure', 'requisiti', 'criteri', 'modalità',
    'scadenze', 'termini', 'documentazione', 'certificati', 'attestati',
    'esami', 'lauree', 'tesi', 'stage', 'tirocinio', 'erasmus', 'borsa',
    'contributo', 'tassa', 'pagamento', 'iscrizione', 'immatricolazione',
    'graduatoria', 'concorso', 'ammissione', 'trasferimento', 'rinuncia',
    'sospensione', 'riattivazione', 'cambio', 'opzione', 'curriculum'
]

# Keywords that suggest database/structured content (lists, contacts, etc.)
DATABASE_KEYWORDS = [
    'quali', 'elenca', 'mostra', 'lista', 'tutti', 'corsi', 'professori',
    'studenti', 'anno', 'matricola', 'insegnante', 'corso', 'email',
    'contatti', 'dipartimento', 'facoltà', 'review', 'recensioni',
    'materiale', 'edizione', 'orario', 'aula', 'sede', 'telefono',
    'indirizzo', 'sito', 'web', 'pagina', 'link', 'numero', 'codice'
]

# Minimum number of keyword matches to trigger strong boost
MIN_KEYWORD_MATCHES = 1

# Debug mode - set to True to see detailed namespace balancing info
DEBUG_MODE = True 