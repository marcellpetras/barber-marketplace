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



# *************** API Endpoint ***************

@app.post("/broadcast") #listen for POST requests at /broadcast
async def broadcast_request(user_id: str, text: str, lat: float, lng: float):

    # Step A: ---> AI Parsing
    try:
        parsed = await parse_user_text(text)
    except Exception:
        raise HTTPException(status_code=422, detail="AI could not understand intent")

    # Step B: ---> Prep Spatial/Temporal data for our SQL Schema
    # PostGIS expects 'POINT(lng lat)'

    point = f"POINT({lng} {lat})"
    
    # Set expiration: 10 mins for auction, 1 hour for service window
    scheduled_at = datetime.now() + timedelta(hours=1)
    expires_at = datetime.now() + timedelta(minutes=10)

    # Step C: ---> Insert into the 'auctions' table
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
    
    # Step D: ---> Check how many barbers we are about to notify
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