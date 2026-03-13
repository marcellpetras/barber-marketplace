from fastapi import APIRouter, HTTPException

from backend.schemas import BroadcastRequest, BroadcastResponse, AuctionListResponse
from backend.services.broadcast import (
    build_auction_payload,
    create_auction,
    find_nearby_barbers,
    get_nearby_auctions,
    get_user_auctions,
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


    request_created_at, service_time, request_expires_at = resolve_request_times(parsed)

    payload = build_auction_payload(
        req=req,
        parsed=parsed,
        lng=req.lng,
        lat=req.lat,
        request_created_at=request_created_at,
        service_time=service_time,
        request_expires_at=request_expires_at,
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


@router.get("/auctions/nearby", response_model=AuctionListResponse)
async def list_nearby_auctions(lat: float, lng: float, radius: float = 15000):
    """Find open auctions near a given latitude and longitude."""
    auctions = await get_nearby_auctions(lat, lng, radius)
    return AuctionListResponse(auctions=auctions)

@router.get("/users/{user_id}/auctions", response_model=AuctionListResponse)
async def list_user_auctions(user_id: str):
    """List all auctions created by a specific user."""
    auctions = await get_user_auctions(user_id)
    return AuctionListResponse(auctions=auctions)