import pytest
from src.document import Document
from src.chunker import SemanticCodeChunker

def test_chunker_prefix_prepending():
    chunker = SemanticCodeChunker(target_size=100, overlap_size=10)
    
    doc = Document(
        page_content="Esto es un texto de prueba para validar que el chunker prefije los headers.",
        metadata={"header_path": "Wompi > Firmas"}
    )
    
    chunks = chunker.chunk([doc])
    assert len(chunks) > 0
    # Every chunk must start with the Contexto prefix
    assert chunks[0].page_content.startswith("Contexto: Wompi > Firmas")

def test_chunker_keeps_code_blocks_intact():
    chunker = SemanticCodeChunker(target_size=50, overlap_size=5)
    
    content = """Parrafo corto.
```python
def mi_funcion():
    x = 10
    y = 20
    return x + y
```
Otro parrafo corto.
"""
    doc = Document(
        page_content=content,
        metadata={"header_path": "Wompi > Tests"}
    )
    
    chunks = chunker.chunk([doc])
    assert len(chunks) > 0
    
    # Verify that the code block is present in its entirety in one of the chunks
    code_block_found = False
    for chunk in chunks:
        if "def mi_funcion():" in chunk.page_content:
            code_block_found = True
            assert "```python" in chunk.page_content
            assert "return x + y" in chunk.page_content
            assert "```" in chunk.page_content
            
    assert code_block_found
