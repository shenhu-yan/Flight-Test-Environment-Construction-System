import sqlite3
import os
import sys

db_paths = [
    os.path.join(os.path.dirname(__file__), 'flight_test_env.db'),
    os.path.join(os.path.dirname(__file__), 'instance', 'flight_test_env.db'),
    os.path.join(os.path.dirname(__file__), '..', 'instance', 'flight_test_env.db'),
]

db_path = None
for p in db_paths:
    if os.path.exists(p):
        conn = sqlite3.connect(p)
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        print(f"Found DB at {p} with tables: {table_names}")
        if 'environment' in table_names:
            db_path = p
            conn.close()
            break
        conn.close()

if not db_path:
    print("No database with environment table found!")
    sys.exit(1)

print(f"Using database: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(environment)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Current columns: {columns}")

if 'desc_format' not in columns:
    cursor.execute("ALTER TABLE environment ADD COLUMN desc_format VARCHAR(10) DEFAULT 'json'")
    print("Added desc_format column")
else:
    print("desc_format column already exists")

if 'preview_data' not in columns:
    cursor.execute("ALTER TABLE environment ADD COLUMN preview_data TEXT")
    print("Added preview_data column")
else:
    print("preview_data column already exists")

cursor.execute("PRAGMA table_info(environment)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Updated columns: {columns}")

cursor.execute("PRAGMA table_info(adjustment)")
adj_columns = [col[1] for col in cursor.fetchall()]
print(f"Adjustment columns: {adj_columns}")

if 'performance_before' not in adj_columns:
    cursor.execute("ALTER TABLE adjustment ADD COLUMN performance_before TEXT")
    print("Added performance_before column")
if 'performance_after' not in adj_columns:
    cursor.execute("ALTER TABLE adjustment ADD COLUMN performance_after TEXT")
    print("Added performance_after column")

tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"Tables: {[t[0] for t in tables]}")

if 'env_template' not in [t[0] for t in tables]:
    cursor.execute('''CREATE TABLE env_template (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        type VARCHAR(50) NOT NULL,
        complexity VARCHAR(20) NOT NULL,
        test_type VARCHAR(50) NOT NULL,
        config TEXT NOT NULL,
        created_by INTEGER,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(created_by) REFERENCES user(id)
    )''')
    print("Created env_template table")

if 'optimization_record' not in [t[0] for t in tables]:
    cursor.execute('''CREATE TABLE optimization_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        env_id INTEGER NOT NULL,
        optimizer VARCHAR(50) NOT NULL,
        trigger VARCHAR(50) NOT NULL,
        original_config TEXT,
        optimized_config TEXT,
        scores_before TEXT,
        scores_after TEXT,
        improvement FLOAT,
        custom_goals TEXT,
        created_at DATETIME,
        FOREIGN KEY(env_id) REFERENCES environment(id)
    )''')
    print("Created optimization_record table")

if 'optimization_schedule' not in [t[0] for t in tables]:
    cursor.execute('''CREATE TABLE optimization_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        env_id INTEGER NOT NULL,
        interval VARCHAR(20) NOT NULL DEFAULT 'daily',
        enabled BOOLEAN DEFAULT 1,
        last_run DATETIME,
        next_run DATETIME,
        custom_goals TEXT,
        created_by INTEGER,
        created_at DATETIME,
        FOREIGN KEY(env_id) REFERENCES environment(id),
        FOREIGN KEY(created_by) REFERENCES user(id)
    )''')
    print("Created optimization_schedule table")

conn.commit()
conn.close()
print("Migration completed successfully!")
