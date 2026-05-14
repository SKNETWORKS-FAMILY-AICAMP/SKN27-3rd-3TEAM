import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

db = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/pokemon_db")
if db.startswith("postgres://"):
    db = db.replace("postgres://", "postgresql://", 1)

import psycopg2
conn = psycopg2.connect(db)
cur = conn.cursor()

cur.execute("SELECT extname FROM pg_extension ORDER BY extname")
exts = [r[0] for r in cur.fetchall()]
print("Extensions:", exts)
print("pg_trgm:", "pg_trgm" in exts)

# Check Neo4j evolution conditions
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    os.environ.get("GRAPH_DB_URI", "bolt://localhost:7687"),
    auth=(os.environ.get("GRAPH_DB_USER", "neo4j"), os.environ.get("GRAPH_DB_PASSWORD", "test1234"))
)
with driver.session() as s:
    r = s.run("MATCH (a:Pokemon)-[e:EVOLVES_TO]->(b:Pokemon) WHERE a.name CONTAINS '이브이' RETURN a.name, b.name, e.min_level, e.trigger_item_id, e.trigger_condition LIMIT 20")
    print("\n이브이 진화 관계:")
    for row in r.data():
        print(row)

    # Check what properties EVOLVES_TO has
    r2 = s.run("MATCH ()-[e:EVOLVES_TO]->() RETURN keys(e) LIMIT 1")
    print("\nEVOLVES_TO keys:", r2.data())

driver.close()
conn.close()
