from fastapi import APIRouter, HTTPException

from backend.schemas import BroadcastRequest, BroadcastResponse
from backend.services.broadcast import (
    build_auction_payload,
    create_auction,
    find_nearby_barbers,
    parse_user_text,
    resolve_request_times,
)


router = APIRouter(tags=["broadcast"])


@router.post("/broadcast", response_model=BroadcastResponse)
async def broadcast_request(req: BroadcastRequest):
    try:
        parsed = await parse_user_text(req.text)
    except Exception:
        raise HTTPException(status_code=422, detail="AI could not understand intent")

    point = f"POINT({req.lng} {req.lat})"

    requested_at, service_time, expires_at = resolve_request_times(parsed)

    payload = build_auction_payload(
        req=req,
        parsed=parsed,
        point=point,
        requested_at=requested_at,
        service_time=service_time,
        expires_at=expires_at,
    )

    auction_id = await create_auction(payload)
    notified_barbers = await find_nearby_barbers(req.lat, req.lng)

    return BroadcastResponse(
        status="Auction Live",
        auction_id=auction_id,
        notified_barbers=notified_barbers,
        ai_parsed_as=parsed,
    )