import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib
from ml_utils import extract_features
import numpy as np
import os

# Dataset base (espandilo con più esempi reali!)
data = [
    # Simple
    {"question": "Quanti crediti vale il corso di informatica?", "label": "simple"},
    {"question": "Quando si tiene l'esame di matematica 2?", "label": "simple"},
    {"question": "Qual è l'aula della lezione di diritto?", "label": "simple"},
    {"question": "Chi è il docente di economia politica?", "label": "simple"},
    {"question": "Qual è la durata della prova scritta?", "label": "simple"},
    {"question": "Qual è il codice del corso di statistica?", "label": "simple"},
    {"question": "Quanti appelli ci sono a luglio?", "label": "simple"},
    {"question": "Quando inizia il semestre primaverile?", "label": "simple"},
    {"question": "Qual è il voto minimo per superare l'esame?", "label": "simple"},
    {"question": "Dove si trova la segreteria studenti?", "label": "simple"},
    {"question": "Qual è il numero massimo di crediti per semestre?", "label": "simple"},
    {"question": "Quando scadono le iscrizioni agli esami?", "label": "simple"},
    {"question": "Qual è la durata di una lezione tipica?", "label": "simple"},
    {"question": "Quanti studenti sono iscritti al corso?", "label": "simple"},
    {"question": "Dove posso trovare il calendario accademico?", "label": "simple"},
    # Complex
    {"question": "Come posso organizzare il piano di studi per laurearmi in 3 anni?", "label": "complex"},
    {"question": "Quali esami posso sostenere in parallelo senza problemi di sovrapposizioni?", "label": "complex"},
    {"question": "Se salto l'esame di statistica a giugno, quando posso riprovare e quali sono le conseguenze?", "label": "complex"},
    {"question": "Posso laurearmi in 3 anni?", "label": "complex"},
    {"question": "Posso superare il test di economia studiando solo 2 ore? E 3? E 4?", "label": "complex"},
    {"question": "Come posso recuperare un esame non superato senza ritardare la laurea?", "label": "complex"},
    {"question": "Quali strategie posso adottare per migliorare la media voti?", "label": "complex"},
    {"question": "Come posso conciliare lavoro e studio durante il semestre?", "label": "complex"},
    {"question": "Quali sono i passi per cambiare corso di laurea senza perdere crediti?", "label": "complex"},
    {"question": "Come posso pianificare gli esami per evitare sovrapposizioni e ritardi?", "label": "complex"},
    {"question": "Quali sono i prerequisiti per economia applicata?", "label": "complex"},
    {"question": "Come posso evitare il sovraccarico di esami in un semestre?", "label": "complex"},
    {"question": "Quali sono i vantaggi e gli svantaggi di scegliere un curriculum internazionale?", "label": "complex"},
    {"question": "Come posso gestire eventuali problemi di propedeuticità tra esami?", "label": "complex"},
    {"question": "Quali soluzioni ci sono se due esami obbligatori si sovrappongono?", "label": "complex"},
]

# Carica il CSV generato automaticamente, se esiste
csv_path = "dataset_domande.csv"
if os.path.exists(csv_path):
    df_csv = pd.read_csv(csv_path)
    print(f"Caricato {csv_path} con {len(df_csv)} domande.")
else:
    df_csv = pd.DataFrame(columns=["question", "label"])
    print(f"Attenzione: {csv_path} non trovato, uso solo dataset base.")

# Unisci i due dataset
df_original = pd.DataFrame(data)
df = pd.concat([df_original, df_csv], ignore_index=True)
print(f"Totale domande in training: {len(df)}")

# Estrai feature e label
print("Estrazione delle feature...")
X = np.stack([extract_features(q) for q in df["question"]])
y = df["label"].to_numpy(dtype=str)  # Conversione sicura per stratify

# Train/test split stratificato
# forse è meglio k cross validation ?
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.4, random_state=42, stratify=y
)
print(f"Train set: {len(X_train)}, Test set: {len(X_test)}")

# Train model
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, y_train)

# Evaluation
y_pred = clf.predict(X_test)
print("\n--- Risultati ---")
print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
print(classification_report(y_test, y_pred, digits=3))

# Save model
joblib.dump(clf, "ml_model.joblib")
print("Modello ML salvato su ml_model.joblib")