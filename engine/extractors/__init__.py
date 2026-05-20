# engine/extractors/
# Step 9: Text extraction — dispatches to PDF, DOCX, or plain-text extractor.

from extractors.extractor_dispatcher import extract_file, chunk_text, get_extractor
from extractors.base_extractor import ExtractorError

__all__ = ["extract_file", "chunk_text", "get_extractor", "ExtractorError"]
