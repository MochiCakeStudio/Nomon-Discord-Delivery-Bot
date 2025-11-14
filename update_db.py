import sqlite3
import os

# Ensure databases directory exists
os.makedirs('databases', exist_ok=True)

conn = sqlite3.connect('databases/bump.db')
cursor = conn.cursor()

# Add missing columns to servers table
try:
    cursor.execute('ALTER TABLE servers ADD COLUMN forum_channel_id INTEGER')
except sqlite3.OperationalError:
    pass  # Column might already exist

try:
    cursor.execute('ALTER TABLE servers ADD COLUMN plan_type TEXT DEFAULT "affiliate"')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('ALTER TABLE servers ADD COLUMN server_name TEXT')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('ALTER TABLE servers ADD COLUMN advertisement TEXT')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('ALTER TABLE servers ADD COLUMN tags TEXT')
except sqlite3.OperationalError:
    pass

# Create whitelisted_servers table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS whitelisted_servers (
        server_id INTEGER PRIMARY KEY
    )
''')

# Create global_partner_threads table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS global_partner_threads (
        hosting_server_id INTEGER,
        thread_id INTEGER,
        advertised_server_id INTEGER,
        PRIMARY KEY (hosting_server_id, advertised_server_id),
        FOREIGN KEY (hosting_server_id) REFERENCES servers (server_id),
        FOREIGN KEY (advertised_server_id) REFERENCES servers (server_id)
    )
''')

conn.commit()
conn.close()

print('Database updated successfully')
