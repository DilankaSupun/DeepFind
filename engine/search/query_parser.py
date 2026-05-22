"""
DeepFind Engine — Natural Query Parser (Step 16 Patch)

Parses natural language search queries into meaningful structured parts.
Uses lightweight dictionaries and regex, avoiding heavy AI/NLP models.
Separates file type intent, folder intent, exact phrases, and semantic terms.
Includes Important Term extraction for coverage scoring.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Any

from search.file_type_registry import detect_file_type_phrases

# Words that should be ignored if they are used as instructions
INSTRUCTION_WORDS = {
    "find", "search", "show", "me", "file", "files", "contain", "contains",
    "containing", "consist", "consists", "with", "using", "use", "uses",
    "has", "have", "about", "related", "that", "the", "a", "an", "of",
    "in", "from", "for", "to", "and", "or", "inside", "under"
}

LITERAL_INTENT_WORDS = {
    "named", "called", "name", "title", "exactly"
}

WEAK_TAGS = {
    "document", "file", "text", "data", "common"
}

CATEGORY_TAGS = {
    "code", "document", "design", "university", "project", "finance",
    "payment", "invoice", "receipt", "cv", "resume", "career", "database",
    "frontend", "backend", "api", "figma", "logo", "assignment", "tutorial",
    "practical", "lecture", "exam"
}

def _extract_time_filter(query: str):
    date_filters = {
        "field": None,
        "modified_after": None,
        "modified_before": None,
        "created_after": None,
        "created_before": None,
        "indexed_after": None,
        "indexed_before": None,
        "modified_year": None,
        "created_year": None,
        "indexed_year": None,
        "fallback_to_modified": False,
        "label": None
    }
    matched_words = set()
    
    # 1. Determine the target field
    field = "modified_at" # default
    q_lower = query.lower()
    
    if re.search(r'\b(?:created|made|generated)\b', q_lower):
        field = "created_at"
        date_filters["fallback_to_modified"] = True
        matched_words.update(re.findall(r'\b(?:created|made|generated)\b', q_lower))
    elif re.search(r'\b(?:indexed|scanned|added)\b', q_lower):
        field = "last_indexed_at"
        matched_words.update(re.findall(r'\b(?:indexed|scanned|added(?: to deepfind)?)\b', q_lower))
    elif re.search(r'\b(?:modified|updated|changed|edited|revised)\b', q_lower):
        field = "modified_at"
        matched_words.update(re.findall(r'\b(?:last )?(?:modified|updated|changed|edited|revised)\b', q_lower))
        
    date_filters["field"] = field
    
    # 2. Extract relative time ranges
    patterns = [
        r'\b(?:in\s+)?(?:last|past)\s+(\d+)\s+(days?|weeks?|months?|years?)\b',
        r'\b(?:in\s+)?(?:last|past)\s+(week|month|year)\b',
        r'\b(?:in\s+)?this\s+(week|month|year)\b',
        r'\b(today|yesterday)\b'
    ]
    
    now = datetime.now()
    range_after = None
    range_before = None
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, q_lower)
        if match:
            matched_str = match.group(0)
            words = re.findall(r'\b\w+\b', matched_str)
            matched_words.update(words)
            
            if i == 0:
                num = int(match.group(1))
                unit = match.group(2)
                if unit.startswith('day'): range_after = now - timedelta(days=num)
                elif unit.startswith('week'): range_after = now - timedelta(days=num * 7)
                elif unit.startswith('month'): range_after = now - timedelta(days=num * 30)
                elif unit.startswith('year'): range_after = now - timedelta(days=num * 365)
            elif i == 1:
                unit = match.group(1)
                if unit == 'week': range_after = now - timedelta(days=7)
                elif unit == 'month': range_after = now - timedelta(days=30)
                elif unit == 'year': range_after = now - timedelta(days=365)
            elif i == 2:
                unit = match.group(1)
                if unit == 'week': 
                    range_after = now - timedelta(days=now.weekday())
                    range_after = range_after.replace(hour=0, minute=0, second=0, microsecond=0)
                elif unit == 'month': range_after = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                elif unit == 'year': range_after = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            elif i == 3:
                word = match.group(1)
                if word == 'today': 
                    range_after = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    range_before = range_after + timedelta(days=1)
                elif word == 'yesterday': 
                    range_after = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    range_before = range_after + timedelta(days=1)
            
            date_filters["label"] = matched_str.strip()
            break

    # Look for year, e.g., 2023, 2024 if no relative range matched
    year_match = re.search(r'\b(?:in\s+)?(20[0-2][0-9])\b', q_lower)
    if year_match and not range_after:
        matched_str = year_match.group(0)
        year_str = year_match.group(1)
        matched_words.update(re.findall(r'\b\w+\b', matched_str))
        if field == "created_at":
            date_filters["created_year"] = int(year_str)
            date_filters["label"] = f"created in {year_str}"
        elif field == "last_indexed_at":
            date_filters["indexed_year"] = int(year_str)
            date_filters["label"] = f"indexed in {year_str}"
        else:
            date_filters["modified_year"] = int(year_str)
            date_filters["label"] = year_str

    if range_after:
        after_str = range_after.strftime("%Y-%m-%dT%H:%M:%S")
        before_str = range_before.strftime("%Y-%m-%dT%H:%M:%S") if range_before else None
        
        if field == "created_at":
            date_filters["created_after"] = after_str
            if before_str: date_filters["created_before"] = before_str
        elif field == "last_indexed_at":
            date_filters["indexed_after"] = after_str
            if before_str: date_filters["indexed_before"] = before_str
        else:
            date_filters["modified_after"] = after_str
            if before_str: date_filters["modified_before"] = before_str
            
        if not date_filters["label"]:
            date_filters["label"] = f"{field.replace('_at', '')} after {after_str}"
            
    return date_filters, matched_words

def _extract_folder_intent(query_lower: str, raw_tokens: List[str]):
    drive_filters = set()
    folder_filters = set()
    folder_phrase_filters = set()
    location_words_used = set()
    
    i = 0
    while i < len(raw_tokens):
        w = raw_tokens[i].lower()
        clean_w = re.sub(r'[^\w:]', '', w)
        
        if clean_w in ("in", "inside", "from", "under"):
            loc_tokens = []
            j = i + 1
            is_drive = False
            is_folder = False
            
            if j < len(raw_tokens):
                cw = re.sub(r'[^\w]', '', raw_tokens[j].lower())
                if cw == "drive":
                    is_drive = True
                    location_words_used.add(raw_tokens[j].lower())
                    j += 1
                elif cw == "folder":
                    is_folder = True
                    location_words_used.add(raw_tokens[j].lower())
                    j += 1
            
            while j < len(raw_tokens):
                cw = re.sub(r'[^\w:]', '', raw_tokens[j].lower())
                if cw in ("folder", "drive"):
                    location_words_used.add(raw_tokens[j].lower())
                    if cw == "drive": is_drive = True
                    if cw == "folder": is_folder = True
                    j += 1
                    break
                
                # If we encounter another location keyword or time keyword, break
                if cw in ("in", "inside", "from", "under", "last", "past", "this", "today", "yesterday"):
                    break
                    
                loc_tokens.append(raw_tokens[j])
                location_words_used.add(raw_tokens[j].lower())
                j += 1
                
            if loc_tokens:
                location_words_used.add(w) # Add "in", "from" etc
                
                phrase = " ".join(loc_tokens).strip()
                if len(loc_tokens) > 1:
                    folder_phrase_filters.add(phrase)
                
                for lt in loc_tokens:
                    cl = re.sub(r'[^\w:]', '', lt.lower())
                    if not cl or cl in INSTRUCTION_WORDS:
                        continue
                    if (len(cl) == 1 and cl.isalpha()) or (len(cl) == 2 and cl[0].isalpha() and cl[1] == ':'):
                        drive_filters.add(cl[0].upper() + ":")
                    else:
                        folder_filters.add(cl)
            i = j
        else:
            i += 1

    return list(drive_filters), list(folder_filters), list(folder_phrase_filters), location_words_used


def parse_query(original_query: str) -> Dict[str, Any]:
    """
    Universal Query Intent Parser.
    Parses a natural query into structured match criteria.
    """
    q_lower = original_query.lower().strip()

    # Normalize UI/UX, ui-ux, ui_ux to "ui ux"
    q_lower = re.sub(r'ui[/-_]ux', 'ui ux', q_lower)
    
    # 1. Date/Time filter extraction
    date_filters, time_words_used = _extract_time_filter(original_query)
    
    # 2. File type alias extraction (from registry)
    registry_exts, registry_removed = detect_file_type_phrases(q_lower)
    # The detect function removes the alias from the query, but we don't use the stripped query globally
    # Instead we track which words were part of aliases so we can ignore them as content terms
    file_type_words_used = set()
    for phrase in registry_removed:
        for w in phrase.split():
            file_type_words_used.add(w)

    raw_tokens = original_query.split()
    
    # 3. Folder/Location extraction
    drive_filters, folder_filters, folder_phrase_filters, location_words_used = _extract_folder_intent(q_lower, raw_tokens)

    extension_filters = set(registry_exts)
    file_type_terms = set(registry_removed)
    metadata_terms = set()
    tag_terms = set()
    weak_tag_terms = set()
    content_terms = set()
    literal_terms = set()
    semantic_terms = set()
    ignored_terms = set()
    ambiguous_terms = set()
    important_terms = []
    
    # Context flags
    has_literal_intent = any(word in LITERAL_INTENT_WORDS for word in raw_tokens)
    has_folder_intent = bool(folder_filters or folder_phrase_filters or drive_filters)
    has_date_intent = date_filters.get("modified_after") or date_filters.get("modified_year")
    
    intent_confidence = {
        "file_type": 1.0 if extension_filters else 0.0,
        "literal_keyword": 0.0,
        "folder": 1.0 if has_folder_intent else 0.0,
        "date": 1.0 if has_date_intent else 0.0,
        "semantic": 0.0
    }

    if has_literal_intent:
        intent_confidence["literal_keyword"] = 0.9

    for token in raw_tokens:
        clean_token = token.lower()
        
        # Explicit filename.extension detection (e.g., pdf.rar, setup.exe)
        # We only treat it as explicit extension if it matches \.\w+
        match_explicit = re.search(r'^(.+)\.(\w+)$', clean_token)
        is_literal = False
        
        if match_explicit:
            base_name = match_explicit.group(1)
            ext = match_explicit.group(2)
            
            # Add to literal intent
            literal_terms.add(clean_token)
            literal_terms.add(base_name)
            metadata_terms.add(base_name)
            important_terms.append(base_name)
            
            # Force the exact extension filter
            extension_filters.add(f".{ext}")
            intent_confidence["literal_keyword"] = max(intent_confidence["literal_keyword"], 0.9)
            intent_confidence["file_type"] = 1.0
            is_literal = True
            
            # Skip further normal word processing for this token
            continue

        clean_token = re.sub(r'[^\w]', '', clean_token)
        if not clean_token:
            continue
            
        if clean_token in time_words_used:
            ignored_terms.add(clean_token)
            continue
            
        if clean_token in location_words_used or clean_token + ":" in location_words_used:
            ignored_terms.add(clean_token)
            continue
            
        if clean_token in INSTRUCTION_WORDS or clean_token in LITERAL_INTENT_WORDS:
            ignored_terms.add(clean_token)
            continue

        if clean_token in file_type_words_used:
            # Word was absorbed into an extension filter (e.g. "exe", "files")
            ignored_terms.add(clean_token)
            continue
            
        if clean_token in CATEGORY_TAGS:
            if clean_token in WEAK_TAGS: weak_tag_terms.add(clean_token)
            else: tag_terms.add(clean_token)
            metadata_terms.add(clean_token)
            content_terms.add(clean_token)
            important_terms.append(clean_token)
            continue
            
        # Ignore random single-letter tokens to prevent junk matching unless literal
        if len(clean_token) == 1 and not has_literal_intent:
            ignored_terms.add(clean_token)
            continue

        metadata_terms.add(clean_token)
        content_terms.add(clean_token)
        semantic_terms.add(clean_token)
        important_terms.append(clean_token)
        if has_literal_intent:
            literal_terms.add(clean_token)

    # Extract phrase candidates (proper nouns / titles)
    phrase_tokens = []
    for raw in raw_tokens:
        clean = re.sub(r'[^\w]', '', raw.lower())
        if clean in location_words_used or clean in time_words_used or clean in INSTRUCTION_WORDS or clean in LITERAL_INTENT_WORDS or clean in file_type_words_used:
            continue
        if clean:
            phrase_tokens.append(raw)
            
    phrase_candidates = []
    if len(phrase_tokens) > 1:
        phrase_candidates.append(" ".join(phrase_tokens))

    # Evaluate Search Intent & Gating
    search_intent = "hybrid"
    semantic_allowed = True
    
    if extension_filters:
        # Check if the extensions are mostly binary/metadata-only
        from search.file_type_registry import is_binary_extension
        if any(is_binary_extension(ext) for ext in extension_filters):
            search_intent = "structured"
            semantic_allowed = False
        else:
            # E.g. "python files"
            search_intent = "structured"
            semantic_allowed = False
    
    if has_folder_intent or has_date_intent or intent_confidence["file_type"] > 0.8:
        search_intent = "structured"
        semantic_allowed = False
    elif intent_confidence["literal_keyword"] > 0.8:
        search_intent = "literal"
        semantic_allowed = False
    elif phrase_candidates:
        search_intent = "structured"
        semantic_allowed = False # Strong exact phrases usually aren't semantic requests
    elif len(semantic_terms) >= 2:
        search_intent = "hybrid"
        semantic_allowed = True
        intent_confidence["semantic"] = 0.8

    return {
        "original": original_query,
        "normalized": q_lower,
        
        "extension_filters": list(extension_filters),
        "file_type_terms": list(file_type_terms),
        
        "folder_filters": list(folder_filters),
        "folder_phrase_filters": list(folder_phrase_filters),
        "drive_filters": list(drive_filters),
        
        "date_filters": date_filters,
        
        "phrase_candidates": phrase_candidates,
        "folder_phrase_candidates": phrase_candidates,
        
        "metadata_terms": list(metadata_terms),
        "tag_terms": list(tag_terms),
        "content_terms": list(content_terms),
        "literal_terms": list(literal_terms),
        "important_terms": list(set(important_terms)), # Remove duplicates
        
        "semantic_terms": list(semantic_terms),
        "ignored_terms": list(ignored_terms),
        "ambiguous_terms": list(ambiguous_terms),
        
        "search_intent": search_intent,
        "semantic_allowed": semantic_allowed,
        
        "intent_confidence": intent_confidence
    }
