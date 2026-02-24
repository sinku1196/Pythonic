from utils.sqlite_manager import SQLiteManager
from utils.sql_db.ms_sql_pyodbc import MSSQLDatabase
from utils.sql_db.queries import credentials_query

# SQLite (safe serialized manager)
db = SQLiteManager("python.db")

# MS SQL Server connection
ms_sql = MSSQLDatabase(
    "localhost",
    "UC_Analytics_Master",
    "sa",
    "my_laptop"
)

# ----------------------------
# Fetch data from SQL Server
# ----------------------------

rows = ms_sql.fetch_all("""
    SELECT 
        ClientID, 
        ExperityUsername, 
        ExperityPassword, 
        ExperityPassphrase
    FROM UC_Analytics_Master..ExperityCredentials
""")

if not rows:
    print("No data found.")
    exit(0)

# ----------------------------
# Ensure SQLite table exists
# ----------------------------

db.execute("""
CREATE TABLE IF NOT EXISTS ExperityCredentials (
    ClientID INTEGER PRIMARY KEY,
    ExperityUsername TEXT,
    ExperityPassword TEXT,
    ExperityPassphrase TEXT
)
""")

# ----------------------------
# Insert into SQLite (atomic)
# ----------------------------

insert_sql = """
INSERT OR REPLACE INTO ExperityCredentials (
    ClientID,
    ExperityUsername,
    ExperityPassword,
    ExperityPassphrase
) VALUES (?, ?, ?, ?)
"""

def insert_batch(conn):
    cur = conn.cursor()
    cur.executemany(insert_sql, rows)

# Atomic, serialized, crash-safe transaction
db.transaction(insert_batch)

print(f"Inserted {len(rows)} rows into SQLite.")