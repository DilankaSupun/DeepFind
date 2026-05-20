"""
DeepFind Engine — Lightweight Auto-Tagging (Step 11)

Generates comma-separated tags based on heuristics:
- Extension (e.g. .pdf -> pdf, document)
- Path parsing (e.g. /UCSC/Year2/ -> ucsc, year2)
- Text keywords (matching against simple dictionaries)

No AI or external APIs are used here.
"""

import re
import os

# ── Dictionaries ───────────────────────────────────────────────────────────────

EXT_TAGS = {
    # Documents
    ".pdf": ["pdf", "document"],
    ".docx": ["docx", "document"],
    ".doc": ["doc", "document"],
    ".txt": ["text", "document"],
    ".md": ["markdown", "document"],
    ".csv": ["csv", "data"],
    ".json": ["json", "data"],
    ".xml": ["xml", "data"],
    # Code
    ".py": ["python", "code"],
    ".js": ["javascript", "code"],
    ".jsx": ["react", "javascript", "code"],
    ".ts": ["typescript", "code"],
    ".tsx": ["react", "typescript", "code"],
    ".php": ["php", "code"],
    ".java": ["java", "code"],
    ".html": ["html", "web", "code"],
    ".css": ["css", "web", "code"],
    ".sql": ["sql", "database", "code"],
    ".go": ["golang", "code"],
    ".rs": ["rust", "code"],
    ".cpp": ["cpp", "c++", "code"],
    ".c": ["c", "code"],
    # Media
    ".jpg": ["image", "photo"],
    ".jpeg": ["image", "photo"],
    ".png": ["image", "photo"],
    ".webp": ["image", "photo"],
    ".svg": ["svg", "image", "design"],
    ".mp4": ["video", "media"],
    ".mov": ["video", "media"],
    ".avi": ["video", "media"],
    ".mkv": ["video", "media"],
    ".mp3": ["audio", "media"],
    ".wav": ["audio", "media"],
    ".m4a": ["audio", "media"],
    # Archives
    ".zip": ["archive", "zip"],
    ".rar": ["archive", "rar"],
    ".7z": ["archive", "7z"],
    # Design
    ".fig": ["figma", "design"],
    ".psd": ["photoshop", "design"],
    ".ai": ["illustrator", "design"],
}

KEYWORD_CATEGORIES = {
    "finance": ["invoice", "payment", "receipt", "salary", "bank", "transaction", "bill", "payhere"],
    "university": ["assignment", "tutorial", "practical", "lecture", "exam", "coursework", "semester", "ucsc", "year1", "year2", "year3", "year4"],
    "project": ["github", "database", "frontend", "backend", "api", "documentation", "report", "fixlanka"],
    "code": ["function", "class", "import", "controller", "model", "config", "route", "service", "module"],
    "design": ["figma", "logo", "ui", "ux", "wireframe", "prototype", "mockup", "design"],
    "career": ["cv", "resume", "cover letter", "job", "application", "portfolio", "interview"],
}

# Generic words to exclude from path tags
STOP_WORDS = {"users", "documents", "desktop", "downloads", "public", "temp", "tmp", "c", "d", "e", "f"}

# ── Tagging Logic ──────────────────────────────────────────────────────────────

def generate_tags(name: str, path: str, extension: str, extracted_text: str | None = None) -> str:
    """
    Generate a comma-separated list of tags for a file.
    """
    tags = set()

    # 1. Extension tags
    if extension:
        ext_lower = extension.lower()
        if ext_lower in EXT_TAGS:
            tags.update(EXT_TAGS[ext_lower])
        else:
            tags.add(ext_lower.lstrip("."))

    # 2. Path tags
    if path:
        # Get directory parts
        dir_path = os.path.dirname(path)
        parts = re.split(r'[\\/]', dir_path)
        for p in parts:
            p_clean = p.strip().lower()
            if p_clean and p_clean not in STOP_WORDS and len(p_clean) > 2:
                # Also split by spaces/hyphens/underscores if compound
                subparts = re.split(r'[ \-_]', p_clean)
                for sp in subparts:
                    if len(sp) > 2 and sp not in STOP_WORDS:
                        tags.add(sp)

    # 3. Keyword tags (from name and content)
    # Combine name and a chunk of text (up to 10k chars)
    content_to_check = name.lower()
    if extracted_text:
        content_to_check += " " + extracted_text[:10000].lower()

    for category, keywords in KEYWORD_CATEGORIES.items():
        for kw in keywords:
            # simple substring match for speed (or regex boundary match)
            if re.search(r'\b' + re.escape(kw) + r'\b', content_to_check):
                tags.add(category)
                tags.add(kw)

    # 4. Clean up tags
    final_tags = []
    for t in tags:
        t = t.strip().lower()
        # Ensure it's not too long and doesn't contain commas
        t = t.replace(",", " ")
        if len(t) <= 30 and t:
            final_tags.append(t)

    # Max 20 tags per file, sorted for consistency
    final_tags.sort()
    return ",".join(final_tags[:20])

