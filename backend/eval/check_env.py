import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '.env'))

DB = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/pokemon_db").replace("postgres://", "postgresql://", 1)

import psycopg2
conn = psycopg2.connect(DB)
cur = conn.cursor()

cur.execute("SELECT extname FROM pg_extension ORDER BY extname")
print("Extensions:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT extname FROM pg_extension WHERE extname='pg_trgm'")
trgm = cur.fetchall()
print("pg_trgm available:", bool(trgm))
conn.close()

try:
    from sentence_transformers import CrossEncoder
    print("sentence_transformers: available")
except ImportError:
    print("sentence_transformers: NOT installed")

try:
    from rank_bm25 import BM25Okapi
    print("rank_bm25: available")
except ImportError:
    print("rank_bm25: NOT installed")
