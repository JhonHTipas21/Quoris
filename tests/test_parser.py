import pytest
from pathlib import Path
from src.parser import MarkdownParser

@pytest.fixture
def sample_markdown_file(tmp_path):
    directory = tmp_path / "stripe"
    directory.mkdir()
    file_path = directory / "02_tokens.md"
    
    content = """# Stripe API — Tokenizacion
    
Este es un parrafo introductorio.

## 1. Tokenizacion de Tarjetas
POST `/v1/tokens`

### Respuesta del Servidor
```json
{
  "id": "tok_123"
}
```

## 2. API de Metodos de Pago
POST `/v1/payment_methods`
"""
    file_path.write_text(content)
    return str(file_path)

def test_markdown_parser_headers_splitting(sample_markdown_file):
    parser = MarkdownParser()
    documents = parser.load(sample_markdown_file)
    
    # Check total documents generated (one per section)
    # Sections are:
    # 1. H1 intro (General)
    # 2. H2 section (1. Tokenizacion de Tarjetas)
    # 3. H3 section (Respuesta del Servidor)
    # 4. H2 section (2. API de Metodos de Pago)
    assert len(documents) == 4
    
    # Validate provider extraction
    for doc in documents:
        assert doc.metadata["api_provider"] == "stripe"
        assert doc.metadata["source_file"] == "02_tokens.md"
        assert doc.metadata["source_url"] == "https://docs.stripe.com/tokens"

def test_markdown_parser_code_block_awareness(tmp_path):
    directory = tmp_path / "mercadopago"
    directory.mkdir()
    file_path = directory / "01_intro.md"
    
    content = """# Mercado Pago Intro
    
```python
# Este numeral es un comentario en Python, no debe interpretarse como header H1.
# Otro comentario.
```
"""
    file_path.write_text(content)
    
    parser = MarkdownParser()
    documents = parser.load(str(file_path))
    
    # Should only produce 1 document under H1
    assert len(documents) == 1
    assert "comentario en Python" in documents[0].page_content
    # Confirm it does not think there are subheaders
    assert documents[0].metadata["header_path"] == "Mercado Pago Intro"
