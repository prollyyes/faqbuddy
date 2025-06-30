import pytest
from sklearn.metrics import classification_report
from ..src.switcher.MLmodel import MLModel
from ..src.utils.llm_gemma import classify_question

ml_model = MLModel()

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

@pytest.mark.parametrize("question", test_questions)
def test_ml_vs_gemma(question):
    ml_pred, ml_conf = ml_model.inference(question)
    gemma_pred = classify_question(question)
    print(f"Question: {question}\nML model: {ml_pred} (conf: {ml_conf:.2f})\tgemma3:4b: {gemma_pred}\n")
    # Esempio di asserzione: i due modelli devono almeno produrre una stringa non vuota
    assert isinstance(ml_pred, str) and ml_pred.strip()
    assert isinstance(gemma_pred, str) and gemma_pred.strip()
    
    # Confronta le predizioni dei due modelli
    assert ml_pred.strip().lower() == gemma_pred.strip().lower()