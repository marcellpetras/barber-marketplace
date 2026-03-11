from fastapi import APIRouter, HTTPException, Depends

from backend.schemas import BroadcastRequest, BroadcastResponse, CurrentUser
from backend.services.broadcast import (
    build_auction_payload,
    create_auction,
    find_nearby_barbers,
    parse_user_text,
    resolve_request_times,
)

from backend.dependencies import get_current_actor


router = APIRouter(tags=["broadcast"])


@router.post("/broadcast", response_model=BroadcastResponse)
async def broadcast_request(
    req: BroadcastRequest,
    actor: CurrentUser = Depends(get_current_actor)):

    if actor.role != 'customer':
        raise HTTPException(status_code=403, detail="Only customers can create broadcast requests") 

    try:
        parsed = await parse_user_text(req.text)
    except Exception:
        raise HTTPException(status_code=422, detail="AI could not understand intent")

    point = f"POINT({req.lng} {req.lat})"

    request_created_at, service_time, request_expires_at = resolve_request_times(parsed)

    payload = build_auction_payload(
        req=req,
        parsed=parsed,
        point=point,
        request_created_at=request_created_at,
        service_time=service_time,
        request_expires_at=request_expires_at,
        user_id = actor.user_id
    )

    auction_id = await create_auction(payload)
    notified_barbers = await find_nearby_barbers(req.lat, req.lng)

    return BroadcastResponse(
        status="Auction Live",
        auction_id=auction_id,
        notified_barbers=notified_barbers,
        ai_parsed_as=parsed,
        request_created_at=request_created_at,
        request_expires_at=request_expires_at,
        service_scheduled_at=service_time,
    )