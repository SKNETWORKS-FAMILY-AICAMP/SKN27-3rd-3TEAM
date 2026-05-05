# database.py
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

USER     = os.getenv("POSTGRES_USER")
PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB       = os.getenv("POSTGRES_DB")
HOST     = os.getenv("POSTGRES_HOST", "localhost")
PORT     = os.getenv("POSTGRES_PORT", "5433")

engine = create_engine(
    f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"
)

def execute_query(sql: str) -> list:
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(row._mapping) for row in result]

def get_schema() -> str:
    sql = """
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position
    """
    rows = execute_query(sql)

    schema_dict = {}
    for row in rows:
        table  = row["table_name"]
        column = row["column_name"]
        dtype  = row["data_type"]
        if table not in schema_dict:
            schema_dict[table] = []
        schema_dict[table].append(f"{column} ({dtype})")

    schema_str = ""
    for table, columns in schema_dict.items():
        schema_str += f"\n테이블: {table}\n"
        schema_str += "\n".join(f"  - {col}" for col in columns)
        schema_str += "\n"

    return schema_str