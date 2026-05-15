import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# .env 로드
load_dotenv()

def check_neo4j_counts():
    uri = os.getenv("GRAPH_DB_URI") or os.getenv("NEO4J_URI")
    user = os.getenv("GRAPH_DB_USER") or os.getenv("NEO4J_USER")
    password = os.getenv("GRAPH_DB_PASSWORD") or os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        print("❌ 에러: .env 파일에 NEO4J 설정이 누락되었습니다.")
        return

    print(f"🔍 Neo4j 접속 시도 중: {uri}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            # 라벨별 노드 개수 쿼리
            result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count")
            
            print("\n📊 --- Neo4j 데이터 적재 현황 ---")
            found = False
            for record in result:
                label = record["label"] or "No Label"
                count = record["count"]
                print(f"✅ {label}: {count}개")
                found = True
            
            if not found:
                print("📭 데이터가 하나도 없습니다. graph_loader.py를 먼저 실행해 주세요.")
        
        driver.close()
    except Exception as e:
        print(f"❌ 접속 실패: {e}")

if __name__ == "__main__":
    check_neo4j_counts()
