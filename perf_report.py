import sqlite3, json, urllib.request, urllib.parse

def get_db_stats():
    conn = sqlite3.connect('engine/data/deepfind.db')
    total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    extracted = conn.execute("SELECT COUNT(*) FROM files WHERE status = 'content_extracted'").fetchone()[0]
    tagged = conn.execute("SELECT COUNT(*) FROM files WHERE tags IS NOT NULL AND tags != ''").fetchone()[0]
    return total, extracted, tagged

total_files, extracted_files, tagged_files = get_db_stats()

print(f"Total Indexed: {total_files}")
print(f"Extracted: {extracted_files}")
print(f"Tagged: {tagged_files}")

BASE_URL = 'http://127.0.0.1:8765'

queries = [
  ('pdf', 'metadata'),
  ('ayya pdf', 'all'),
  ('UI UX Design', 'content'),
  ('finder pdf contain UI/UX Design', 'all'),
  ('password getElementById in folder E', 'all')
]

print('\n=== Performance Report ===')
for q, t in queries:
  url = f"{BASE_URL}/search?q={urllib.parse.quote(q)}&type={t}&debug=true"
  try:
    with urllib.request.urlopen(url) as response:
      data = json.loads(response.read())
      print(f'\nQuery: "{q}" (type={t})')
      print(f'Total matches: {data.get("total")}')
      print(f'Timings: {data.get("timing_ms")}')
  except Exception as e:
    print(f'Query "{q}" failed:', e)
