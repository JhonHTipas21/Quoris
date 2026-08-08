import re
from typing import List
from src.document import Document
from src.interfaces import Chunker
from src.logger import get_logger

class SemanticCodeChunker(Chunker):
    """
    Splits documents into chunks of 500-800 characters.
    - Code-block aware: Never splits code blocks (``` ... ```) across chunks.
    - Context prefixing: Prepends the section header path to every chunk.
    - Respects a configurable chunk size and overlap.
    """
    
    def __init__(self, target_size: int = 600, overlap_size: int = 100):
        self.logger = get_logger(__name__)
        self.target_size = target_size
        self.overlap_size = overlap_size

    def _split_into_blocks(self, text: str) -> List[str]:
        """Split text into blocks (paragraphs or full code blocks)."""
        lines = text.split("\n")
        blocks: List[str] = []
        current_block: List[str] = []
        in_code_block = False

        for line in lines:
            if line.strip().startswith("```"):
                if in_code_block:
                    # Closing code block
                    current_block.append(line)
                    in_code_block = False
                    blocks.append("\n".join(current_block))
                    current_block = []
                else:
                    # Opening code block: flush current text block first
                    if current_block:
                        blocks.append("\n".join(current_block))
                        current_block = []
                    current_block.append(line)
                    in_code_block = True
            else:
                current_block.append(line)
                # If not in code block and we hit a paragraph separator, flush
                if not in_code_block and not line.strip() and len(current_block) > 1:
                    blocks.append("\n".join(current_block))
                    current_block = []

        if current_block:
            blocks.append("\n".join(current_block))

        return [b.strip() for b in blocks if b.strip()]

    def chunk(self, documents: List[Document]) -> List[Document]:
        self.logger.info(f"Starting chunking process for {len(documents)} documents")
        chunks: List[Document] = []

        for doc in documents:
            header_path = doc.metadata.get("header_path", "")
            prefix = f"Contexto: {header_path}\n\n" if header_path else ""
            
            blocks = self._split_into_blocks(doc.page_content)
            
            current_chunk_blocks: List[str] = []
            current_length = len(prefix)
            
            chunk_index = 0
            
            for block in blocks:
                block_len = len(block)
                
                # Check if adding this block exceeds target size and we already have content
                if current_chunk_blocks and (current_length + block_len > self.target_size + 150):
                    # Flush current chunk
                    chunk_text = prefix + "\n\n".join(current_chunk_blocks)
                    
                    chunk_metadata = doc.metadata.copy()
                    chunk_metadata["chunk_index"] = chunk_index
                    
                    chunks.append(Document(page_content=chunk_text, metadata=chunk_metadata))
                    chunk_index += 1
                    
                    # Implement overlap by carrying over the last block if it is not a code block and fits
                    last_block = current_chunk_blocks[-1] if current_chunk_blocks else ""
                    if last_block and not last_block.startswith("```") and len(last_block) < self.overlap_size:
                        current_chunk_blocks = [last_block, block]
                        current_length = len(prefix) + len(last_block) + len(block) + 2 # +2 for join \n\n
                    else:
                        current_chunk_blocks = [block]
                        current_length = len(prefix) + block_len
                else:
                    current_chunk_blocks.append(block)
                    current_length += (block_len + 2) if len(current_chunk_blocks) > 1 else block_len

            # Flush any remaining blocks
            if current_chunk_blocks:
                chunk_text = prefix + "\n\n".join(current_chunk_blocks)
                chunk_metadata = doc.metadata.copy()
                chunk_metadata["chunk_index"] = chunk_index
                chunks.append(Document(page_content=chunk_text, metadata=chunk_metadata))

        self.logger.info(f"Successfully generated {len(chunks)} chunks")
        return chunks
