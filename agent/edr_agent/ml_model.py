"""Optional local model; only load trusted, locally trained joblib files."""
from pathlib import Path
import logging
from .features import vector
class Model:
    def __init__(self, path: str):
        self.model = None
        if Path(path).is_file():
            try:
                import joblib
                self.model=joblib.load(path)
            except Exception:
                logging.warning('Model unavailable; rule-based detection remains active')
    def probability(self, values: dict) -> float | None:
        if self.model is None: return None
        try:
            index=list(self.model.classes_).index(1)
            return float(self.model.predict_proba([vector(values)])[0][index])
        except (ValueError,AttributeError): return None
