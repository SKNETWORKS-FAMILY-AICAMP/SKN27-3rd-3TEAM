import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

PROCESSED_DATA_DIR = "data/data/processed"

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "pokemon_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5433")
    )

def ensure_schema_up_to_date(cursor):
    print("Checking database schema...")
    # 1. Add missing columns to existing tables
    cursor.execute("""
        DO $$ 
        BEGIN 
            -- moves 테이블에 damage_class 추가
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='damage_class') THEN
                ALTER TABLE moves ADD COLUMN damage_class VARCHAR(20);
            END IF;

            -- abilities 테이블에 embedding 추가
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='abilities' AND column_name='embedding') THEN
                ALTER TABLE abilities ADD COLUMN embedding VECTOR(1536);
            END IF;

            -- pokemon 테이블에 image_url 추가
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='pokemon' AND column_name='image_url') THEN
                ALTER TABLE pokemon ADD COLUMN image_url VARCHAR(255);
            END IF;

            -- pokemon 테이블에 cry_url 추가
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='pokemon' AND column_name='cry_url') THEN
                ALTER TABLE pokemon ADD COLUMN cry_url VARCHAR(255);
            END IF;

            -- pokemon 테이블에 is_default 추가
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='pokemon' AND column_name='is_default') THEN
                ALTER TABLE pokemon ADD COLUMN is_default BOOLEAN DEFAULT TRUE;
            END IF;
        END $$;
    """)
    
    # 2. Run schema.sql to create new tables if they don't exist
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            cursor.execute(f.read())
    
    print("Schema is up to date.")

