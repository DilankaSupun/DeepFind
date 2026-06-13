import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../engine')))
from database.db import get_connection

with get_connection() as conn:
    print(conn.execute("SELECT COUNT(*) FROM files_fts WHERE extracted_text MATCH 'buddhism'").fetchone()[0])
