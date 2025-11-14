import sqlite3
import os

# Update the bump database to include devs table
db_path = 'databases/bump.db'
os.makedirs('databases', exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create devs table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS devs (
        user_id INTEGER PRIMARY KEY
    )
''')

# Insert default dev (replace with your actual user ID)
cursor.execute('INSERT OR IGNORE INTO devs (user_id) VALUES (?)', (1234567890,))

conn.commit()
conn.close()

print("Database updated with devs table.")
