import os
from typing import List, Dict, Any
from groq import Groq
from src.document import Document
from src.interfaces import LLMGenerator
from src.config import GROQ_API_KEY, GROQ_LLM_MODEL

class GroqLLMGenerator(LLMGenerator):
    """
    Groq API Client Wrapper.
    - Implements strict RAG grounding via clear instruction prompts.
    - Supports Llama 3.3 70B models.
    - Guides the model to output document references [Doc X] for precise citation.
    """
    
    def __init__(self, api_key: str = GROQ_API_KEY, model_name: str = GROQ_LLM_MODEL):
        if not api_key:
            raise ValueError("Groq API Key (GROQ_API_KEY) must be provided or configured in the environment.")
        self.client = Groq(api_key=api_key)
        self.model_name = model_name

    def generate(self, query: str, context: List[Document]) -> Dict[str, Any]:
        if not context:
            return {
                "answer": "No tengo información suficiente para responder a tu pregunta.",
                "citations": []
            }

        # 1. Format the context for the LLM
        formatted_context = []
        for idx, doc in enumerate(context, start=1):
            source_url = doc.metadata.get("source_url", "N/A")
            section = doc.metadata.get("section", "N/A")
            formatted_context.append(
                f"[Doc {idx}]\n"
                f"Proveedor: {doc.metadata.get('api_provider', 'N/A')}\n"
                f"Sección: {section}\n"
                f"URL de origen: {source_url}\n"
                f"Contenido:\n{doc.page_content}\n"
                "----------------------------------------"
            )
        
        context_str = "\n".join(formatted_context)

        # 2. Build system and user prompts
        system_prompt = (
            "Eres un asistente experto técnico en APIs de pago (Wompi, Stripe, MercadoPago, etc.).\n"
            "Tu tarea es responder a la pregunta del usuario utilizando ÚNICAMENTE la información provista en el Contexto a continuación.\n\n"
            "Reglas no negociables:\n"
            "1. Responde de forma clara, técnica y concisa.\n"
            "2. Apóyate de forma estricta en el contexto. No asumas, no inventes ni uses conocimiento externo.\n"
            "3. Si en el contexto no se encuentra la respuesta exacta a la pregunta o no hay suficiente información, responde estrictamente: "
            "\"No tengo información suficiente para responder a tu pregunta.\"\n"
            "4. Cuando uses información de un documento del contexto, debes citarlo al final de la oración o fragmento correspondiente "
            "usando el formato '[Doc X]', donde X es el número del documento correspondente (ej. [Doc 1], [Doc 2]). "
            "Nunca inventes IDs de documentos que no estén en el contexto.\n"
            "5. Responde en el mismo idioma en el que se realiza la pregunta (usualmente español)."
        )

        user_prompt = (
            f"Contexto:\n{context_str}\n\n"
            f"Pregunta: {query}\n\n"
            "Respuesta:"
        )

        # 3. Call Groq API
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model_name,
                temperature=0.0,  # Minimize creativity to enforce grounding
                max_tokens=1024,
            )
            
            answer = chat_completion.choices[0].message.content.strip()
            
            # 4. Resolve citations based on the references in the generated text
            citations = []
            for idx, doc in enumerate(context, start=1):
                reference_tag = f"[Doc {idx}]"
                if reference_tag in answer:
                    citations.append({
                        "id": reference_tag,
                        "api_provider": doc.metadata.get("api_provider"),
                        "section": doc.metadata.get("section"),
                        "source_url": doc.metadata.get("source_url")
                    })
                    
            return {
                "answer": answer,
                "citations": citations
            }
            
        except Exception as e:
            return {
                "answer": f"Error al generar la respuesta con el LLM: {str(e)}",
                "citations": []
            }
