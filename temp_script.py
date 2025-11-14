import sqlite3
conn = sqlite3.connect('databases/bump.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print(tables)
conn.close()
