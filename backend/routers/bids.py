from fastapi import APIRouter

from backend.schemas import BidResponse, BidSubmission
from backend.services.bids import create_bid, ensure_auction_open, get_auction_status


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