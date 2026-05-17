import logging
import os
from typing import Any

import httpx
from openai import OpenAI
from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

OLLAMA_TIMEOUT = httpx.Timeout(180.0, connect=10.0)

# Clients for external providers
openai_client = None
google_client = None

def get_openai_client():
    global openai_client
    if openai_client is None:
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return openai_client

def get_google_client():
    global google_client
    if google_client is None:
        google_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    return google_client

async def chat(messages: list[dict[str, str]], model: str | None = None) -> str:
    """
    Send a chat completion request to the configured LLM provider.
    """
    provider = settings.LLM_PROVIDER.lower()
    if provider != "openai":
        model = settings.LLM_MODEL
    else:
        model = model or settings.LLM_MODEL

    if provider == "openai":
        return await _chat_openai(messages, model)
    elif provider == "google":
        return await _chat_google(messages, model)
    else:
        return await _chat_ollama(messages, model)

async def _chat_openai(messages: list[dict[str, str]], model: str) -> str:
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.error("OpenAI chat error: %s", exc)
        return f"[AI ERROR] OpenAI failure: {str(exc)}"

async def _chat_google(messages: list[dict[str, str]], model: str) -> str:
    try:
        client = get_google_client()
        # Convert messages to Google format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            if msg["role"] == "system":
                # Gemini handles system instructions separately or as first user message
                # For simplicity, we'll prefix it to the next message or send as user
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=f"System Instruction: {msg['content']}")]))
            else:
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
        
        response = client.models.generate_content(
            model=model,
            contents=contents
        )
        return response.text or ""
    except Exception as exc:
        logger.error("Google chat error: %s", exc)
        return f"[AI ERROR] Google Gemini failure: {str(exc)}"

async def _chat_ollama(messages: list[dict[str, str]], model: str) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
    except Exception as exc:
        logger.error("Ollama chat error: %s", exc)
        return f"[AI ERROR] Ollama failure: {str(exc)}"

async def generate(prompt: str, model: str | None = None) -> str:
    """
    Single-turn text generation via configured provider.
    """
    return await chat([{"role": "user", "content": prompt}], model)

async def embed(text: str, model: str | None = None) -> list[float]:
    """
    Generate a vector embedding for the given text.
    """
    provider = settings.LLM_PROVIDER.lower()
    if provider == "google":
        model = "text-embedding-004"
    elif provider == "ollama":
        model = settings.OLLAMA_MODEL
    else:
        model = model or "text-embedding-3-small"

    if provider == "openai":
        try:
            client = get_openai_client()
            response = client.embeddings.create(input=[text], model=model)
            return response.data[0].embedding
        except Exception as exc:
            logger.error("OpenAI embed error: %s", exc)
            return []
    elif provider == "google":
        try:
            client = get_google_client()
            response = client.models.embed_content(
                model=model, # e.g., "text-embedding-004"
                contents=text
            )
            return response.embeddings[0].values
        except Exception as exc:
            logger.error("Google embed error: %s", exc)
            return []
    else:
        # Ollama
        model = model or settings.OLLAMA_MODEL
        payload = {"model": model, "prompt": text}
        try:
            async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("embedding", [])
        except Exception as exc:
            logger.error("Ollama embed error: %s", exc)
            return []

async def check_ai_status() -> dict[str, Any]:
    """Check availability of configured AI provider."""
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    return {
                        "provider": "ollama",
                        "available": True,
                        "status": "online",
                        "models": models,
                    }
        except:
            pass
        return {"provider": "ollama", "available": False, "status": "offline"}
    
    elif provider == "openai":
        has_key = bool(settings.OPENAI_API_KEY and "your_openai" not in settings.OPENAI_API_KEY)
        return {
            "provider": "openai",
            "available": has_key,
            "status": "online" if has_key else "key_missing",
            "model": settings.LLM_MODEL
        }
    
    elif provider == "google":
        has_key = bool(settings.GOOGLE_API_KEY and "your_google" not in settings.GOOGLE_API_KEY)
        return {
            "provider": "google",
            "available": has_key,
            "status": "online" if has_key else "key_missing",
            "model": settings.LLM_MODEL
        }
    
    return {"provider": "unknown", "available": False}
