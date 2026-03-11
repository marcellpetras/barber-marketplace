from contextlib import asynccontextmanager
from typing import Optional

from fastapi import HTTPException, Header
from langchain_openai import ChatOpenAI
from supabase import AsyncClient, create_async_client

from backend.config import settings, validate_settings
from backend.schemas import CurrentActor


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


def get_bearer_token(authorization: Optional[str] = Header()): #assuming bearer type of auth
    
    if not authorization:
        raise HTTPException(status_code=401, detail="tbd")
    
    scheme,_,token = authorization.partition(" ")
    if scheme.lower() != 'bearer' or not token:
        raise HTTPException(status_code=401, detail="tbd")
    
    return token.strip()


async def get_current_actor(authorization: Optional[str] = Header()):
    #assuming format is "Authorization: bearer customer_id:customer_role"

    token = get_bearer_token(authorization)
    client = get_supabase_client()
    auth_response = await client.auth.get_user(token)
    user = auth_response.user

    if not user:
        raise HTTPException(status_code=401, detail='Invalid token')
    
    profile_result = await client.table('profiles').select('id, role').eq('id',user.id).execute()

    if not profile_result.data:
        raise HTTPException(status_code =403, detail='Profile not found')
    
    profile = profile_result.data[0]
    return CurrentActor(
        user_id = profile['id'],
        role = profile['role']
    )


