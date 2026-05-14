"""
Neo4j backend client

목적:
    FastAPI 백엔드에서 Neo4j Graph DB에 접속하고 Cypher 쿼리를 실행합니다.

큰 흐름:
    1. .env 또는 Docker 환경변수에서 Neo4j 접속 정보 읽기
    2. Neo4j driver 생성
    3. 쿼리 실행 함수 제공
    4. FastAPI dependency로 사용할 get_neo4j() 제공
"""

import os
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase


class Neo4jClient:
    """Neo4j 연결과 Cypher 실행을 담당하는 백엔드용 클래스입니다."""

    def __init__(self, uri: str, user: str, password: str):
        """
        Neo4j driver를 생성합니다.

        Args:
            uri: Neo4j Bolt 주소입니다. 로컬 실행 예: bolt://localhost:7687
            user: Neo4j 사용자명입니다. 기본값은 보통 neo4j입니다.
            password: Neo4j 비밀번호입니다.
        """
        self.uri = uri
        self.user = user
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        """애플리케이션 종료 시 Neo4j driver 연결을 닫습니다."""
        self.driver.close()

    def verify_connection(self) -> bool:
        """
        Neo4j 연결이 가능한지 확인합니다.

        Returns:
            연결에 성공하면 True를 반환합니다.
        """
        self.driver.verify_connectivity()
        return True

    def run_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Cypher 쿼리를 실행하고 결과를 dict 리스트로 반환합니다.

        Args:
            query: 실행할 Cypher 쿼리 문자열입니다.
            parameters: 쿼리에 전달할 파라미터 딕셔너리입니다.

        Returns:
            각 row를 dict로 변환한 리스트입니다.
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def run_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        생성/수정용 Cypher 쿼리를 실행합니다.

        지금 백엔드는 주로 조회에 쓰지만,
        나중에 Team/TeamMember 저장 기능을 만들 때 사용할 수 있습니다.
        """
        with self.driver.session() as session:
            session.run(query, parameters or {}).consume()


def create_neo4j_client_from_env() -> Neo4jClient:
    """
    환경변수에서 Neo4j 접속 정보를 읽어 Neo4jClient를 생성합니다.

    필요한 환경변수:
        NEO4J_URI
        NEO4J_USER
        NEO4J_PASSWORD

    주의:
        백엔드가 Docker 컨테이너 안에서 실행되면 NEO4J_URI는 보통 bolt://neo4j:7687 입니다.
        로컬 PC에서 실행되면 보통 bolt://localhost:7687 입니다.
    """
    neo4j_auth = os.getenv("NEO4J_AUTH", "")
    auth_user = "neo4j"
    auth_password = ""

    # NEO4J_AUTH:
    # - Neo4j Docker 공식 환경변수는 보통 "neo4j/password" 형태입니다.
    # - GRAPH_DB_USER/PASSWORD가 없으면 이 값을 백엔드 접속 정보로 재사용합니다.
    if "/" in neo4j_auth:
        auth_user, auth_password = neo4j_auth.split("/", 1)

    # 1. GRAPH_DB_* 우선, 2. NEO4J_* 차선, 3. 기본값 순으로 읽어옴
    uri = os.getenv("GRAPH_DB_URI") or os.getenv("NEO4J_URI") or "bolt://neo4j:7687"
    user = os.getenv("GRAPH_DB_USER") or os.getenv("NEO4J_USER") or auth_user
    password = os.getenv("GRAPH_DB_PASSWORD") or os.getenv("NEO4J_PASSWORD") or auth_password

    return Neo4jClient(uri=uri, user=user, password=password)


# 앱 전체에서 재사용할 Neo4j client입니다.
# FastAPI가 여러 요청을 처리할 때 매번 driver를 새로 만들지 않기 위해 전역 객체로 둡니다.
neo4j_client = create_neo4j_client_from_env()


def get_neo4j() -> Neo4jClient:
    """
    FastAPI dependency로 사용할 Neo4j client provider입니다.

    사용 예:
        graph: Neo4jClient = Depends(get_neo4j)
    """
    return neo4j_client

