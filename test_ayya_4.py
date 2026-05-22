import sys
sys.path.append(".")
from search.query_parser import parse_query
from search.filename_search import search_files

parsed = parse_query("pdfs in ayya folder")
res = search_files(parsed, limit=50)
for r in res['results']:
    print(r['path'])
    print("matched_folder:", r.get("matched_folder_filters"))
