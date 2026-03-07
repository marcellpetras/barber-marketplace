from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from backend.config import settings
from backend.dependencies import get_llm, get_supabase_client
from backend.schemas import BroadcastRequest, ParsedIntent


async def parse_user_text(text: str) -> ParsedIntent:
    parser = JsonOutputParser(pydantic_object=ParsedIntent)

    prompt = ChatPromptTemplate.from_template(
        "You are a barber shop assistant. Extract the service details from: '{user_input}'.\n"
        "{format_instructions}"
    )

    chain = prompt | get_llm() | parser

    parsed = await chain.ainvoke(
        {
            "user_input": text,
            "format_instructions": parser.get_format_instructions(),
        }
    )

    return ParsedIntent(**parsed)


def resolve_request_times(parsed: ParsedIntent):
    requested_at = datetime.now(timezone.utc)

    service_time = None
    if parsed.requested_time:
        try:
            service_time = datetime.fromisoformat(parsed.requested_time)
            if service_time.tzinfo is None:
                service_time = service_time.replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="invalid extracted requested_time format",
            )

    max_expiry = requested_at + timedelta(hours=settings.default_expiry_hours)
    expires_at = min(max_expiry, service_time) if service_time else max_expiry

    return requested_at, service_time, expires_at


def build_auction_payload(
    req: BroadcastRequest,
    parsed: ParsedIntent,
    point: str,
    requested_at: datetime,
    service_time: Optional[datetime],
    expires_at: datetime,
) -> dict:
    return {
        "customer_id": req.user_id,
        "service_category": parsed.service_category,
        "structured_intent": parsed.model_dump(),
        "location": point,
        "created_at": requested_at.isoformat(),
        "scheduled_at": service_time.isoformat() if service_time else None,
        "expires_at": expires_at.isoformat(),
        "status": "open",
    }


async def create_auction(payload: dict) -> str:
    client = get_supabase_client()
    result = await client.table("auctions").insert(payload).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create auction")

    return result.data[0]["id"]


async def find_nearby_barbers(lat: float, lng: float) -> int:
    client = get_supabase_client()

    nearby = await client.rpc(
        "get_eligible_barbers",
        {
            "user_lat": lat,
            "user_lng": lng,
            "max_radius_meters": settings.max_radius_meters,
        },
    ).execute()

    return len(nearby.data or [])