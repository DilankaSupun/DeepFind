import sys
sys.path.append(".")
from search.query_parser import parse_query
from search.filename_search import search_files
from search.hybrid_search import unified_search, _calculate_score

parsed = parse_query("pdfs in ayya folder")
res = search_files(parsed, limit=50)

for r in res['results']:
    _calculate_score(r, parsed)
    print("Name:", r['name'])
    print("Score:", r.get('score'))
    print("Matched Folder:", r.get("matched_folder_filters"))
    print("Matched Exts:", r.get("matched_extensions"))
    print("---")
