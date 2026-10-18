import sqlite3

conn = sqlite3.connect('library_db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
print("Tables found:", tables)

for t in tables:
    count = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    sample = [dict(row) for row in c.execute(f"SELECT * FROM {t} LIMIT 2").fetchall()]
    print(f"\n--- {t} (Count: {count}) ---")
    for s in sample:
        print("  ", s)
