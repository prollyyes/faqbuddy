import time
from sklearn.metrics import classification_report, precision_score, recall_score, f1_score
from src.switcher.ml_utils import extract_features
from src.utils.utils_llm import classify_question

# Carica il modello ML già addestrato
import os
import joblib
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'ml_model.joblib'))
clf = joblib.load(model_path)

# Domande di test aggiuntive (mai viste dal modello)
test_questions = [
    "Quanti crediti servono per iscriversi al secondo anno?",
    "Come posso recuperare un esame se sono fuori corso?",
    "Qual è la scadenza per il pagamento delle tasse universitarie?",
    "Quali documenti servono per la domanda di laurea?",
    "Come posso migliorare la mia media degli esami?",
    "Quando si svolgono le sessioni straordinarie?",
    "Quali sono i requisiti per accedere alla magistrale?",
    "Come posso evitare sovrapposizioni tra esami obbligatori?",
    "Dove posso trovare il regolamento del corso di laurea?",
    "Quali sono le procedure per il riconoscimento di esami esteri?",
    "Come posso pianificare gli esami per laurearmi in tempo?",
    "Quanti appelli sono previsti per ogni esame?",
    "Quali sono i vantaggi di scegliere un curriculum internazionale?",
    "Come posso conciliare lavoro e studio?",
    "Qual è la durata della sessione estiva?",
]

print("\n--- Benchmark: ML model vs gemma3:4b ---")
correct = 0
ml_confidences = []
ml_true = []
gemma_true = []

# Benchmark ML model
start_ml = time.time()
ml_preds = []
for q in test_questions:
    features = [extract_features(q)]
    ml_pred = clf.predict(features)[0]
    proba = max(clf.predict_proba(features)[0])
    ml_preds.append(ml_pred)
    ml_confidences.append(proba)
elapsed_ml = time.time() - start_ml

# Benchmark gemma3:4b
start_gemma = time.time()
gemma_preds = []
for q in test_questions:
    gemma_pred = classify_question(q)
    gemma_preds.append(gemma_pred)
elapsed_gemma = time.time() - start_gemma

# Confronto e accuracy
for i, q in enumerate(test_questions):
    print(f"Question: {q}\nML model: {ml_preds[i]} (conf: {ml_confidences[i]:.2f})\tgemma3:4b: {gemma_preds[i]}\n")
    if ml_preds[i].strip().lower() == gemma_preds[i].strip().lower():
        correct += 1

# Calcola metriche rispetto a gemma3:4b come "ground truth"
ml_true = [m.lower() for m in ml_preds]
gemma_true = [g.lower() for g in gemma_preds]

print(f"Accuracy of ML model vs gemma3:4b: {correct / len(test_questions) * 100:.2f}%")
print(f"ML model total time: {elapsed_ml:.4f} seconds")
print(f"gemma3:4b total time: {elapsed_gemma:.4f} seconds")
print(f"Media confidenza ML: {sum(ml_confidences)/len(ml_confidences):.2f}")

# Precision, recall, f1 rispetto a gemma3:4b
print("\nClassification report (ML vs gemma3:4b):")
print(classification_report(gemma_true, ml_true, digits=3))