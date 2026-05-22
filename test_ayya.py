import sys
sys.path.append("engine")
from search.query_parser import parse_query
from search.hybrid_search import unified_search

parsed = parse_query("pdfs in ayya folder")
print("Parsed:")
print(parsed)

res = unified_search("pdfs in ayya folder", mode="all", limit=50)
print(f"Results: {res['total']}")
if res['results']:
    print(f"Top 1: {res['results'][0]['name']}")
    print(f"Reasons: {res['results'][0]['matched_reasons']}")
