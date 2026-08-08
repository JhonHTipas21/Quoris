import os
from typing import List, Dict, Any
from pathlib import Path
from src.document import Document
from src.interfaces import DocumentLoader
from src.logger import get_logger

class MarkdownParser(DocumentLoader):
    """
    Parses Markdown files into structured Document objects.
    Maintains header hierarchy, code blocks intact, and populates metadata.
    """
    
    def __init__(self, base_urls: Dict[str, str] = None):
        self.logger = get_logger(__name__)
        # Map provider folders to their base URLs for source citing
        self.base_urls = base_urls or {
            "wompi": "https://docs.wompi.co",
            "stripe": "https://docs.stripe.com",
            "mercadopago": "https://www.mercadopago.com.co/developers"
        }

    def load(self, file_path: str) -> List[Document]:
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"Failed to load file, path does not exist: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        self.logger.info(f"Starting markdown parsing for file: {file_path}")

        # Determine metadata from file path
        api_provider = path.parent.name.lower()
        source_file = path.name
        
        # Determine source url
        base_url = self.base_urls.get(api_provider, "https://docs.example.com")
        # Generate slug from filename, e.g. "01_intro.md" -> "intro" or "02_acceptance.md" -> "acceptance"
        slug = source_file.split("_", 1)[-1].replace(".md", "") if "_" in source_file else source_file.replace(".md", "")
        source_url = f"{base_url}/{slug}"

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        documents: List[Document] = []
        current_h1 = ""
        current_h2 = ""
        current_h3 = ""
        
        section_lines: List[str] = []
        in_code_block = False

        def flush_section():
            nonlocal section_lines
            content = "".join(section_lines).strip()
            if content:
                # Determine active section title
                active_section = current_h3 or current_h2 or current_h1 or "General"
                header_path = " > ".join([h for h in [current_h1, current_h2, current_h3] if h])
                
                # Create metadata
                metadata = {
                    "api_provider": api_provider,
                    "source_file": source_file,
                    "source_url": source_url,
                    "section": active_section,
                    "header_path": header_path,
                }
                
                documents.append(Document(page_content=content, metadata=metadata))
            section_lines = []

        for line in lines:
            stripped = line.strip()
            
            # Track if we are inside a code block
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                section_lines.append(line)
                continue

            # If inside code block, do not parse headers
            if in_code_block:
                section_lines.append(line)
                continue

            # Parse headers
            if stripped.startswith("# "):
                flush_section()
                current_h1 = stripped[2:].strip()
                current_h2 = ""
                current_h3 = ""
                section_lines.append(line)
            elif stripped.startswith("## "):
                flush_section()
                current_h2 = stripped[3:].strip()
                current_h3 = ""
                # Prefix the header path to the section lines for context
                section_lines.append(f"# {current_h1}\n" if current_h1 else "")
                section_lines.append(line)
            elif stripped.startswith("### "):
                flush_section()
                current_h3 = stripped[4:].strip()
                # Prefix the parent headers for context
                section_lines.append(f"# {current_h1}\n" if current_h1 else "")
                section_lines.append(f"## {current_h2}\n" if current_h2 else "")
                section_lines.append(line)
            else:
                section_lines.append(line)

        # Flush final section
        flush_section()

        return documents
