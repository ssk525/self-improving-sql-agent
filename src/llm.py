from __future__ import annotations

from src.config import settings


def get_llm():
    if settings.groq_api_key:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=settings.groq_api_key,
        )
    if settings.google_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=settings.google_api_key,
        )
    if settings.openai_api_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=settings.openai_api_key)
    if settings.use_ollama:
        from langchain_ollama import ChatOllama

        return ChatOllama(model=settings.ollama_model, temperature=0)
    return None
