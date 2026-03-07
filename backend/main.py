from fastapi import FastAPI

from backend.dependencies import lifespan
from backend.routers.bids import router as bids_router
from backend.routers.broadcast import router as broadcast_router


app = FastAPI(title="Barber Marketplace AI Orchestrator", lifespan=lifespan)

app.include_router(broadcast_router)
app.include_router(bids_router)