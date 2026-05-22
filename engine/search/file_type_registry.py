"""
DeepFind Engine — Central File Type Registry
Defines mappings between common terms and actual file extensions,
plus metadata regarding extractability.
"""

REGISTRY = {
    "pdf": {
        "label": "PDF Document",
        "extensions": [".pdf"],
        "aliases": ["pdf", "pdfs", "pdf file", "pdf files", "pdf document", "pdf documents"],
        "category": "document",
        "extractable": True,
        "semantic_supported": True
    },
    "word": {
        "label": "Word Document",
        "extensions": [".docx", ".doc"],
        "aliases": ["word", "doc", "docx", "word file", "word files", "word document", "word documents"],
        "category": "document",
        "extractable": True,
        "semantic_supported": True
    },
    "powerpoint": {
        "label": "PowerPoint Presentation",
        "extensions": [".pptx", ".ppt"],
        "aliases": ["powerpoint", "ppt", "pptx", "presentation", "presentations", "slide", "slides"],
        "category": "document",
        "extractable": False,
        "semantic_supported": False
    },
    "excel": {
        "label": "Excel Spreadsheet",
        "extensions": [".xlsx", ".xls", ".csv"],
        "aliases": ["excel", "spreadsheet", "xls", "xlsx", "csv", "sheet", "sheets"],
        "category": "document",
        "extractable": True,
        "semantic_supported": True
    },
    "text": {
        "label": "Text File",
        "extensions": [".txt", ".md", ".rtf"],
        "aliases": ["text", "txt", "markdown", "md", "notes", "note files"],
        "category": "document",
        "extractable": True,
        "semantic_supported": True
    },
    "opendocument": {
        "label": "OpenDocument",
        "extensions": [".odt", ".ods", ".odp"],
        "aliases": ["opendocument", "libreoffice", "openoffice"],
        "category": "document",
        "extractable": False,
        "semantic_supported": False
    },
    "javascript": {
        "label": "JavaScript",
        "extensions": [".js", ".jsx", ".mjs", ".cjs"],
        "aliases": ["js", "javascript", "js file", "js files", "javascript file", "javascript files"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "typescript": {
        "label": "TypeScript",
        "extensions": [".ts", ".tsx"],
        "aliases": ["ts", "typescript", "typescript file", "typescript files"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "html": {
        "label": "HTML",
        "extensions": [".html", ".htm"],
        "aliases": ["html", "html file", "html files", "webpage", "web page"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "css": {
        "label": "CSS",
        "extensions": [".css", ".scss", ".sass", ".less"],
        "aliases": ["css", "stylesheet", "stylesheets", "scss", "sass", "less"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "php": {
        "label": "PHP",
        "extensions": [".php"],
        "aliases": ["php", "php file", "php files"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "python": {
        "label": "Python",
        "extensions": [".py", ".pyw", ".ipynb"],
        "aliases": ["python", "py", "python file", "python files", "notebook", "jupyter"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "java": {
        "label": "Java",
        "extensions": [".java", ".class", ".jar"],
        "aliases": ["java", "java file", "jar"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "cpp": {
        "label": "C/C++",
        "extensions": [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"],
        "aliases": ["c", "cpp", "c++", "header", "headers"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "csharp": {
        "label": "C#",
        "extensions": [".cs"],
        "aliases": ["csharp", "c#", "cs file"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "sql": {
        "label": "SQL",
        "extensions": [".sql"],
        "aliases": ["sql", "database script", "database scripts"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "config": {
        "label": "Configuration",
        "extensions": [".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".conf", ".cfg", ".env", ".log"],
        "aliases": ["json", "xml", "yaml", "yml", "config", "configuration", "ini", "log", "logs", "environment file"],
        "category": "config",
        "extractable": True,
        "semantic_supported": True
    },
    "shell": {
        "label": "Shell Script",
        "extensions": [".bat", ".cmd", ".ps1", ".sh", ".bash"],
        "aliases": ["batch", "bat", "cmd", "powershell", "ps1", "shell", "bash", "script", "scripts"],
        "category": "code",
        "extractable": True,
        "semantic_supported": True
    },
    "executable": {
        "label": "Executable",
        "extensions": [".exe"],
        "aliases": ["exe", "executable", "executable file", "application", "program", "app", "exe files"],
        "category": "application",
        "extractable": False,
        "semantic_supported": False
    },
    "installer": {
        "label": "Installer",
        "extensions": [".msi", ".msix", ".appx"],
        "aliases": ["installer", "setup", "msi", "app installer"],
        "category": "application",
        "extractable": False,
        "semantic_supported": False
    },
    "library": {
        "label": "System Library",
        "extensions": [".dll", ".sys", ".drv", ".ocx"],
        "aliases": ["dll", "library", "system file", "driver"],
        "category": "application",
        "extractable": False,
        "semantic_supported": False
    },
    "shortcut": {
        "label": "Shortcut",
        "extensions": [".lnk", ".url"],
        "aliases": ["shortcut", "shortcuts", "link", "links"],
        "category": "application",
        "extractable": False,
        "semantic_supported": False
    },
    "iso": {
        "label": "Disk Image",
        "extensions": [".iso", ".img"],
        "aliases": ["iso", "disk image", "image file"],
        "category": "archive",
        "extractable": False,
        "semantic_supported": False
    },
    "android": {
        "label": "Android Package",
        "extensions": [".apk", ".aab"],
        "aliases": ["apk", "android app", "android package"],
        "category": "application",
        "extractable": False,
        "semantic_supported": False
    },
    "archive": {
        "label": "Archive",
        "extensions": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
        "aliases": ["zip", "rar", "archive", "compressed", "compressed file", "7z", "archive files", "archive file"],
        "category": "archive",
        "extractable": False,
        "semantic_supported": False
    },
    "image": {
        "label": "Image",
        "extensions": [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".ico"],
        "aliases": ["image", "images", "picture", "pictures", "photo", "photos", "image files", "image file"],
        "category": "media",
        "extractable": False,
        "semantic_supported": False
    },
    "vector": {
        "label": "Vector Image",
        "extensions": [".svg"],
        "aliases": ["svg", "vector", "vector image"],
        "category": "media",
        "extractable": False,
        "semantic_supported": False
    },
    "design": {
        "label": "Design File",
        "extensions": [".psd", ".ai", ".fig", ".xd", ".sketch"],
        "aliases": ["photoshop", "illustrator", "figma", "adobe xd", "sketch", "design file", "design files"],
        "category": "media",
        "extractable": False,
        "semantic_supported": False
    },
    "video": {
        "label": "Video",
        "extensions": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"],
        "aliases": ["video", "videos", "movie", "movies", "video file", "video files"],
        "category": "media",
        "extractable": False,
        "semantic_supported": False
    },
    "audio": {
        "label": "Audio",
        "extensions": [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"],
        "aliases": ["audio", "music", "song", "songs", "sound", "audio file", "audio files"],
        "category": "media",
        "extractable": False,
        "semantic_supported": False
    },
    "subtitle": {
        "label": "Subtitle",
        "extensions": [".srt", ".vtt"],
        "aliases": ["subtitle", "subtitles"],
        "category": "media",
        "extractable": True,
        "semantic_supported": False
    },
    "font": {
        "label": "Font",
        "extensions": [".ttf", ".otf", ".woff", ".woff2"],
        "aliases": ["font", "fonts"],
        "category": "media",
        "extractable": False,
        "semantic_supported": False
    },
    "database": {
        "label": "Database",
        "extensions": [".db", ".sqlite", ".sqlite3", ".mdb", ".accdb"],
        "aliases": ["database", "db", "sqlite", "access database", "database files"],
        "category": "database",
        "extractable": False,
        "semantic_supported": False
    },
    "backup": {
        "label": "Backup/Temp",
        "extensions": [".tmp", ".bak", ".old", ".backup"],
        "aliases": ["temp", "temporary", "backup", "backups", "old file"],
        "category": "backup",
        "extractable": False,
        "semantic_supported": False
    }
}

# Build reverse maps
ALIAS_TO_EXTENSIONS = {}
EXTENSION_TO_INFO = {}

for key, data in REGISTRY.items():
    for alias in data["aliases"]:
        ALIAS_TO_EXTENSIONS[alias.lower()] = data["extensions"]
    for ext in data["extensions"]:
        EXTENSION_TO_INFO[ext] = data

def normalize_extension(ext: str) -> str:
    ext = ext.lower()
    return ext if ext.startswith(".") else f".{ext}"

def extensions_for_alias(alias: str) -> list[str]:
    return ALIAS_TO_EXTENSIONS.get(alias.lower(), [])

def label_for_extension(ext: str) -> str:
    info = EXTENSION_TO_INFO.get(normalize_extension(ext))
    return info["label"] if info else ext.replace(".", "").upper()

def category_for_extension(ext: str) -> str:
    info = EXTENSION_TO_INFO.get(normalize_extension(ext))
    return info["category"] if info else "unknown"

def is_extractable_extension(ext: str) -> bool:
    info = EXTENSION_TO_INFO.get(normalize_extension(ext))
    return info["extractable"] if info else False

def is_semantic_supported_extension(ext: str) -> bool:
    info = EXTENSION_TO_INFO.get(normalize_extension(ext))
    return info["semantic_supported"] if info else False

def is_binary_extension(ext: str) -> bool:
    info = EXTENSION_TO_INFO.get(normalize_extension(ext))
    # If it's explicitly marked as non-extractable, we treat as binary
    return not info["extractable"] if info else True

def detect_file_type_phrases(query: str) -> tuple[list[str], list[str]]:
    """
    Returns (matched_extensions, removed_terms)
    We sort aliases by length descending so "pdf files" matches before "pdf".
    """
    query_lower = query.lower()
    found_exts = set()
    removed_terms = []

    # Simple alias match
    # We'll split query into words to ensure boundary matching, 
    # but some aliases have spaces.
    
    # Sort aliases by word length descending to prevent partial match
    all_aliases = sorted(ALIAS_TO_EXTENSIONS.keys(), key=lambda x: len(x.split()), reverse=True)
    
    for alias in all_aliases:
        # Require word boundaries for the alias
        import re
        pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(pattern, query_lower):
            found_exts.update(ALIAS_TO_EXTENSIONS[alias])
            removed_terms.append(alias)
            # Remove from query to prevent matching smaller parts
            query_lower = re.sub(pattern, "", query_lower)

    return list(found_exts), removed_terms
