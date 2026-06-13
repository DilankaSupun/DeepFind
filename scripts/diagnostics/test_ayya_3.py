import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine"))
from search.query_parser import parse_query
from search.filename_search import search_files
from search.hybrid_search import unified_search

parsed = parse_query("pdfs in ayya folder")

res = unified_search("pdfs in ayya folder", mode="all", limit=50)
print(f"Hybrid Results: {res['total']}")
if not res['results']:
    print("Zero results returned!")
else:
    print(res['results'][0])

#hello world