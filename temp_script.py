import sqlite3

conn = sqlite3.connect('databases/bump.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

for table in tables:
    print(f"\nSchema for {table}:")
    cursor.execute(f'PRAGMA table_info({table})')
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

conn.close()
