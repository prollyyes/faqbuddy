##########################################
# INUTILIZZATO PER IL MOMENTO #
##########################################

import pandas as pd
from src.local_llm import classify_question

# Parametri
N_SIMPLE = 20
N_COMPLEX = 20

# Prompt per generare domande (puoi anche farlo manualmente o con un LLM esterno)
simple_prompts = [
    "Quanti crediti servono per iscriversi al secondo anno?",
    "Quando si svolge la sessione autunnale?",
    "Qual è la scadenza per il pagamento delle tasse universitarie?",
    "Dove si trova la segreteria studenti?",
    "Qual è il voto minimo per superare l'esame?",
    "Quanti appelli sono previsti per ogni esame?",
    "Qual è la durata di una lezione tipica?",
    "Quando scadono le iscrizioni agli esami?",
    "Qual è il numero massimo di crediti per semestre?",
    "Qual è il codice del corso di statistica?",
    "Quando inizia il semestre primaverile?",
    "Quanti studenti sono iscritti al corso?",
    "Qual è il costo della tassa di iscrizione?",
    "Qual è il sito ufficiale dell'università?",
    "Qual è il nome del preside di facoltà?",
    "Dove posso trovare il calendario accademico?",
    "Qual è la durata della sessione estiva?",
    "Qual è il termine per presentare la domanda di laurea?",
    "Qual è il numero di telefono della segreteria?",
    "Quanti anni dura il corso di laurea triennale?",
]

complex_prompts = [
    "Come posso organizzare il piano di studi per laurearmi in 3 anni?",
    "Quali esami posso sostenere in parallelo senza problemi di sovrapposizioni?",
    "Se salto l'esame di statistica a giugno, quando posso riprovare e quali sono le conseguenze?",
    "Come posso recuperare un esame non superato senza ritardare la laurea?",
    "Quali strategie posso adottare per migliorare la media voti?",
    "Come posso conciliare lavoro e studio durante il semestre?",
    "Quali sono i passi per cambiare corso di laurea senza perdere crediti?",
    "Come posso pianificare gli esami per evitare sovrapposizioni e ritardi?",
    "Quali sono i vantaggi e gli svantaggi di scegliere un curriculum internazionale?",
    "Come posso ottenere una borsa di studio e quali sono i requisiti?",
    "Quali sono le migliori strategie per preparare più esami nello stesso periodo?",
    "Come posso integrare un'esperienza di tirocinio nel mio percorso di studi?",
    "Cosa succede se non supero un esame obbligatorio entro il secondo anno?",
    "Quali sono le procedure per il riconoscimento di esami sostenuti all'estero?",
    "Come posso pianificare la laurea magistrale dopo la triennale?",
    "Quali sono le differenze tra i vari indirizzi del corso di laurea?",
    "Come posso gestire il carico di studio durante la sessione d'esami?",
    "Quali sono le opportunità di scambio internazionale e come candidarsi?",
    "Come posso recuperare crediti formativi mancanti?",
    "Quali sono i passaggi per richiedere il trasferimento ad un altro ateneo?",
]

# Etichetta automatica con LLM (puoi anche etichettare a mano)
dataset = []
for q in simple_prompts:
    """ label = classify_question(q) """  # oppure "simple" se vuoi forzare
    label = "simple"  # Forza l'etichetta per semplicità
    dataset.append({"question": q, "label": label})

for q in complex_prompts:
    """ label = classify_question(q)  """ # oppure "complex" se vuoi forzare
    label = "complex"  # Forza l'etichetta per semplicità
    dataset.append({"question": q, "label": label})

# Salva in CSV
df = pd.DataFrame(dataset)
df.to_csv("dataset_domande.csv", index=False)
print("Dataset generato e salvato in dataset_domande.csv")