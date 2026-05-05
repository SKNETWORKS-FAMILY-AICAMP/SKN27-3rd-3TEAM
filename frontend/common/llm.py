# llm.py (LangChain 방식으로 교체)
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)

def llm_generate(prompt: str) -> str:
    response = llm.invoke(prompt)
    return response.content.strip()