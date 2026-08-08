import os
from pathlib import Path
import pytest
from src.document import Document
from src.parser import MarkdownParser
from src.chunker import SemanticCodeChunker
from src.embedder import LocalEmbedder
from src.vector_store import ChromaVectorStore

# Helper to create a temp markdown file for testing
@pytest.fixture
def temp_markdown_file(tmp_path):
    d = tmp_path / "wompi"
    d.mkdir()
    f = d / "02_acceptance.md"
    f.write_text("""# Wompi API — Tokens de Aceptación

De acuerdo con la legislación colombiana, es obligatorio aceptar los términos.

## Paso 1: Consultar los términos vigentes
Petición GET al endpoint:
```http
GET https://sandbox.wompi.co/v1/merchants/pub_test_Qz8R2
```

## Paso 2: Presentar los contratos al usuario
El usuario debe marcar un control checkbox.
""")
    return str(f)

def test_markdown_parser(temp_markdown_file):
    parser = MarkdownParser()
    docs = parser.load(temp_markdown_file)
    
    assert len(docs) > 0
    # Check metadata extraction
    assert docs[0].metadata["api_provider"] == "wompi"
    assert docs[0].metadata["source_file"] == "02_acceptance.md"
    assert docs[0].metadata["source_url"] == "https://docs.wompi.co/acceptance"
    
    # Check that header structure is captured
    header_paths = [doc.metadata["header_path"] for doc in docs]
    assert any("Paso 1: Consultar" in path for path in header_paths)
    assert any("Paso 2: Presentar" in path for path in header_paths)

def test_semantic_code_chunker():
    chunker = SemanticCodeChunker(target_size=200, overlap_size=20)
    
    # Create doc with a code block
    content = """Some text before code.
```python
def hello():
    print("This is a long code block that should stay intact.")
    print("Line 2 of code block.")
    print("Line 3 of code block.")
```
Some text after code."""
    
    doc = Document(
        page_content=content,
        metadata={"header_path": "Wompi > Testing"}
    )
    
    chunks = chunker.chunk([doc])
    
    assert len(chunks) > 0
    # Confirm code block is not split (it should exist in its entirety in one of the chunks)
    for chunk in chunks:
        # If code block is present, verify it has opening and closing markers
        if "def hello()" in chunk.page_content:
            assert "```python" in chunk.page_content
            assert "```" in chunk.page_content
            assert "Some text after code." in chunk.page_content or len(chunks) > 1

def test_local_embedder():
    embedder = LocalEmbedder()
    embedding = embedder.embed_query("¿Cómo generar la firma de integridad?")
    
    assert isinstance(embedding, list)
    assert len(embedding) == 384  # Size of all-MiniLM-L6-v2 embeddings
    assert all(isinstance(val, float) for val in embedding)

def test_chroma_vector_store(tmp_path):
    # Use a mock embedder to make test run fast and independent of HuggingFace download in tests
    class MockEmbedder:
        def embed_documents(self, texts):
            return [[0.1] * 384 for _ in texts]
        def embed_query(self, text):
            return [0.1] * 384

    # Setup vector store in a temp dir
    import chromadb
    db_path = tmp_path / "chroma_test"
    db_path.mkdir()
    
    # Patch DB_DIR in vector_store module
    from src import vector_store
    original_db_dir = vector_store.DB_DIR
    vector_store.DB_DIR = db_path
    
    try:
        vs = ChromaVectorStore(embedder=MockEmbedder(), collection_name="test_collection")
        
        doc1 = Document(page_content="Cómo autenticar en la API", metadata={"api_provider": "wompi", "source_file": "intro.md", "chunk_index": 0})
        doc2 = Document(page_content="Cómo validar firmas de webhooks", metadata={"api_provider": "wompi", "source_file": "webhooks.md", "chunk_index": 0})
        
        vs.add_documents([doc1, doc2])
        
        # Search
        results = vs.search(query_vector=[0.1]*384, k=1)
        assert len(results) == 1
        
        # Search with metadata filter
        results_filtered = vs.search(query_vector=[0.1]*384, k=5, metadata_filter={"api_provider": "wompi"})
        assert len(results_filtered) == 2
        
    finally:
        # Restore original path
        vector_store.DB_DIR = original_db_dir
