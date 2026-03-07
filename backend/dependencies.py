from contextlib import asynccontextmanager
from typing import Optional

from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from supabase import AsyncClient, create_async_client

from backend.config import settings, validate_settings


supabase: Optional[AsyncClient] = None

def get_supabase_client() -> AsyncClient:
    if supabase is None:
        raise HTTPException(status_code=500, detail="Database client is not initialized")
    return supabase


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
    )



@asynccontextmanager
async def lifespan(app):
    global supabase

    validate_settings(settings)

    supabase = await create_async_client(
        settings.supabase_url,
        settings.supabase_key,
    )
    yield
    await supabase.auth.sign_out()