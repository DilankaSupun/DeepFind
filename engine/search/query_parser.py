"""
DeepFind Engine — Natural Query Parser (Step 11.5)

Parses natural language search queries into meaningful structured parts.
Uses lightweight dictionaries and regex, avoiding heavy AI/NLP models.
"""

import re
from typing import Dict, List, Any

# Words that should be ignored if they are used as instructions
INSTRUCTION_WORDS = {
    "find", "search", "show", "me", "file", "files", "contain", "contains",
    "containing", "consist", "consists", "with", "using", "use", "uses",
    "has", "have", "about", "related", "that", "the", "a", "an", "of",
    "in", "from", "for", "to", "and", "or"
}

WEAK_TAGS = {
    "document", "file", "text", "data", "common"
}

# Maps file type keywords to extensions and associated tag categories
FILE_TYPE_MAP = {
    "pdf":        {"exts": [".pdf"], "tags": ["pdf", "document"]},
    "docx":       {"exts": [".docx"], "tags": ["docx", "document"]},
    "word":       {"exts": [".docx"], "tags": ["docx", "document"]},
    "txt":        {"exts": [".txt"], "tags": ["text", "document"]},
    "text":       {"exts": [".txt"], "tags": ["text", "document"]},
    "python":     {"exts": [".py"], "tags": ["python", "code"]},
    "php":        {"exts": [".php"], "tags": ["php", "code"]},
    "javascript": {"exts": [".js"], "tags": ["javascript", "code"]},
    "js":         {"exts": [".js"], "tags": ["javascript", "code"]},
    "typescript": {"exts": [".ts"], "tags": ["typescript", "code"]},
    "ts":         {"exts": [".ts"], "tags": ["typescript", "code"]},
    "sql":        {"exts": [".sql"], "tags": ["sql", "database", "code"]},
    "html":       {"exts": [".html"], "tags": ["html", "web", "code"]},
    "css":        {"exts": [".css"], "tags": ["css", "web", "code"]},
    "image":      {"exts": [".jpg", ".jpeg", ".png", ".webp"], "tags": ["image"]},
    "video":      {"exts": [".mp4", ".mov", ".avi", ".mkv"], "tags": ["video"]},
    "audio":      {"exts": [".mp3", ".wav", ".m4a"], "tags": ["audio"]},
}

# General tags/categories to detect
CATEGORY_TAGS = {
    "code", "document", "design", "university", "project", "finance",
    "payment", "invoice", "receipt", "cv", "resume", "career", "database",
    "frontend", "backend", "api", "figma", "logo", "assignment", "tutorial",
    "practical", "lecture", "exam"
}

def parse_query(original_query: str) -> Dict[str, Any]:
    """
    Parses a natural query into structured match criteria.
    """
    q = original_query.lower().strip()

    # Normalize UI/UX, ui-ux, ui_ux to "ui ux"
    q = re.sub(r'ui[/-_]ux', 'ui ux', q)

    # Convert .pdf to pdf to handle extensions properly during parsing
    q = re.sub(r'\.(\w+)', r'\1', q)

    raw_tokens = q.split()
    drive_filters = set()
    folder_filters = set()
    location_words_used = set()
    
    i = 0
    while i < len(raw_tokens):
        w = raw_tokens[i]
        clean_w = re.sub(r'[^\w:]', '', w)
        
        if clean_w in ("in", "inside", "from", "under"):
            loc_tokens = []
            j = i + 1
            is_drive = False
            is_folder = False
            
            if j < len(raw_tokens):
                cw = re.sub(r'[^\w]', '', raw_tokens[j])
                if cw == "drive":
                    is_drive = True
                    location_words_used.add(raw_tokens[j])
                    j += 1
                elif cw == "folder":
                    is_folder = True
                    location_words_used.add(raw_tokens[j])
                    j += 1
            
            while j < len(raw_tokens):
                cw = re.sub(r'[^\w:]', '', raw_tokens[j])
                if cw in ("folder", "drive"):
                    location_words_used.add(raw_tokens[j])
                    if cw == "drive": is_drive = True
                    if cw == "folder": is_folder = True
                    j += 1
                    break
                
                loc_tokens.append(raw_tokens[j])
                location_words_used.add(raw_tokens[j])
                j += 1
                
            location_words_used.add(w)
            
            for lt in loc_tokens:
                cl = re.sub(r'[^\w:]', '', lt)
                if not cl or cl in INSTRUCTION_WORDS:
                    continue
                if (len(cl) == 1 and cl.isalpha()) or (len(cl) == 2 and cl[0].isalpha() and cl[1] == ':'):
                    drive_filters.add(cl[0].upper() + ":")
                elif is_drive:
                    folder_filters.add(cl)
                else:
                    folder_filters.add(cl)
            i = j
        else:
            i += 1

    # Re-normalize for general parsing without punctuation
    normalized_q = re.sub(r'[^\w\s]', ' ', q)
    normalized_q = re.sub(r'\s+', ' ', normalized_q).strip()
    tokens = normalized_q.split()

    metadata_terms: set[str] = set()
    extension_filters: set[str] = set()
    tag_terms: set[str] = set()
    weak_tag_terms: set[str] = set()
    content_terms: set[str] = set()
    ignored_terms: set[str] = set()

    for token in tokens:
        # Ignore words consumed by location parser
        if token in location_words_used or token + ":" in location_words_used:
            continue
            
        if token in INSTRUCTION_WORDS:
            ignored_terms.add(token)
            continue
            
        # Ignore random single-letter tokens to prevent junk matching, unless it's a known extension
        if len(token) == 1 and token not in FILE_TYPE_MAP:
            ignored_terms.add(token)
            continue
        
        handled = False
        
        if token in FILE_TYPE_MAP:
            extension_filters.update(FILE_TYPE_MAP[token]["exts"])
            for t in FILE_TYPE_MAP[token]["tags"]:
                if t in WEAK_TAGS:
                    weak_tag_terms.add(t)
                else:
                    tag_terms.add(t)
            handled = True
            
        if token in CATEGORY_TAGS:
            if token in WEAK_TAGS:
                weak_tag_terms.add(token)
            else:
                tag_terms.add(token)
            handled = True
            
        if not handled:
            metadata_terms.add(token)
            content_terms.add(token)
            
    for token in tokens:
        if token in location_words_used or token + ":" in location_words_used:
            continue
        if token in CATEGORY_TAGS and token not in INSTRUCTION_WORDS:
            metadata_terms.add(token)

    return {
        "original": original_query,
        "normalized": normalized_q,
        "metadata_terms": list(metadata_terms),
        "extension_filters": list(extension_filters),
        "tag_terms": list(tag_terms),
        "weak_tag_terms": list(weak_tag_terms),
        "content_terms": list(content_terms),
        "ignored_terms": list(ignored_terms),
        "drive_filters": list(drive_filters),
        "folder_filters": list(folder_filters),
        "location_filters": list(drive_filters) + list(folder_filters)
    }
