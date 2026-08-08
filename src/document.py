import hashlib
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class Document(BaseModel):
    page_content: str = Field(..., description="The main text content of the document or chunk.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary (source_url, api_provider, section, etc.)")
    content_hash: Optional[str] = Field(None, description="MD5 hash of the page_content, used for incremental updates.")

    def model_post_init(self, __context: Any) -> None:
        # Calculate content hash if not already provided
        if not self.content_hash and self.page_content:
            self.content_hash = hashlib.md5(self.page_content.encode("utf-8")).hexdigest()

    def update_hash(self) -> None:
        self.content_hash = hashlib.md5(self.page_content.encode("utf-8")).hexdigest()
