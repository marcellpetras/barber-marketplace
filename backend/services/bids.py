from fastapi import HTTPException

from backend.dependencies import get_supabase_client
from backend.schemas import BidSubmission
import random #temmporarily


async def get_auction_status(auction_id: str) -> str:
    """Return the current status for the given auction."""
    client = get_supabase_client()

    result = await client.table("auctions").select("status").eq("id", auction_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Auction not found")

    return result.data[0]["status"]


def ensure_auction_open(status: str) -> None:
    """Reject bidding attempts for auctions that are not open."""
    if status != "open":
        raise HTTPException(
            status_code=400,
            detail="This auction is no longer open for bidding",
        )


async def create_bid(bid: BidSubmission) -> str:
    """Insert a new bid and map common database errors to HTTP responses."""
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

async def get_bids_for_auction(auction_id: str):
    """Return enriched auction bids ranked by normalized price, rating, and distance."""
    client = get_supabase_client()

    bids_result = (
        await client.table("bids")
        .select("*")
        .eq("auction_id", auction_id)
        .execute()
    )
    bids = bids_result.data or []
    if not bids:
        return []

    barber_ids = list({bid["barber_id"] for bid in bids if bid.get("barber_id")})
    profiles_by_id = {}

    if barber_ids:
        profiles_result = (
            await client.table("profiles")
            .select("id, full_name, rating")
            .in_("id", barber_ids)
            .execute()
        )
        profiles_by_id = {
            profile["id"]: profile
            for profile in (profiles_result.data or [])
        }

    enriched_bids = []
    prices, ratings, distances = [], [], []

    for bid in bids:
        profile = profiles_by_id.get(bid["barber_id"], {})
        barber_rating = float(profile.get("rating") or 0)
        distance_meters = round(random.uniform(100, 3000), 2)
        price = float(bid["price"])

        enriched = {
            **bid,
            "barber_name": profile.get("full_name", "Unknown"),
            "barber_rating": barber_rating,
            "distance_meters": distance_meters,
        }
        enriched_bids.append(enriched)

        prices.append(price)
        ratings.append(barber_rating)
        distances.append(distance_meters)

    min_price, max_price = min(prices), max(prices)
    min_rating, max_rating = min(ratings), max(ratings)
    min_distance, max_distance = min(distances), max(distances)

    def norm(value: float, low: float, high: float, *, reverse: bool = False) -> float:
        """Normalize a value to 0..1, optionally reversing lower-is-better metrics."""
        if high == low:
            return 1.0
        score = (value - low) / (high - low)
        return 1.0 - score if reverse else score

    ranked_bids = [
        {
            **bid,
            "score": round(
                norm(float(bid["price"]), min_price, max_price, reverse=True) * 0.5
                + norm(float(bid["barber_rating"]), min_rating, max_rating) * 0.3
                + norm(float(bid["distance_meters"]), min_distance, max_distance, reverse=True) * 0.2,
                4,
            ),
        }
        for bid in enriched_bids
    ]

    return sorted(ranked_bids, key=lambda bid: bid["score"], reverse=True)


async def accept_winning_bid(auction_id: str, bid_id: str) -> None:
    """Accept a winning bid through the atomic database RPC."""
    client = get_supabase_client()

    try:
        await client.rpc(
            "accept_bid_for_auction",
            {
                "p_auction_id": auction_id,
                "p_bid_id": bid_id,
            },
        ).execute()

    except Exception as e:
        error_msg = str(e)
        if "Auction not found" in error_msg:
            raise HTTPException(status_code=404, detail="Auction not found")

        if "Auction is not open for acceptance" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="This auction is no longer open for acceptance",
            )

        if "Bid not found for this auction" in error_msg:
            raise HTTPException(
                status_code=404,
                detail="Bid not found for this auction",
            )

        if "Bid is not pending" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="This bid is no longer pending",
            )
        
        if "Failed to update auction" in error_msg:
            raise HTTPException(
                status_code=500,
                detail="Failed to update auction",
            )

        raise HTTPException(
            status_code=500,
            detail="An error occurred while accepting the bid.",
        )

async def get_barber_bids(barber_id: str):
    """Get all bids placed by a specific barber, including the associated auction details."""
    client = get_supabase_client()
    
    result = (
        await client.table("bids")
        .select("*, auctions!bids_auction_id_fkey(*)")
        .eq("barber_id", barber_id)
        .order("created_at", desc=True)
        .execute()
    )
    
    # Restructure the response to match the BidWithAuctionResponse schema
    bids = []
    for row in (result.data or []):
        auction = row.pop("auctions", None)
        bid = {
            "bid_id": row.pop("id"),
            **row
        }
        if auction:
            bid["auction"] = {
                "auction_id": auction.pop("id"),
                **auction
            }
        bids.append(bid)

    return bids
