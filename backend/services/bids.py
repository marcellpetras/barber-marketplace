from fastapi import HTTPException

from backend.dependencies import get_supabase_client
from backend.schemas import BidSubmission


async def get_auction_status(auction_id: str) -> str:
    client = get_supabase_client()

    result = await client.table("auctions").select("status").eq("id", auction_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Auction not found")

    return result.data[0]["status"]


def ensure_auction_open(status: str) -> None:
    if status != "open":
        raise HTTPException(
            status_code=400,
            detail="This auction is no longer open for bidding",
        )


async def create_bid(bid: BidSubmission) -> str:
    client = get_supabase_client()

    try:
        result = await client.table("bids").insert(bid.model_dump()).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create bid")

        return result.data[0]["id"]

    except HTTPException:
        raise

    except Exception as e:
        error_msg = str(e)

        if "unique_barber_bid" in error_msg or "23505" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="You have already placed a bid on this auction.",
            )

        if "23503" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid barber ID or auction ID.",
            )

        raise HTTPException(
            status_code=500,
            detail="An error occurred while placing the bid.",
        )