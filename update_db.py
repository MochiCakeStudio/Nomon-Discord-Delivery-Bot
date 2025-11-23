import sqlite3

def migrate_bump_db():
    db_path = 'databases/bump.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get list of columns in partner_threads
    cursor.execute("PRAGMA table_info(partner_threads)")
    columns = [info[1] for info in cursor.fetchall()]

    if 'last_bump_message_id' not in columns:
        cursor.execute("ALTER TABLE partner_threads ADD COLUMN last_bump_message_id INTEGER")

    # Initialize last_bump_message_id to NULL for all rows (if needed)
    cursor.execute("UPDATE partner_threads SET last_bump_message_id = NULL WHERE last_bump_message_id IS NULL")

    conn.commit()
    conn.close()
    print("Database migration complete: Added 'last_bump_message_id' column to partner_threads table.")

if __name__ == "__main__":
    migrate_bump_db()
