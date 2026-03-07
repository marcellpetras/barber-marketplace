from typing import List, Optional
from pydantic import BaseModel, Field

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
    user_id: str
    text: str = Field(min_length=1, max_length=500)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class BroadcastResponse(BaseModel):
    status: str
    auction_id: str
    notified_barbers: int
    ai_parsed_as: ParsedIntent


class BidSubmission(BaseModel):
    auction_id: str = Field(description="The UUID of the active auction")
    barber_id: str = Field(description="The UUID of the barber placing the bid")
    price: float = Field(gt=0, description="The proposed price (must be greater than 0)")
    eta_minutes: int = Field(ge=0, description="Estimated time of arrival or wait time in minutes")


class BidResponse(BaseModel):
    status: str
    bid_id: str
    auction_id: str
    price: float
    eta_minutes: int