def load_json(filename):
    filepath = os.path.join(PROCESSED_DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_types(cursor):
    data = load_json("types.json")
    for row in data:
        cursor.execute(
            "INSERT INTO types (id, name) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name",
            (row['id'], row['name'])
        )
    print(f"Loaded {len(data)} types.")

def load_type_efficacy(cursor):
    data = load_json("type_efficacy.json")
    for row in data:
        cursor.execute(
            """INSERT INTO type_efficacy (damage_type_id, target_type_id, damage_factor) 
               VALUES (%s, %s, %s) 
               ON CONFLICT (damage_type_id, target_type_id) 
               DO UPDATE SET damage_factor = EXCLUDED.damage_factor""",
            (row['damage_type_id'], row['target_type_id'], row['damage_factor'])
        )
    print(f"Loaded {len(data)} type efficacies.")

def load_pokemon(cursor):
    data = load_json("pokemon.json")
    for row in data:
        cursor.execute(
            """INSERT INTO pokemon (id, name, height, weight, base_exp, image_url, cry_url, is_default) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
               ON CONFLICT (id) DO UPDATE SET 
               name = EXCLUDED.name, height = EXCLUDED.height, weight = EXCLUDED.weight, 
               base_exp = EXCLUDED.base_exp, image_url = EXCLUDED.image_url,
               cry_url = EXCLUDED.cry_url, is_default = EXCLUDED.is_default""",
            (row['id'], row['name'], row['height'], row['weight'], row['base_exp'], 
             row['image_url'], row['cry_url'], row.get('is_default', True))
        )
    print(f"Loaded {len(data)} pokemon.")

def load_pokemon_stats(cursor):
    data = load_json("pokemon_stats.json")
    for row in data:
        cursor.execute(
            """INSERT INTO pokemon_stats (pokemon_id, hp, attack, defense, sp_attack, sp_defense, speed) 
               VALUES (%s, %s, %s, %s, %s, %s, %s) 
               ON CONFLICT (pokemon_id) DO UPDATE SET 
               hp = EXCLUDED.hp, attack = EXCLUDED.attack, defense = EXCLUDED.defense, 
               sp_attack = EXCLUDED.sp_attack, sp_defense = EXCLUDED.sp_defense, speed = EXCLUDED.speed""",
            (row['pokemon_id'], row['hp'], row['attack'], row['defense'], row['sp_attack'], row['sp_defense'], row['speed'])
        )
    print(f"Loaded {len(data)} pokemon stats.")

def load_pokemon_types(cursor):
    data = load_json("pokemon_types.json")
    for row in data:
        cursor.execute(
            """INSERT INTO pokemon_types (pokemon_id, type_id, slot) 
               VALUES (%s, %s, %s) 
               ON CONFLICT (pokemon_id, type_id) DO UPDATE SET slot = EXCLUDED.slot""",
            (row['pokemon_id'], row['type_id'], row['slot'])
        )
    print(f"Loaded {len(data)} pokemon types.")

def load_species(cursor):
    data = load_json("species.json")
    for row in data:
        cursor.execute(
            """INSERT INTO species (id, pokemon_id, generation, capture_rate) 
               VALUES (%s, %s, %s, %s) 
               ON CONFLICT (id) DO UPDATE SET pokemon_id = EXCLUDED.pokemon_id, generation = EXCLUDED.generation, capture_rate = EXCLUDED.capture_rate""",
            (row['id'], row['pokemon_id'], row['generation'], row['capture_rate'])
        )
    print(f"Loaded {len(data)} species.")

def load_flavor_text(cursor):
    # Check if split files exist
    import glob
    split_files = glob.glob(os.path.join(PROCESSED_DATA_DIR, "flavor_text_part*.json"))
    
    if split_files:
        print(f"Loading flavor text from {len(split_files)} split files...")
        data = []
        for filepath in sorted(split_files):
            with open(filepath, 'r', encoding='utf-8') as f:
                data.extend(json.load(f))
    else:
        data = load_json("flavor_text.json")

    for row in data:
        # flavor_text uses SERIAL for ID, so we insert without conflict handling for simplicity
        embedding = row.get('embedding')
        cursor.execute(
            """INSERT INTO flavor_text (species_id, version_name, content, embedding) 
               VALUES (%s, %s, %s, %s)""",
            (row['species_id'], row['version_name'], row['content'], embedding)
        )
    print(f"Loaded {len(data)} flavor texts.")

def load_items(cursor):
    data = load_json("items.json")
    for row in data:
        cursor.execute(
            """INSERT INTO items (id, name, category, effect_text) 
               VALUES (%s, %s, %s, %s) 
               ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, effect_text = EXCLUDED.effect_text""",
            (row['id'], row['name'], row['category'], row['effect_text'])
        )
    print(f"Loaded {len(data)} items.")

def load_abilities(cursor):
    data = load_json("abilities.json")
    for row in data:
        embedding = row.get('embedding')
        cursor.execute(
            """INSERT INTO abilities (id, name, effect_text, embedding) 
               VALUES (%s, %s, %s, %s) 
               ON CONFLICT (id) DO UPDATE SET 
               name = EXCLUDED.name, effect_text = EXCLUDED.effect_text, embedding = EXCLUDED.embedding""",
            (row['id'], row['name'], row['effect_text'], embedding)
        )
    print(f"Loaded {len(data)} abilities.")

def load_pokemon_abilities(cursor):
    data = load_json("pokemon_abilities.json")
    for row in data:
        cursor.execute(
            """INSERT INTO pokemon_abilities (pokemon_id, ability_id, is_hidden, slot) 
               VALUES (%s, %s, %s, %s) 
               ON CONFLICT (pokemon_id, ability_id) DO UPDATE SET is_hidden = EXCLUDED.is_hidden, slot = EXCLUDED.slot""",
            (row['pokemon_id'], row['ability_id'], row['is_hidden'], row['slot'])
        )
    print(f"Loaded {len(data)} pokemon abilities.")

def load_pokemon_moves(cursor):
    data = load_json("pokemon_moves.json")
    for row in data:
        cursor.execute(
            """INSERT INTO pokemon_moves (pokemon_id, move_id, learn_method, level_learned_at) 
               VALUES (%s, %s, %s, %s) 
               ON CONFLICT (pokemon_id, move_id, learn_method, level_learned_at) DO NOTHING""",
            (row['pokemon_id'], row['move_id'], row['learn_method'], row['level_learned_at'])
        )
    print(f"Loaded {len(data)} pokemon moves mappings.")

def load_natures(cursor):
    data = load_json("natures.json")
    for row in data:
        cursor.execute(
            """INSERT INTO natures (id, name, increased_stat, decreased_stat) 
               VALUES (%s, %s, %s, %s) 
               ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, increased_stat = EXCLUDED.increased_stat, decreased_stat = EXCLUDED.decreased_stat""",
            (row['id'], row['name'], row['increased_stat'], row['decreased_stat'])
        )
    print(f"Loaded {len(data)} natures.")

def load_moves(cursor):
    data = load_json("moves.json")
    for row in data:
        embedding = row.get('embedding')
        cursor.execute(
            """INSERT INTO moves (id, name, type_id, power, accuracy, damage_class, effect_text, embedding) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
               ON CONFLICT (id) DO UPDATE SET 
               name = EXCLUDED.name, type_id = EXCLUDED.type_id, power = EXCLUDED.power, 
               accuracy = EXCLUDED.accuracy, damage_class = EXCLUDED.damage_class, 
               effect_text = EXCLUDED.effect_text, embedding = EXCLUDED.embedding""",
            (row['id'], row['name'], row['type_id'], row['power'], row['accuracy'], 
             row['damage_class'], row['effect_text'], embedding)
        )
    print(f"Loaded {len(data)} moves.")

def load_evolutions(cursor):
    data = load_json("evolutions.json")
    loaded_count = 0
    for row in data:
        # Check if item exists if trigger_item_id is provided
        if row['trigger_item_id']:
            cursor.execute("SELECT id FROM items WHERE id = %s", (row['trigger_item_id'],))
            if not cursor.fetchone():
                print(f"Warning: Item {row['trigger_item_id']} not found in DB. Skipping evolution trigger.")
                row['trigger_item_id'] = None # Or skip the record, but setting to None is safer for the chain
        
        cursor.execute(
            """INSERT INTO evolutions (from_species_id, to_species_id, min_level, trigger_item_id) 
               VALUES (%s, %s, %s, %s)""",
            (row['from_species_id'], row['to_species_id'], row['min_level'], row['trigger_item_id'])
        )
        loaded_count += 1
    print(f"Loaded {loaded_count} evolutions.")

def load_pokemon_knowledge(cursor):
    data = load_json("pokemon_knowledge.json")
    for row in data:
        embedding = row.get('embedding')
        cursor.execute(
            """INSERT INTO pokemon_knowledge (pokemon_id, content, embedding) 
               VALUES (%s, %s, %s) 
               ON CONFLICT (pokemon_id) DO UPDATE SET 
               content = EXCLUDED.content, embedding = EXCLUDED.embedding""",
            (row['pokemon_id'], row['content'], embedding)
        )
    print(f"Loaded {len(data)} pokemon knowledge profiles.")

if __name__ == "__main__":
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("Synchronizing Database Schema...")
        ensure_schema_up_to_date(cursor)
        
        print("Loading additional data into Database...")
        load_types(cursor)
        load_type_efficacy(cursor)
        load_pokemon(cursor)
        load_pokemon_stats(cursor)
        load_pokemon_types(cursor)
        load_species(cursor)
        
        cursor.execute("TRUNCATE TABLE flavor_text RESTART IDENTITY;")
        load_flavor_text(cursor)

        load_items(cursor)
        load_moves(cursor)
        load_abilities(cursor)
        load_pokemon_abilities(cursor)
        load_pokemon_moves(cursor)
        load_natures(cursor)
        load_pokemon_knowledge(cursor)
        cursor.execute("TRUNCATE TABLE evolutions RESTART IDENTITY;")
        load_evolutions(cursor)

        conn.commit()
        cursor.close()
        conn.close()
        print("DB Load Complete!")
        
    except Exception as e:
        print(f"Database error: {e}")
