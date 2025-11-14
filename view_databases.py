import sqlite3
import os

def view_database(db_path, db_name):
    if not os.path.exists(db_path):
        print(f"Database {db_name} does not exist.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"=== {db_name.upper()} DATABASE ===")
    if not tables:
        print("No tables found in this database.")
        conn.close()
        return

    for table_name, in tables:
        print(f"\n--- Table: {table_name} ---")

        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Columns: {', '.join(column_names)}")

        # Get all rows
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print("No data in table")
        else:
            print(f"Data ({len(rows)} rows):")
            for row in rows:
                print(f"  {row}")

    conn.close()

def main():
    databases_dir = 'databases'
    if not os.path.exists(databases_dir):
        print("Databases directory does not exist.")
        return

    db_files = [f for f in os.listdir(databases_dir) if f.endswith('.db')]
    if not db_files:
        print("No database files found.")
        return

    for db_file in db_files:
        db_path = os.path.join(databases_dir, db_file)
        db_name = db_file[:-3]  # Remove .db extension
        view_database(db_path, db_name)
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
