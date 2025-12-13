import os

class AdvisorFilter:
    def __init__(self, terms_file="advisor_terms.txt"):
        self.terms_file = os.path.join(os.path.dirname(__file__), terms_file)
        self.harmful_terms = self._load_terms()

    def _load_terms(self):
        if not os.path.exists(self.terms_file):
            return []
        with open(self.terms_file, 'r') as f:
            return [line.strip().lower() for line in f if line.strip()]

    def scan_for_harmful_phrases(self, text: str) -> bool:
        """
        Scans the given text for any harmful phrases defined in advisor_terms.txt.
        Returns True if harmful phrases are found, False otherwise.
        """
        text_lower = text.lower()
        for term in self.harmful_terms:
            if term in text_lower:
                return True
        return False
