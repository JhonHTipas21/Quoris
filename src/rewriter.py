from typing import Optional
from groq import Groq
from src.logger import get_logger
from src.config import GROQ_API_KEY, GROQ_LLM_MODEL

class GroqQueryRewriter:
    """
    LLM-based Query Rewriter using Groq.
    Transforms raw user queries into search-optimized technical queries
    to improve both vector and lexical retrieval.
    """
    
    def __init__(self, api_key: str = GROQ_API_KEY, model_name: str = GROQ_LLM_MODEL):
        self.logger = get_logger(__name__)
        if not api_key:
            self.logger.warning("GROQ_API_KEY is not configured. Query rewriter is disabled.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
        self.model_name = model_name

    def rewrite(self, query: str) -> str:
        if not self.client:
            return query

        self.logger.info(f"Rewriting user query: '{query}'")
        
        system_prompt = (
            "Eres un asistente de busqueda tecnica especializado en RAG sobre APIs de pago.\n"
            "Tu tarea es reescribir la pregunta vaga o informal del usuario en una query de busqueda tecnica optimizada para recuperar informacion en una base de datos vectorial y BM25.\n"
            "Reglas:\n"
            "1. Agrega terminos tecnicos, codigos de error, nombres de metodos de pago o parametros comunes si son relevantes.\n"
            "2. Retorna UNICAMENTE la query reescrita, sin introducciones, explicaciones, ni comillas."
        )
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Reescribe esta query: {query}"}
                ],
                model=self.model_name,
                temperature=0.0,
                max_tokens=64
            )
            rewritten = chat_completion.choices[0].message.content.strip()
            self.logger.info(f"Query successfully rewritten to: '{rewritten}'")
            return rewritten
            
        except Exception as e:
            self.logger.error(f"Error during query rewriting: {e}. Falling back to original query.")
            return query
