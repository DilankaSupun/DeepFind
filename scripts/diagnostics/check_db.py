import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../engine')))
from database.db import get_connection

with get_connection() as conn:
    count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    print(f"FILES IN DB: {count}")
