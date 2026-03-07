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


async def get_bids_for_auction(auction_id: str) -> list[dict]:
    client = get_supabase_client()
    
    result = await client.table("bids").select("*").eq("auction_id", auction_id).execute()
    
    return result.data or []


async def accept_winning_bid(auction_id: str, bid_id: str) -> None:
    client = get_supabase_client()

    # Verify the auction is still open
    status = await get_auction_status(auction_id)
    ensure_auction_open(status)

    # Begin the process of accepting the bid
    # First, verify the bid belongs to this auction
    bid_result = await client.table("bids").select("id").eq("id", bid_id).eq("auction_id", auction_id).execute()
    if not bid_result.data:
        raise HTTPException(status_code=404, detail="Bid not found for this auction")

    # We update the accepted bid
    update_bid_res = await client.table("bids").update({"status": "accepted"}).eq("id", bid_id).execute()
    if not update_bid_res.data:
        raise HTTPException(status_code=500, detail="Failed to accept the bid")

    # Update all other bids to rejected
    await client.table("bids").update({"status": "rejected"}).eq("auction_id", auction_id).neq("id", bid_id).execute()

    # Update the auction itself
    update_auction_res = await client.table("auctions").update({
        "status": "accepted",
        "winning_bid_id": bid_id
    }).eq("id", auction_id).execute()

    if not update_auction_res.data:
        # In a fully transactional system, we'd rollback. Since we use supabase postgrest,
        # we try our best. This point would mean DB schema is probably misaligned.
        raise HTTPException(status_code=500, detail="Failed to update auction status")