from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Pokemon App Backend")

# CORS 설정 (프론트엔드와 통신을 위해 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 프론트엔드 주소로 제한하는 것이 좋습니다.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Pokemon App API", "status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
