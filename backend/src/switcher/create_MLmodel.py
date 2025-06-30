import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from .ml_utils import extract_features
import numpy as np
import os

csv_path = os.path.join(os.path.dirname(__file__), "dataset_domande.csv")

df = pd.read_csv(csv_path, on_bad_lines='skip')  # on_bad_lines='skip' se vuoi saltare le righe malformate
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

# Save model inside the models directory
import joblib
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'ml_model.joblib'))
joblib.dump(clf, model_path)
print(f"Modello salvato in: {model_path}")