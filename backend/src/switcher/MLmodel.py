import os
import joblib
from .ml_utils import extract_features

class MLModel:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'ml_model.joblib'))
        self.model = joblib.load(model_path)

    def inference(self, question):
        features = [extract_features(question)]
        pred = self.model.predict(features)[0]
        proba = max(self.model.predict_proba(features)[0])
        return pred, proba