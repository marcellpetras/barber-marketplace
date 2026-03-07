import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from supabase import create_async_client, AsyncClient
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from contextlib import asynccontextmanager

# Load keys from .env
load_dotenv()

# Define a global variable for the database client
supabase: Optional[AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global supabase
    supabase = await create_async_client(
        os.getenv("SUPABASE_URL"), 
        os.getenv("SUPABASE_KEY")
    )
    yield
    await supabase.auth.sign_out() 

# Create the app with the lifespan attached 
app = FastAPI(title="Barber Marketplace AI Orchestrator", lifespan=lifespan)

# Initialize OpenAI Client
llm = ChatOpenAI(model="gpt-5-nano", temperature=0)

# Define the structured intent schema 
class ParsedIntent(BaseModel):
    service_category: str = Field(description="Service type, e.g., 'haircut', 'shave'")
    preferences: Optional[List[str]] = Field(description="Style specifics like 'skin fade' or 'long hair'")
    is_urgent: bool = Field(description="Is the user asking for something ASAP?")

# Define the bid submission schema for barbers
class BidSubmission(BaseModel):
    auction_id: str = Field(description="The UUID of the active auction")
    barber_id: str = Field(description="The UUID of the barber placing the bid")
    price: float = Field(gt=0, description="The proposed price (must be greater than 0)")
    eta_minutes: int = Field(ge=0, description="Estimated time of arrival or wait time in minutes")

# Parsing logic
async def parse_user_text(text: str) -> ParsedIntent:
    parser = JsonOutputParser(pydantic_object=ParsedIntent) 
    
    prompt = ChatPromptTemplate.from_template( 
        "You are a barber shop assistant. Extract the service details from: '{user_input}'.\n"
        "{format_instructions}"
    )
    
    chain = prompt | llm | parser #pipeline 

    #prompt takes dict → outputs formatted string
    #llm takes string → outputs AI response text
    #parser takes text → outputs ParsedIntent object

    return await chain.ainvoke({
        "user_input": text,
        "format_instructions": parser.get_format_instructions()
    })



# *************** API Endpoints ***************

@app.post("/broadcast") #listen for POST requests at /broadcast
async def broadcast_request(user_id: str, text: str, lat: float, lng: float):

    # Step 1: ---> AI Parsing
    try:
        parsed = await parse_user_text(text)
    except Exception:
        raise HTTPException(status_code=422, detail="AI could not understand intent")

    # Step 2: ---> Prep Spatial/Temporal data for our SQL Schema
    # PostGIS expects 'POINT(lng lat)'

    point = f"POINT({lng} {lat})"
    
    # Set expiration: 10 mins for auction, 1 hour for service window
    scheduled_at = datetime.now() + timedelta(hours=1)
    expires_at = datetime.now() + timedelta(minutes=10)

    # Step 3: ---> Insert into the 'auctions' table
    auction_data = {
        "customer_id": user_id,
        "service_category": parsed["service_category"],
        "structured_intent": parsed, 
        "location": point,
        "scheduled_at": scheduled_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "status": "open"
    }

    result = await supabase.table("auctions").insert(auction_data).execute() 
    
    # Step 4: ---> Check how many barbers we are about to notify
    nearby = await supabase.rpc('get_eligible_barbers', { #triggers the specified SQL funtion and returns the list
        'user_lat': lat, 
        'user_lng': lng, 
        'max_radius_meters': 5000
    }).execute() 

    return {
        "status": "Auction Live",
        "auction_id": result.data[0]['id'],
        "notified_barbers": len(nearby.data),
        "ai_parsed_as": parsed
    }

@app.post("/bid")
async def submit_bid(bid: BidSubmission):
    
    # Step 1: Verify the auction exists and is actually open
    auction_res = await supabase.table("auctions").select("status").eq("id", bid.auction_id).execute()
    
    if not auction_res.data:
        raise HTTPException(status_code=404, detail="Auction not found")
        
    if auction_res.data[0]["status"] != "open":
        raise HTTPException(status_code=400, detail="This auction is no longer open for bidding")

    # Step 2: Insert the bid
    try:
        # Convert the Pydantic model to a dictionary for Supabase
        bid_data = bid.model_dump()
        
        result = await supabase.table("bids").insert(bid_data).execute()
        
        return {
            "status": "Bid successfully placed",
            "bid_id": result.data[0]["id"],
            "auction_id": bid.auction_id,
            "price": bid.price,
            "eta_minutes": bid.eta_minutes
        }
        
    except Exception as e:
        error_msg = str(e)
        # Catch the specific unique constraint violation from PostgreSQL
        if "unique_barber_bid" in error_msg or "23505" in error_msg:
            raise HTTPException(
                status_code=400, 
                detail="You have already placed a bid on this auction."
            )
        # Catch foreign key violations (e.g., Barber doesn't exist)
        elif "23503" in error_msg:
            raise HTTPException(
                status_code=400, 
                detail="Invalid barber ID or auction ID."
            )
        # Generic fallback
        raise HTTPException(status_code=500, detail="An error occurred while placing the bid.")


        