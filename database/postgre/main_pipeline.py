import subprocess
import sys
import os
import json
import glob
import psycopg2
from dotenv import load_dotenv

load_dotenv()

RAW_DATA_DIR = "database/common/data/raw"
PROCESSED_DATA_DIR = "database/common/data/processed"


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "pokemon_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5433")
    )


def cleanup():
    print("\n🧹 Cleaning up stale data...")

    # 1. 삭제 대상 raw 파일 식별: totem 또는 이미지 없는 포켓몬
    remove_ids = []
    for f in sorted(glob.glob(os.path.join(RAW_DATA_DIR, "pokemon_1*.json"))):
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
            name = data.get('name', '')
            sprites = data.get('sprites', {})
            image_url = (sprites.get('other', {})
                                .get('official-artwork', {})
                                .get('front_default'))
            fallback = sprites.get('front_default')
            if 'totem' in name.split('-') or (not image_url and not fallback):
                remove_ids.append(data['id'])
                os.remove(f)
                print(f"  [raw 삭제] {name} (id={data['id']})")
        except Exception as e:
            print(f"  [raw 읽기 실패] {f}: {e}")

    # 2. 처리된 JSON 전체 삭제 (pipeline이 새로 생성)
    for f in glob.glob(os.path.join(PROCESSED_DATA_DIR, "*.json")):
        os.remove(f)
        print(f"  [processed 삭제] {os.path.basename(f)}")

    # 3. DB에서 해당 포켓몬 레코드 삭제
    if remove_ids:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            id_list = list(remove_ids)
            # 의존 테이블 먼저 삭제 (FK 순서)
            for table in ["pokemon_knowledge", "pokemon_moves",
                          "pokemon_abilities", "pokemon_types", "pokemon_stats"]:
                cur.execute(f"DELETE FROM {table} WHERE pokemon_id = ANY(%s)", (id_list,))
            cur.execute("DELETE FROM pokemon WHERE id = ANY(%s)", (id_list,))
            conn.commit()
            cur.close()
            conn.close()
            print(f"  [DB 삭제] {len(remove_ids)}개 포켓몬 레코드 삭제 완료")
        except Exception as e:
            print(f"  [DB 삭제 스킵] DB 미연결 상태이거나 테이블 없음: {e}")

    print("✅ Cleanup complete.\n")


def run_script(script_path):
    print(f"\n--- Running {script_path} ---")
    try:
        result = subprocess.run([sys.executable, script_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {e}")
        return False


def main():
    print("Starting Pokemon Data Pipeline Update...")

    # cleanup()

    scripts = [
        # "database/common/processing/api_collector.py",
        "database/common/processing/data_processor.py",
        "database/postgre/utils/db_loader.py",
        # "database/postgre/utils/vectorizer.py"
    ]

    for script in scripts:
        if not run_script(script):
            print(f"Pipeline failed at {script}. Aborting.")
            return

    print("\n✅ Pokemon Data Pipeline Update Complete!")


if __name__ == "__main__":
    main()
