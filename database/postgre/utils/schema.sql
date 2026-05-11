-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ==========================================
-- 1. 핵심 정형 데이터 (Core Pokemon Data)
-- ==========================================

CREATE TABLE IF NOT EXISTS pokemon (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    height INTEGER,
    weight INTEGER,
    base_exp INTEGER,
    image_url VARCHAR(255),
    cry_url VARCHAR(255),
    is_default BOOLEAN DEFAULT TRUE,
    species_id INTEGER
);

CREATE TABLE IF NOT EXISTS pokemon_stats (
    pokemon_id INTEGER REFERENCES pokemon(id) ON DELETE CASCADE,
    hp INTEGER NOT NULL,
    attack INTEGER NOT NULL,
    defense INTEGER NOT NULL,
    sp_attack INTEGER NOT NULL,
    sp_defense INTEGER NOT NULL,
    speed INTEGER NOT NULL,
    PRIMARY KEY (pokemon_id)
);

-- ==========================================
-- 2. 속성 및 상성 시스템 (Types & Mechanics)
-- ==========================================

CREATE TABLE IF NOT EXISTS types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS pokemon_types (
    pokemon_id INTEGER REFERENCES pokemon(id) ON DELETE CASCADE,
    type_id INTEGER REFERENCES types(id) ON DELETE CASCADE,
    slot INTEGER NOT NULL,
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE IF NOT EXISTS type_efficacy (
    damage_type_id INTEGER REFERENCES types(id) ON DELETE CASCADE,
    target_type_id INTEGER REFERENCES types(id) ON DELETE CASCADE,
    damage_factor FLOAT NOT NULL, -- 0.0, 0.5, 1.0, 2.0
    PRIMARY KEY (damage_type_id, target_type_id)
);

-- ==========================================
-- 2.5 특성 시스템 (Abilities)
-- ==========================================

CREATE TABLE IF NOT EXISTS abilities (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    effect_text TEXT,
    embedding VECTOR(1536)
);

CREATE TABLE IF NOT EXISTS pokemon_abilities (
    pokemon_id INTEGER REFERENCES pokemon(id) ON DELETE CASCADE,
    ability_id INTEGER REFERENCES abilities(id) ON DELETE CASCADE,
    is_hidden BOOLEAN NOT NULL,
    slot INTEGER NOT NULL,
    PRIMARY KEY (pokemon_id, ability_id)
);

-- ==========================================
-- 3. RAG 핵심 지식 베이스 (Species & Unstructured Data)
-- ==========================================

CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY,
    pokemon_id INTEGER REFERENCES pokemon(id) ON DELETE CASCADE,
    generation INTEGER,
    capture_rate INTEGER
);

CREATE TABLE IF NOT EXISTS flavor_text (
    id SERIAL PRIMARY KEY,
    species_id INTEGER REFERENCES species(id) ON DELETE CASCADE,
    version_name VARCHAR(50),
    content TEXT NOT NULL,
    embedding VECTOR(1536) -- Placeholder dimension, OpenAI text-embedding-3-small
);

-- ==========================================
-- 3.5 성격 시스템 (Natures)
-- ==========================================

CREATE TABLE IF NOT EXISTS natures (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    increased_stat VARCHAR(50),
    decreased_stat VARCHAR(50)
);

-- ==========================================
-- 5. 전투 및 도구 (Moves & Items)
-- ==========================================

CREATE TABLE IF NOT EXISTS moves (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type_id INTEGER REFERENCES types(id) ON DELETE SET NULL,
    power INTEGER,
    accuracy INTEGER,
    damage_class VARCHAR(20), -- physical, special, status
    effect_text TEXT,
    embedding VECTOR(1536) -- Optional for vector search
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    effect_text TEXT
);

-- ==========================================
-- 4. 진화 파이프라인 (Evolution)
-- ==========================================

CREATE TABLE IF NOT EXISTS evolutions (
    id SERIAL PRIMARY KEY,
    from_species_id INTEGER REFERENCES species(id) ON DELETE CASCADE,
    to_species_id INTEGER REFERENCES species(id) ON DELETE CASCADE,
    min_level INTEGER,
    trigger_item_id INTEGER REFERENCES items(id) ON DELETE SET NULL
);

-- ==========================================
-- 6. 통합 지식 베이스 (Consolidated Knowledge)
-- ==========================================

CREATE TABLE IF NOT EXISTS pokemon_knowledge (
    pokemon_id INTEGER PRIMARY KEY REFERENCES pokemon(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536)
);

-- ==========================================
-- 7. 기술 습득 매핑 (Pokemon-Moves)
-- ==========================================

CREATE TABLE IF NOT EXISTS pokemon_moves (
    pokemon_id INTEGER REFERENCES pokemon(id) ON DELETE CASCADE,
    move_id INTEGER REFERENCES moves(id) ON DELETE CASCADE,
    learn_method VARCHAR(50), -- level-up, machine, egg, tutor
    level_learned_at INTEGER,
    PRIMARY KEY (pokemon_id, move_id, learn_method, level_learned_at)
);
