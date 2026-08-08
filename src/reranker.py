from typing import List
from sentence_transformers import CrossEncoder
from src.document import Document
from src.interfaces import Reranker
from src.config import RERANK_MODEL_NAME

class LocalCrossEncoderReranker(Reranker):
    """
    Local Cross-Encoder Reranker.
    - Uses sentence-transformers CrossEncoder.
    - Evaluates query-document pairs to compute direct similarity.
    - Re-ranks candidate documents, selecting the top N.
    """
    
    def __init__(self, model_name: str = RERANK_MODEL_NAME):
        # This will download the cross-encoder model on first run
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: List[Document], top_n: int = 3) -> List[Document]:
        if not documents:
            return []

        # 1. Build pairs: [(query, document_text), ...]
        pairs = [[query, doc.page_content] for doc in documents]
        
        # 2. Predict relevance scores (higher means more relevant)
        scores = self.model.predict(pairs, show_progress_bar=False)
        
        # 3. Associate scores with documents
        scored_docs = list(zip(documents, scores))
        
        # 4. Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N documents
        return [doc for doc, score in scored_docs[:top_n]]
