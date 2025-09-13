##########################################
# INUTILIZZATO PER IL MOMENTO #
##########################################

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
from .ml_utils import extract_features
from ..utils.llm_gemma import classify_question


app = FastAPI()

# Abilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'ml_model.joblib'))
clf = joblib.load(model_path)

class ChatRequest(BaseModel):
    question: str

@app.post("/classify")
def classify(req: ChatRequest):
    features = [extract_features(req.question)]
    ml_pred = clf.predict(features)[0]
    # Calcola la probabilità della predizione ML
    proba = max(clf.predict_proba(features)[0])
    threshold = 0.7  # Soglia di confidenza: sotto questo valore si usa il fallback LLM

    if proba < threshold:
        # Fallback: usa gemma3:4b per la classificazione
        gemma_pred = classify_question(req.question)
        chosen = gemma_pred
        fallback_used = True
    else:
        gemma_pred = None
        chosen = ml_pred
        fallback_used = False

    return {
        "ml_model": ml_pred,
        "ml_confidence": proba,
        "gemma3_4b": gemma_pred,
        "chosen": chosen,
        "fallback_used": fallback_used
    }