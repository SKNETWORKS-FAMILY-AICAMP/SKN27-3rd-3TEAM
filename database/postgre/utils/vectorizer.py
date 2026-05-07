import os
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
import json

load_dotenv()

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "pokemon_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5433")
    )

def get_embedding(text):
    """Generate embedding for a given text using OpenAI."""
    if not text or text.strip() == "":
        return None
    # Clean text: remove newlines which can sometimes affect embedding quality
    text = text.replace("\n", " ")
    try:
        response = client.embeddings.create(input=[text], model="text-embedding-3-small")
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def vectorize_table(cursor, table_name, text_column, id_column="id"):
    """Vectorize a specific table's text column if embedding is NULL."""
    print(f"Vectorizing {table_name}...")
    
    # Fetch only rows that don't have an embedding yet
    cursor.execute(f"SELECT {id_column}, {text_column} FROM {table_name} WHERE embedding IS NULL")
    rows = cursor.fetchall()
    
    if not rows:
        print(f"All rows in {table_name} are already vectorized.")
        return

    for row_id, text in tqdm(rows, desc=f"Processing {table_name}"):
        embedding = get_embedding(text)
        if embedding:
            cursor.execute(
                f"UPDATE {table_name} SET embedding = %s WHERE {id_column} = %s",
                (embedding, row_id)
            )

def update_processed_json(table_name, id_column="id"):
    """Fetch embeddings from DB and update the corresponding processed JSON file."""
    print(f"Syncing {table_name} embeddings back to JSON...")
    PROCESSED_DATA_DIR = "database/common/data/processed"
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Fetch all columns to recreate JSON if it doesn't exist
        cursor.execute(f"SELECT * FROM {table_name} WHERE embedding IS NOT NULL")
        
        colnames = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        if not rows:
            return

        # Create a mapping of all data from DB
        db_data = []
        for row in rows:
            item = dict(zip(colnames, row))
            # Convert embedding (which might be a string from pgvector) to list
            if isinstance(item['embedding'], str):
                item['embedding'] = [float(x) for x in item['embedding'].strip('[]').split(',')]
            db_data.append(item)

        filename = f"{table_name}.json"
        filepath = os.path.join(PROCESSED_DATA_DIR, filename)
        
        # Special handling for large flavor_text file
        if table_name == "flavor_text":
            import glob
            split_files = glob.glob(os.path.join(PROCESSED_DATA_DIR, "flavor_text_part*.json"))
            if split_files:
                print(f"Updating split files for {table_name}...")
                # For simplicity, we recreate the split from db_data
                mid = len(db_data) // 2
                with open(os.path.join(PROCESSED_DATA_DIR, "flavor_text_part1.json"), 'w', encoding='utf-8') as f:
                    json.dump(db_data[:mid], f, indent=2, ensure_ascii=False)
                with open(os.path.join(PROCESSED_DATA_DIR, "flavor_text_part2.json"), 'w', encoding='utf-8') as f:
                    json.dump(db_data[mid:], f, indent=2, ensure_ascii=False)
                print(f"Updated split files for {table_name}.")
                return

        # Default single file logic
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            embedding_map = {item[id_column]: item['embedding'] for item in db_data}
            
            updated = False
            for item in json_data:
                item_id = item.get(id_column)
                if item_id in embedding_map:
                    item['embedding'] = embedding_map[item_id]
                    updated = True
            
            if updated:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                print(f"Updated {filename} with embeddings.")
        else:
            # If file doesn't exist (like for pokemon_knowledge), create it from DB data
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(db_data, f, indent=2, ensure_ascii=False)
            print(f"Created {filename} from DB data.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error syncing {table_name} to JSON: {e}")

def generate_pokemon_knowledge(cursor):
    """Generate and vectorize consolidated Pokemon knowledge profiles."""
    print("Generating consolidated pokemon_knowledge...")
    
    # Find pokemon that don't have a knowledge entry yet
    cursor.execute("""
        SELECT p.id, p.name, 
               string_agg(DISTINCT t.name, ', ') as types,
               ps.hp, ps.attack, ps.defense, ps.sp_attack, ps.sp_defense, ps.speed,
               string_agg(DISTINCT a.name, ', ') as abilities,
               (SELECT content FROM flavor_text WHERE species_id = s.id LIMIT 1) as description
        FROM pokemon p
        JOIN pokemon_stats ps ON p.id = ps.pokemon_id
        JOIN pokemon_types pt ON p.id = pt.pokemon_id
        JOIN types t ON pt.type_id = t.id
        JOIN species s ON p.id = s.pokemon_id
        JOIN pokemon_abilities pa ON p.id = pa.pokemon_id
        JOIN abilities a ON pa.ability_id = a.id
        LEFT JOIN pokemon_knowledge pk ON p.id = pk.pokemon_id
        WHERE pk.pokemon_id IS NULL
        GROUP BY p.id, ps.hp, ps.attack, ps.defense, ps.sp_attack, ps.sp_defense, ps.speed, s.id
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("All pokemon knowledge profiles are up to date.")
        return

    for row in tqdm(rows, desc="Generating Knowledge Profiles"):
        p_id, name, types, hp, atk, df, spa, spd, spe, abilities, desc = row
        
        # Create a rich summary text
        content = (
            f"이름: {name}\n"
            f"타입: {types}\n"
            f"능력치: HP {hp}, 공격 {atk}, 방어 {df}, 특수공격 {spa}, 특수방어 {spd}, 스피드 {spe}\n"
            f"특성: {abilities}\n"
            f"설명: {desc if desc else '설명 없음'}"
        )
        
        embedding = get_embedding(content)
        
        if embedding:
            cursor.execute(
                "INSERT INTO pokemon_knowledge (pokemon_id, content, embedding) VALUES (%s, %s, %s)",
                (p_id, content, embedding)
            )

if __name__ == "__main__":
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Vectorize Moves
        vectorize_table(cursor, "moves", "effect_text")
        
        # 2. Vectorize Abilities
        vectorize_table(cursor, "abilities", "effect_text")
        
        # 3. Vectorize Flavor Texts (Historical descriptions)
        vectorize_table(cursor, "flavor_text", "content")
        
        # 4. Generate and Vectorize Consolidated Knowledge Profiles
        generate_pokemon_knowledge(cursor)
        
        conn.commit()
        print("Vectorization successfully completed!")

        # 5. Sync results back to JSON files for portability
        update_processed_json("moves")
        update_processed_json("abilities")
        update_processed_json("flavor_text")
        update_processed_json("pokemon_knowledge", id_column="pokemon_id")
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error during vectorization: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
