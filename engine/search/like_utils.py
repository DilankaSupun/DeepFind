"""
DeepFind Engine — LIKE Escape Utilities (Step 25)

Provides a shared helper for safely escaping user-supplied terms before
embedding them in SQLite LIKE patterns.

SQLite LIKE special characters:
  %   matches any sequence of zero or more characters
  _   matches any single character
  \\  is the escape character when LIKE ? ESCAPE '\\' is used

Without escaping, a user query like "report_2024" would match
"reportX2024", "report02024", etc., and "50%off" would match
"50anything-off".

Usage in SQL:
    lower(name) LIKE ? ESCAPE '\\'
    params: [f"%{escape_like(term)}%"]

The application-level wildcards (leading/trailing %) are added by the
calling code AFTER escaping — never include them in the escaped string.
"""

_LIKE_ESCAPE_CHAR = "\\"


def escape_like(term: str) -> str:
    """
    Escape a user-supplied string for safe use inside a SQLite LIKE pattern.

    Escapes (in order):
      1. backslash  \\  →  \\\\
      2. percent     %  →  \\%
      3. underscore  _  →  \\_

    The caller is responsible for adding the application-level wildcards
    (e.g. surrounding % for substring search) AFTER calling this function.

    Example:
        escape_like("report_2024")  →  "report\\_2024"
        escape_like("50%off")       →  "50\\%off"
        escape_like("C:\\users")    →  "C:\\\\users"
    """
    if not term:
        return term
    # Order matters: escape backslash first so we don't double-escape
    escaped = term.replace(_LIKE_ESCAPE_CHAR, _LIKE_ESCAPE_CHAR * 2)
    escaped = escaped.replace("%", f"{_LIKE_ESCAPE_CHAR}%")
    escaped = escaped.replace("_", f"{_LIKE_ESCAPE_CHAR}_")
    return escaped


def like_clause(column_expr: str, pattern_type: str = "contains") -> str:
    """
    Return a LIKE clause fragment with ESCAPE for a given column expression.

    pattern_type:
      'contains'  →  column_expr LIKE ? ESCAPE '\\'   (caller adds %...% around term)
      'prefix'    →  column_expr LIKE ? ESCAPE '\\'   (caller adds term.% suffix)
      'exact'     →  column_expr = ?                  (no LIKE, no escaping needed)

    This is a convenience wrapper so callers don't repeat the ESCAPE literal.
    """
    if pattern_type == "exact":
        return f"{column_expr} = ?"
    return f"{column_expr} LIKE ? ESCAPE '\\\\'"
