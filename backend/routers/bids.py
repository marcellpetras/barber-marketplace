from fastapi import APIRouter, Depends, HTTPException

from backend.schemas import (
    BidCreate,
    BidResponse, 
    BidSubmission, 
    AuctionBidsResponse,
    BidAcceptRequest,
    CurrentActor
    )

from backend.services.bids import (
    create_bid, 
    ensure_auction_open, 
    get_auction_status, 
    get_bids_for_auction, 
    accept_winning_bid,
    ensure_customer_owns_auction
    )

from backend.dependencies import get_current_actor


router = APIRouter(tags=["bids"])


@router.post("/bid", response_model=BidResponse)
async def submit_bid(
    bid: BidSubmission, 
    actor: CurrentActor = Depends(get_current_actor)):

    if actor.role != 'barber':
        raise HTTPException(status_code=403, detail="Only barbers can palce bids ") 

    status = await get_auction_status(bid.auction_id)
    ensure_auction_open(status)

    payload = BidCreate(
    auction_id=bid.auction_id,
    barber_id=actor.user_id,
    price=bid.price,
    eta_minutes=bid.eta_minutes,
    )

    bid_id = await create_bid(payload)

    return BidResponse(
        status="Bid successfully placed",
        bid_id=bid_id,
        auction_id=bid.auction_id,
        price=bid.price,
        eta_minutes=bid.eta_minutes,
    )


@router.get("/auction/{auction_id}/bids", response_model=AuctionBidsResponse)
async def list_auction_bids(auction_id: str, actor: CurrentActor = Depends(get_current_actor)):
    if actor.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can view auction bids")

    await ensure_customer_owns_auction(auction_id, actor.user_id)
    bids_data = await get_bids_for_auction(auction_id)
    return AuctionBidsResponse(bids=bids_data)


@router.post("/auction/{auction_id}/accept")
async def accept_bid(auction_id: str, request: BidAcceptRequest, actor: CurrentActor = Depends(get_current_actor)):
    if actor.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can accept bids")

    await ensure_customer_owns_auction(auction_id, actor.user_id)
    await accept_winning_bid(auction_id, request.bid_id)
    return {"status": "success", "message": "Bid accepted and auction closed"}