from typing import List
from sentence_transformers import SentenceTransformer
from src.interfaces import Embedder
from src.config import EMBEDDING_MODEL_NAME

class LocalEmbedder(Embedder):
    """
    Computes text embeddings locally using sentence-transformers.
    Defaults to the lightweight and efficient all-MiniLM-L6-v2 model.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        # This will download the model to ~/.cache/huggingface/hub on the first run
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=False)
        # Convert numpy array to list of lists of floats
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(text, show_progress_bar=False)
        # Convert numpy array to list of floats
        return embedding.tolist()
