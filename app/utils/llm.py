import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv(override=True)

def get_llm():
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Set it in .env and restart.")
    return ChatGroq(
        model="llama-3.3-70b-versatile",   # FAST + FREE
        temperature=0.3,
        api_key=api_key
    )

