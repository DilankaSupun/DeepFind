import urllib.request, urllib.parse, json

BASE_URL = 'http://127.0.0.1:8765'

queries = [
  ('hello world in drive D', 'all'),
  ('hello world in drive E', 'all'),
  ('hello world in E:', 'all'),
  ('cv pdf in Downloads', 'all'),
  ('assignment pdf in UCSC Year2', 'all')
]

print('=== Location Test ===')
for q, t in queries:
  url = f"{BASE_URL}/search?q={urllib.parse.quote(q)}&type={t}&debug=true"
  try:
    with urllib.request.urlopen(url) as response:
      data = json.loads(response.read())
      print(f'\nQuery: "{q}" (type={t})')
      print(f'Total matches: {data.get("total")}')
      if data.get("parsed_query"):
          print('Drive filters:', data["parsed_query"].get("drive_filters"))
          print('Folder filters:', data["parsed_query"].get("folder_filters"))
      if data.get("results"):
          print('Top Result Match Reasons:', data["results"][0].get("matched_reasons"))
          print('Top Result Match Location:', data["results"][0].get("matched_location"))
          print('Top Result Path:', data["results"][0].get("path"))
  except Exception as e:
    print(f'Query "{q}" failed:', e)
