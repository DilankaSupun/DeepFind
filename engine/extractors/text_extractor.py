"""
DeepFind Engine — Plain Text & Code Extractor

Handles all plain text and code file types using built-in Python file I/O.

Supported:
  Text:  .txt .md .csv .json .xml
  Code:  .py .js .jsx .ts .tsx .php .java .html .css .sql
         .c .cpp .cs .go .rs
"""

import logging
from pathlib import Path

from extractors.base_extractor import BaseExtractor, ExtractorError

log = logging.getLogger(__name__)

# Encodings to attempt in order
_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1", "cp1252")


class TextExtractor(BaseExtractor):
    """
    Reads plain text and source code files.
    Tries multiple encodings before giving up.
    """

    def _extract_raw(self, path: Path) -> str:
        last_err = None
        for enc in _ENCODINGS:
            try:
                return path.read_text(encoding=enc, errors="strict")
            except UnicodeDecodeError as e:
                last_err = e
                continue
            except Exception as e:
                raise ExtractorError(str(e)) from e

        # All encodings failed — try with replacement chars as last resort
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise ExtractorError(
                f"Cannot read file with any encoding: {last_err}"
            ) from exc
