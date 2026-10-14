import sqlite3
import os

db_path = os.path.expandvars(r"%APPDATA%\9router\db\data.sqlite")
print("DB path:", db_path, "Exists:", os.path.exists(db_path))

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

for table in tables:
    cur.execute(f"PRAGMA table_info({table});")
    cols = [r[1] for r in cur.fetchall()]
    cur.execute(f"SELECT count(*) FROM {table};")
    cnt = cur.fetchone()[0]
    print(f"Table '{table}' ({cnt} rows): cols = {cols}")
    if any(k in table.lower() for k in ("key", "token", "user", "auth", "config", "setting", "provider")):
        cur.execute(f"SELECT * FROM {table} LIMIT 5;")
        for r in cur.fetchall():
            # Mask sensitive values slightly
            safe_r = [str(x)[:15] + "..." if isinstance(x, str) and len(x) > 20 else x for x in r]
            print(f"   Row: {safe_r}")
