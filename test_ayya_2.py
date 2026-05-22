import sys
sys.path.append(".")
from search.query_parser import parse_query
from search.filename_search import search_files
from search.hybrid_search import unified_search

parsed = parse_query("pdfs in ayya folder")
res = search_files(parsed, limit=50)
print(f"Filename Search Results: {res['total']}")
if res['results']:
    print(f"Top 1: {res['results'][0]['name']}")
