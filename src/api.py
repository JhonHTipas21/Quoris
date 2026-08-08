import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from src.config import GROQ_API_KEY, DOCS_DIR
from src.parser import MarkdownParser
from src.chunker import SemanticCodeChunker
from src.embedder import LocalEmbedder
from src.vector_store import ChromaVectorStore
from src.retriever import LocalBM25Retriever, HybridRetriever
from src.reranker import LocalCrossEncoderReranker
from src.llm import GroqLLMGenerator
from src.orchestrator import RAGOrchestrator

app = FastAPI(
    title="Quoris RAG API",
    description="Asistente RAG de producción sobre documentación de APIs de pago",
    version="1.0.0"
)

# Global instances of RAG components
orchestrator: Optional[RAGOrchestrator] = None
bm25_retriever: Optional[LocalBM25Retriever] = None
vector_store: Optional[ChromaVectorStore] = None

class QueryRequest(BaseModel):
    query: str = Field(..., examples=["¿Cómo calculo la firma de integridad de Wompi?"])

class CitationSchema(BaseModel):
    id: str
    api_provider: str
    section: str
    source_url: str

class QueryResponse(BaseModel):
    query: str
    search_query: str
    answer: str
    citations: List[CitationSchema]
    latency_seconds: float

def initialize_rag_system():
    global orchestrator, bm25_retriever, vector_store
    
    print("Initializing RAG pipeline components...")
    
    # 1. Initialize core layers
    parser = MarkdownParser()
    chunker = SemanticCodeChunker()
    embedder = LocalEmbedder()
    vector_store = ChromaVectorStore(embedder=embedder)
    bm25_retriever = LocalBM25Retriever()
    
    # 2. Ingest documents to build BM25 lexical corpus and populate vector store
    md_files = list(DOCS_DIR.glob("**/*.md"))
    all_chunks = []
    
    for file_path in md_files:
        try:
            parsed_docs = parser.load(str(file_path))
            chunks = chunker.chunk(parsed_docs)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error loading {file_path} on startup: {e}")
            
    # Index in Vector Store (checks hashes internally)
    if all_chunks:
        vector_store.add_documents(all_chunks)
        
    # Index in BM25 (always fully populated in memory)
    bm25_retriever.index_documents(all_chunks)
    
    # 3. Setup retrievers & generators
    hybrid_retriever = HybridRetriever(
        vector_store=vector_store,
        embedder=embedder,
        bm25_retriever=bm25_retriever
    )
    
    reranker = LocalCrossEncoderReranker()
    llm = GroqLLMGenerator(api_key=GROQ_API_KEY)
    
    # 4. Instantiate orchestrator
    orchestrator = RAGOrchestrator(
        hybrid_retriever=hybrid_retriever,
        reranker=reranker,
        llm=llm
    )
    print("RAG pipeline successfully initialized!")

@app.on_event("startup")
def startup_event():
    # Make sure GROQ_API_KEY is present
    if not GROQ_API_KEY:
        print("[WARNING] GROQ_API_KEY is missing! Queries will fail.")
    initialize_rag_system()

@app.post("/api/v1/query", response_model=QueryResponse)
def execute_query(request: QueryRequest):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="RAG system is still initializing or unavailable.")
    
    try:
        response = orchestrator.query(request.query)
        return QueryResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/api/v1/ingest")
def trigger_ingestion(background_tasks: BackgroundTasks):
    """
    Triggers document scanning and updates vector index and BM25 index in background.
    """
    background_tasks.add_task(initialize_rag_system)
    return {"status": "Ingest process triggered in the background"}

@app.get("/api/v1/status")
def get_status():
    global vector_store, bm25_retriever
    return {
        "status": "online" if orchestrator else "initializing",
        "has_groq_key": bool(GROQ_API_KEY),
        "indexed_chunks_count": len(bm25_retriever.documents) if bm25_retriever else 0,
        "chroma_collection_name": vector_store.collection.name if vector_store else None
    }
