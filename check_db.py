import sqlite3

conn = sqlite3.connect("data/recruitx.db")
cur = conn.cursor()

print("\n=== Candidate 51 ===")
cur.execute("""
SELECT id, name, location
FROM candidates
WHERE id = 51
""")

print(cur.fetchone())

print("\n=== Candidates containing 'Kanpur' ===")
cur.execute("""
SELECT id, name, location
FROM candidates
WHERE location LIKE '%Kanpur%'
""")

rows = cur.fetchall()

for row in rows:
    print(row)

conn.close()