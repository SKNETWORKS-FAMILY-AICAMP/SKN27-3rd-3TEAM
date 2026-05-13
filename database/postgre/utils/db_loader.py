import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

PROCESSED_DATA_DIR = "database/common/data/processed"

def get_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "pokemon_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5433")
    )

def ensure_schema_up_to_date(cursor):
    print("Checking database schema...")
    # 1. 기존 테이블에 누락 컬럼 추가
    cursor.execute("""
        DO $$ 
        BEGIN 
            -- moves 테이블에 damage_class 추가
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='damage_class') THEN
                ALTER TABLE moves ADD COLUMN damage_class VARCHAR(20);
            END IF;

            -- moves 테이블에 나머지 컬럼들 추가 (존재하지 않을 경우)
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='ailment') THEN
                ALTER TABLE moves ADD COLUMN ailment VARCHAR(10);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='ailment_chance') THEN
                ALTER TABLE moves ADD COLUMN ailment_chance INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='category') THEN
                ALTER TABLE moves ADD COLUMN category VARCHAR(20);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='crit_rate') THEN
                ALTER TABLE moves ADD COLUMN crit_rate INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='drain') THEN
                ALTER TABLE moves ADD COLUMN drain INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='flinch_chance') THEN
                ALTER TABLE moves ADD COLUMN flinch_chance INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='healing') THEN
                ALTER TABLE moves ADD COLUMN healing INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='max_hits') THEN
                ALTER TABLE moves ADD COLUMN max_hits INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='max_turns') THEN
                ALTER TABLE moves ADD COLUMN max_turns INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='min_hits') THEN
                ALTER TABLE moves ADD COLUMN min_hits INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='min_turns') THEN
                ALTER TABLE moves ADD COLUMN min_turns INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='stat_chance') THEN
                ALTER TABLE moves ADD COLUMN stat_chance INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='stat_changes') THEN
                ALTER TABLE moves ADD COLUMN stat_changes VARCHAR(100);
            ELSE
                -- 이미 존재한다면 길이 확장
                ALTER TABLE moves ALTER COLUMN stat_changes TYPE VARCHAR(100);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='target') THEN
                ALTER TABLE moves ADD COLUMN target VARCHAR(20);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='moves' AND column_name='fixed_damage') THEN
                ALTER TABLE moves ADD COLUMN fixed_damage VARCHAR(30);
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

            -- pokemon 테이블에 species_id 추가
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='pokemon' AND column_name='species_id') THEN
                ALTER TABLE pokemon ADD COLUMN species_id INTEGER;
            END IF;

            -- species 테이블에 classification 추가
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='species' AND column_name='classification') THEN
                ALTER TABLE species ADD COLUMN classification VARCHAR(50);
            END IF;

            -- species 테이블에 gender_rate 추가
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='species' AND column_name='gender_rate') THEN
                ALTER TABLE species ADD COLUMN gender_rate INTEGER;
            END IF;

            -- users 테이블 마이그레이션
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN
                -- github_id BIGINT 변환
                ALTER TABLE users ALTER COLUMN github_id TYPE BIGINT;

                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='users' AND column_name='public_repos') THEN
                    ALTER TABLE users ADD COLUMN public_repos INTEGER DEFAULT 0;
                END IF;

                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='users' AND column_name='total_commits') THEN
                    ALTER TABLE users ADD COLUMN total_commits INTEGER DEFAULT 0;
                END IF;

                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='users' AND column_name='total_stars') THEN
                    ALTER TABLE users ADD COLUMN total_stars INTEGER DEFAULT 0;
                END IF;
            END IF;
        END $$;
    """)
    
    # 2. schema.sql 실행으로 신규 테이블 생성
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            full_sql = f.read()
            # 세미콜론 단위로 쪼개서 하나씩 실행 (하나가 실패해도 나머지는 시도하도록)
            statements = full_sql.split(';')
            for statement in statements:
                if statement.strip():
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        # 이미 존재하는 등의 사소한 에러는 무시
                        pass
    
    print("Schema synchronization complete.")

