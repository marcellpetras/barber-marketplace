from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class ParsedIntent(BaseModel):
    service_category: str = Field(description="Service type, e.g., 'haircut', 'shave'")
    preferences: Optional[List[str]] = Field(
        default=None,
        description="Style specifics like 'skin fade' or 'long hair'",
    )
    is_urgent: bool = Field(description="Is the user asking for something ASAP?")
    requested_time: Optional[str] = Field(
        default=None,
        description="Requested service time in ISO format if the user specifies one",
    )


class BroadcastRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class BroadcastResponse(BaseModel):
    status: str
    auction_id: str
    notified_barbers: int
    ai_parsed_as: ParsedIntent
    request_created_at: datetime 
    request_expires_at: datetime 
    service_scheduled_at: Optional[datetime] 


class BidSubmission(BaseModel):
    auction_id: str = Field(description="The UUID of the active auction")
    price: float = Field(gt=0, description="The proposed price (must be greater than 0)")
    eta_minutes: int = Field(ge=0, description="Estimated time of arrival or wait time in minutes")

class BidCreate(BaseModel):
    auction_id: str
    barber_id: str
    price: float
    eta_minutes: int

class BidResponse(BaseModel):
    status: str
    bid_id: str
    auction_id: str
    price: float
    eta_minutes: int

class RankedBidItem(BaseModel):
    id: str
    auction_id: str
    barber_id: str
    barber_name: str
    barber_rating: float
    price: float
    eta_minutes: int
    distance_meters: float
    status: str
    created_at: str
    score: float


class AuctionBidsResponse(BaseModel):
    bids: List[RankedBidItem]


class BidAcceptRequest(BaseModel):
    bid_id: str = Field(description="The UUID of the winning bid to accept")


class CurrentActor(BaseModel): #actor model for auth context
    user_id: str
    role: Literal['customer', 'barber']
    