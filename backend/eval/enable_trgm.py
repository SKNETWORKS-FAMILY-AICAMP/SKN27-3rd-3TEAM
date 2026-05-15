import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

db = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/pokemon_db")
if db.startswith("postgres://"):
    db = db.replace("postgres://", "postgresql://", 1)

import psycopg2
conn = psycopg2.connect(db)
conn.autocommit = True
cur = conn.cursor()
try:
    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    print("pg_trgm extension created/already exists")
    cur.execute("SELECT extname FROM pg_extension WHERE extname='pg_trgm'")
    print("Confirmed:", cur.fetchall())
except Exception as e:
    print("Failed:", e)
conn.close()
