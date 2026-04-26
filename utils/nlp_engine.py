import logging
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPEngine:
    def __init__(self):
        self.model = None
        self.has_nlp = False
        self._initialize_model()

    def _initialize_model(self):
        """Attempts to load the sentence-transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.has_nlp = True
            logger.info("NLP Engine initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer: {e}. Falling back to keyword matching.")
            self.has_nlp = False

    def get_similarity(self, text1: str, text2: str) -> float:
        """
        Computes similarity between two texts.
        Uses cosine similarity if model is loaded, otherwise falls back to keyword overlap.
        """
        if self.has_nlp and self.model:
            try:
                embeddings = self.model.encode([text1, text2])
                # Cosine similarity
                sim = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
                return float(sim)
            except Exception as e:
                logger.error(f"Error computing semantic similarity: {e}")
                return self._keyword_fallback(text1, text2)
        else:
            return self._keyword_fallback(text1, text2)

    def _keyword_fallback(self, text1: str, text2: str) -> float:
        """Basic Jaccard-like similarity based on keyword overlap."""
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        if not set1 or not set2:
            return 0.0
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

# Singleton instance
nlp_engine = NLPEngine()