def load_json(filename):
    filepath = os.path.join(PROCESSED_DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_types(cursor):
    data = load_json("types.json")
    if not data: return
    values = [(row['id'], row['name']) for row in data]
    execute_values(cursor, 
        "INSERT INTO types (id, name) VALUES %s ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name",
        values
    )
    print(f"Loaded {len(data)} types.")

def load_type_efficacy(cursor):
    data = load_json("type_efficacy.json")
    if not data: return
    values = [(row['damage_type_id'], row['target_type_id'], row['damage_factor']) for row in data]
    execute_values(cursor, 
        "INSERT INTO type_efficacy (damage_type_id, target_type_id, damage_factor) VALUES %s ON CONFLICT (damage_type_id, target_type_id) DO UPDATE SET damage_factor = EXCLUDED.damage_factor",
        values
    )
    print(f"Loaded {len(data)} type efficacies.")

def load_pokemon(cursor):
    data = load_json("pokemon.json")
    if not data: return
    values = [(row['id'], row['name'], row['height'], row['weight'], row['base_exp'], 
              row['image_url'], row['cry_url'], row.get('is_default', True), row.get('species_id')) for row in data]
    execute_values(cursor, 
        """INSERT INTO pokemon (id, name, height, weight, base_exp, image_url, cry_url, is_default, species_id) 
           VALUES %s ON CONFLICT (id) DO UPDATE SET 
           name = EXCLUDED.name, height = EXCLUDED.height, weight = EXCLUDED.weight, 
           base_exp = EXCLUDED.base_exp, image_url = EXCLUDED.image_url,
           cry_url = EXCLUDED.cry_url, is_default = EXCLUDED.is_default,
           species_id = EXCLUDED.species_id""",
        values
    )
    print(f"Loaded {len(data)} pokemon.")

def load_pokemon_stats(cursor):
    data = load_json("pokemon_stats.json")
    if not data: return
    values = [(row['pokemon_id'], row['hp'], row['attack'], row['defense'], row['sp_attack'], row['sp_defense'], row['speed']) for row in data]
    execute_values(cursor, 
        """INSERT INTO pokemon_stats (pokemon_id, hp, attack, defense, sp_attack, sp_defense, speed) 
           VALUES %s ON CONFLICT (pokemon_id) DO UPDATE SET 
           hp = EXCLUDED.hp, attack = EXCLUDED.attack, defense = EXCLUDED.defense, 
           sp_attack = EXCLUDED.sp_attack, sp_defense = EXCLUDED.sp_defense, speed = EXCLUDED.speed""",
        values
    )
    print(f"Loaded {len(data)} pokemon stats.")

def load_pokemon_types(cursor):
    data = load_json("pokemon_types.json")
    if not data: return
    values = [(row['pokemon_id'], row['type_id'], row['slot']) for row in data]
    execute_values(cursor, 
        "INSERT INTO pokemon_types (pokemon_id, type_id, slot) VALUES %s ON CONFLICT (pokemon_id, type_id) DO UPDATE SET slot = EXCLUDED.slot",
        values
    )
    print(f"Loaded {len(data)} pokemon types.")

def load_species(cursor):
    data = load_json("species.json")
    if not data: return
    values = [(row['id'], row['pokemon_id'], row['generation'], row['capture_rate'], row.get('classification'), row.get('gender_rate')) for row in data]
    execute_values(cursor, 
        """INSERT INTO species (id, pokemon_id, generation, capture_rate, classification, gender_rate) 
           VALUES %s ON CONFLICT (id) DO UPDATE SET 
           pokemon_id = EXCLUDED.pokemon_id, generation = EXCLUDED.generation, 
           capture_rate = EXCLUDED.capture_rate, classification = EXCLUDED.classification, gender_rate = EXCLUDED.gender_rate""",
        values
    )
    print(f"Loaded {len(data)} species.")

def load_flavor_text(cursor):
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

    if not data: return
    values = [(row['species_id'], row['version_name'], row['content'], row.get('embedding')) for row in data]
    execute_values(cursor, 
        "INSERT INTO flavor_text (species_id, version_name, content, embedding) VALUES %s",
        values
    )
    print(f"Loaded {len(data)} flavor texts.")

def load_items(cursor):
    data = load_json("items.json")
    if not data: return
    values = [(row['id'], row['name'], row['category'], row['effect_text']) for row in data]
    execute_values(cursor, 
        "INSERT INTO items (id, name, category, effect_text) VALUES %s ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, effect_text = EXCLUDED.effect_text",
        values
    )
    print(f"Loaded {len(data)} items.")

def load_abilities(cursor):
    data = load_json("abilities.json")
    if not data: return
    values = [(row['id'], row['name'], row['effect_text'], row.get('embedding')) for row in data]
    execute_values(cursor, 
        "INSERT INTO abilities (id, name, effect_text, embedding) VALUES %s ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, effect_text = EXCLUDED.effect_text, embedding = EXCLUDED.embedding",
        values
    )
    print(f"Loaded {len(data)} abilities.")

def load_pokemon_abilities(cursor):
    data = load_json("pokemon_abilities.json")
    if not data: return
    
    # Batch existence check for ability_id to replace row-by-row SELECT
    cursor.execute("SELECT id FROM abilities")
    existing_abilities = {r[0] for r in cursor.fetchall()}
    
    valid_data = [row for row in data if row['ability_id'] in existing_abilities]
    skipped_count = len(data) - len(valid_data)
    
    if valid_data:
        values = [(row['pokemon_id'], row['ability_id'], row['is_hidden'], row['slot']) for row in valid_data]
        execute_values(cursor, 
            "INSERT INTO pokemon_abilities (pokemon_id, ability_id, is_hidden, slot) VALUES %s ON CONFLICT (pokemon_id, ability_id) DO UPDATE SET is_hidden = EXCLUDED.is_hidden, slot = EXCLUDED.slot",
            values
        )
    
    if skipped_count:
        print(f"경고: ability_id가 없는 레코드 {skipped_count}개 건너뜀")
    print(f"Loaded {len(valid_data)} pokemon abilities.")

def load_pokemon_moves(cursor):
    data = load_json("pokemon_moves.json")
    if not data: return
    values = [(row['pokemon_id'], row['move_id'], row['learn_method'], row['level_learned_at']) for row in data]
    execute_values(cursor, 
        "INSERT INTO pokemon_moves (pokemon_id, move_id, learn_method, level_learned_at) VALUES %s ON CONFLICT (pokemon_id, move_id, learn_method, level_learned_at) DO NOTHING",
        values
    )
    print(f"Loaded {len(data)} pokemon moves mappings.")

def load_natures(cursor):
    data = load_json("natures.json")
    if not data: return
    values = [(row['id'], row['name'], row['increased_stat'], row['decreased_stat']) for row in data]
    execute_values(cursor, 
        "INSERT INTO natures (id, name, increased_stat, decreased_stat) VALUES %s ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, increased_stat = EXCLUDED.increased_stat, decreased_stat = EXCLUDED.decreased_stat",
        values
    )
    print(f"Loaded {len(data)} natures.")

def load_moves(cursor):
    data = load_json("moves.json")
    for row in data:
        embedding = row.get('embedding')
        cursor.execute(
            """INSERT INTO moves (
                   id, name, type_id, power, accuracy, damage_class, 
                   ailment, ailment_chance, category, crit_rate, 
                   drain, flinch_chance, healing, max_hits, max_turns, 
                   min_hits, min_turns, stat_chance, stat_changes, 
                   target, fixed_damage, effect_text, embedding
               ) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
               ON CONFLICT (id) DO UPDATE SET 
               name = EXCLUDED.name, type_id = EXCLUDED.type_id, power = EXCLUDED.power, 
               accuracy = EXCLUDED.accuracy, damage_class = EXCLUDED.damage_class,
               ailment = EXCLUDED.ailment, ailment_chance = EXCLUDED.ailment_chance,
               category = EXCLUDED.category, crit_rate = EXCLUDED.crit_rate,
               drain = EXCLUDED.drain, flinch_chance = EXCLUDED.flinch_chance,
               healing = EXCLUDED.healing, max_hits = EXCLUDED.max_hits,
               max_turns = EXCLUDED.max_turns, min_hits = EXCLUDED.min_hits,
               min_turns = EXCLUDED.min_turns, stat_chance = EXCLUDED.stat_chance,
               stat_changes = EXCLUDED.stat_changes, target = EXCLUDED.target,
               fixed_damage = EXCLUDED.fixed_damage,
               effect_text = EXCLUDED.effect_text, embedding = EXCLUDED.embedding
            """,
            (row['id'], row['name'], row['type_id'], row['power'], row['accuracy'], 
             row['damage_class'], row['ailment'], row['ailment_chance'], row['category'],
             row['crit_rate'], row['drain'], row['flinch_chance'], row['healing'],
             row['max_hits'], row['max_turns'], row['min_hits'], row['min_turns'],
             row['stat_chance'], json.dumps(row['stat_changes']), row['target'], row.get('fixed_damage'),
             row['effect_text'], embedding)
        )
    print(f"Loaded {len(data)} moves.")

def load_evolutions(cursor):
    data = load_json("evolutions.json")
    if not data: return
    
    # Batch item check
    cursor.execute("SELECT id FROM items")
    existing_items = {r[0] for r in cursor.fetchall()}
    
    values = []
    for row in data:
        trigger_item = row['trigger_item_id']
        if trigger_item and trigger_item not in existing_items:
            trigger_item = None
        values.append((row['from_species_id'], row['to_species_id'], row['min_level'], trigger_item))
        
    execute_values(cursor, 
        "INSERT INTO evolutions (from_species_id, to_species_id, min_level, trigger_item_id) VALUES %s",
        values
    )
    print(f"Loaded {len(data)} evolutions.")

def load_pokemon_knowledge(cursor):
    data = load_json("pokemon_knowledge.json")
    if not data: return
    values = [(row['pokemon_id'], row['content'], row.get('embedding')) for row in data]
    execute_values(cursor, 
        "INSERT INTO pokemon_knowledge (pokemon_id, content, embedding) VALUES %s ON CONFLICT (pokemon_id) DO UPDATE SET content = EXCLUDED.content, embedding = EXCLUDED.embedding",
        values
    )
    print(f"Loaded {len(data)} pokemon knowledge profiles.")

if __name__ == "__main__":
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("Synchronizing Database Schema...")
        ensure_schema_up_to_date(cursor)
        
        print("Loading additional data into Database...")
        # 제약 조건을 잠시 꺼서 순환 참조 문제를 해결합니다.
        cursor.execute("SET session_replication_role = 'replica';")
        
        load_types(cursor)
        load_type_efficacy(cursor)
        load_species(cursor)  # species를 먼저 로드
        load_pokemon(cursor)
        load_pokemon_stats(cursor)
        load_pokemon_types(cursor)
        
        cursor.execute("SET session_replication_role = 'origin';")
        
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

