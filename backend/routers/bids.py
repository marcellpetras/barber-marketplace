from fastapi import APIRouter

from backend.schemas import BidResponse, BidSubmission, AuctionBidsResponse, BidAcceptRequest, BidListResponse
from backend.services.bids import create_bid, ensure_auction_open, get_auction_status, get_bids_for_auction, accept_winning_bid, get_barber_bids


router = APIRouter(tags=["bids"])


@router.post("/bid", response_model=BidResponse)
async def submit_bid(bid: BidSubmission):
    status = await get_auction_status(bid.auction_id)
    ensure_auction_open(status)

    bid_id = await create_bid(bid)

    return BidResponse(
        status="Bid successfully placed",
        bid_id=bid_id,
        auction_id=bid.auction_id,
        price=bid.price,
        eta_minutes=bid.eta_minutes,
    )


@router.get("/auction/{auction_id}/bids", response_model=AuctionBidsResponse)
async def list_auction_bids(auction_id: str):
    bids_data = await get_bids_for_auction(auction_id)
    return AuctionBidsResponse(bids=bids_data)


@router.post("/auction/{auction_id}/accept")
async def accept_bid(auction_id: str, request: BidAcceptRequest):
    await accept_winning_bid(auction_id, request.bid_id)
    return {"status": "success", "message": "Bid accepted and auction closed"}

@router.get("/barbers/{barber_id}/bids", response_model=BidListResponse)
async def list_barber_bids(barber_id: str):
    """List all bids placed by a specific barber."""
    bids_data = await get_barber_bids(barber_id)
    return BidListResponse(bids=bids_data)