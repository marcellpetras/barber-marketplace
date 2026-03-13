import asyncio
import httpx
from colorama import Fore, Style, init

init()

BASE_URL = "http://127.0.0.1:8000"

# From seed.sql
CUSTOMER_ID = "00000000-0000-0000-0000-000000000000"
BARBER_ID = "11111111-1111-1111-1111-111111111111"

async def run_e2e_flow():
    print(Fore.CYAN + "=== Simulating Barber Marketplace E2E Flow ===" + Style.RESET_ALL)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Step 1: Customer Broadcasts a Request
        print(Fore.YELLOW + "\n[Customer] Browsing for a haircut..." + Style.RESET_ALL)
        req_payload = {
            "user_id": CUSTOMER_ID,
            "text": "I need a skin fade haircut near the city center as soon as possible",
            "lat": 47.4979, 
            "lng": 19.0402 
        }
        print(f"  Sending request: {req_payload['text']}")
        
        resp = await client.post("/broadcast", json=req_payload)
        resp.raise_for_status()
        broadcast_data = resp.json()
        auction_id = broadcast_data["auction_id"]
        
        print(Fore.GREEN + f"  Success! Auction created: {auction_id}" + Style.RESET_ALL)
        print(Fore.BLUE + f"  AI Extracted Intent: {broadcast_data['ai_parsed_as']}" + Style.RESET_ALL)
        print(f"  Notified Barbers Nearby: {broadcast_data['notified_barbers']}")

        await asyncio.sleep(1)

        # Step 2: Barber Finds the Auction
        print(Fore.YELLOW + "\n[Barber] Checking for nearby open requests..." + Style.RESET_ALL)
        resp = await client.get("/auctions/nearby", params={"lat": 47.4979, "lng": 19.0402, "radius": 5000})
        resp.raise_for_status()
        auctions = resp.json()["auctions"]
        
        print(Fore.GREEN + f"  Found {len(auctions)} open auctions." + Style.RESET_ALL)
        target_auction = next((a for a in auctions if a["auction_id"] == auction_id), None)
        if not target_auction:
            print(Fore.RED + "  Error: Could not find the broadcasted auction!" + Style.RESET_ALL)
            return
            
        print(f"  Selected Request: {target_auction['structured_intent']}")

        await asyncio.sleep(1)

        # Step 3: Barber Submits a Bid
        print(Fore.YELLOW + "\n[Barber] Submitting a quote for the haircut..." + Style.RESET_ALL)
        bid_payload = {
            "auction_id": auction_id,
            "barber_id": BARBER_ID,
            "price": 35.00,
            "eta_minutes": 20
        }
        
        resp = await client.post("/bid", json=bid_payload)
        resp.raise_for_status()
        bid_data = resp.json()
        bid_id = bid_data["bid_id"]
        
        print(Fore.GREEN + f"  Success! Bid placed: {bid_id} (Price: ${bid_payload['price']}, ETA: {bid_payload['eta_minutes']}m)" + Style.RESET_ALL)

        await asyncio.sleep(1)

        # Step 4: Customer Checks Bids
        print(Fore.YELLOW + "\n[Customer] Checking app for barber quotes..." + Style.RESET_ALL)
        resp = await client.get(f"/auction/{auction_id}/bids")
        resp.raise_for_status()
        bids = resp.json()["bids"]
        
        print(Fore.GREEN + f"  Found {len(bids)} quotes." + Style.RESET_ALL)
        top_bid = bids[0]
        print(f"  Top Ranked Bid: {top_bid['barber_name']} - ${top_bid['price']} (Score: {top_bid['score']})")

        await asyncio.sleep(1)

        # Step 5: Customer Accepts the Bid
        print(Fore.YELLOW + f"\n[Customer] Accepting the quote from {top_bid['barber_name']}..." + Style.RESET_ALL)
        resp = await client.post(f"/auction/{auction_id}/accept", json={"bid_id": top_bid["id"]})
        resp.raise_for_status()
        
        print(Fore.GREEN + "  Success! Bid accepted. The barber is on their way." + Style.RESET_ALL)

        await asyncio.sleep(1)

        # Step 6: Barber Checks Status
        print(Fore.YELLOW + "\n[Barber] Checking job status..." + Style.RESET_ALL)
        resp = await client.get(f"/barbers/{BARBER_ID}/bids")
        resp.raise_for_status()
        barber_bids = resp.json()["bids"]
        
        won_bid = next((b for b in barber_bids if b["bid_id"] == bid_id), None)
        print(Fore.GREEN + f"  Bid Status: {won_bid['status'].upper()}" + Style.RESET_ALL)
        
        print(Fore.CYAN + "\n=== End of Flow ===" + Style.RESET_ALL)


if __name__ == "__main__":
    asyncio.run(run_e2e_flow())
