from fastapi import HTTPException


def test_bid_success(client, monkeypatch):
    async def mock_get_auction_status(auction_id: str):
        return "open"

    def mock_ensure_auction_open(status: str):
        return None

    async def mock_create_bid(bid):
        return "bid-123"

    monkeypatch.setattr("backend.routers.bids.get_auction_status", mock_get_auction_status)
    monkeypatch.setattr("backend.routers.bids.ensure_auction_open", mock_ensure_auction_open)
    monkeypatch.setattr("backend.routers.bids.create_bid", mock_create_bid)

    response = client.post(
        "/bid",
        json={
            "auction_id": "auction-123",
            "barber_id": "barber-456",
            "price": 25.0,
            "eta_minutes": 15,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "Bid successfully placed"
    assert body["bid_id"] == "bid-123"
    assert body["auction_id"] == "auction-123"
    assert body["price"] == 25.0
    assert body["eta_minutes"] == 15


def test_bid_auction_not_found(client, monkeypatch):
    async def mock_get_auction_status(auction_id: str):
        raise HTTPException(status_code=404, detail="Auction not found")

    monkeypatch.setattr("backend.routers.bids.get_auction_status", mock_get_auction_status)

    response = client.post(
        "/bid",
        json={
            "auction_id": "missing-auction",
            "barber_id": "barber-456",
            "price": 25.0,
            "eta_minutes": 15,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Auction not found"


def test_bid_auction_closed(client, monkeypatch):
    async def mock_get_auction_status(auction_id: str):
        return "closed"

    def mock_ensure_auction_open(status: str):
        raise HTTPException(
            status_code=400,
            detail="This auction is no longer open for bidding",
        )

    monkeypatch.setattr("backend.routers.bids.get_auction_status", mock_get_auction_status)
    monkeypatch.setattr("backend.routers.bids.ensure_auction_open", mock_ensure_auction_open)

    response = client.post(
        "/bid",
        json={
            "auction_id": "auction-123",
            "barber_id": "barber-456",
            "price": 25.0,
            "eta_minutes": 15,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "This auction is no longer open for bidding"


def test_bid_duplicate_bid(client, monkeypatch):
    async def mock_get_auction_status(auction_id: str):
        return "open"

    def mock_ensure_auction_open(status: str):
        return None

    async def mock_create_bid(bid):
        raise HTTPException(
            status_code=400,
            detail="You have already placed a bid on this auction.",
        )

    monkeypatch.setattr("backend.routers.bids.get_auction_status", mock_get_auction_status)
    monkeypatch.setattr("backend.routers.bids.ensure_auction_open", mock_ensure_auction_open)
    monkeypatch.setattr("backend.routers.bids.create_bid", mock_create_bid)

    response = client.post(
        "/bid",
        json={
            "auction_id": "auction-123",
            "barber_id": "barber-456",
            "price": 25.0,
            "eta_minutes": 15,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You have already placed a bid on this auction."


def test_list_auction_bids(client, monkeypatch):
    async def mock_get_bids_for_auction(auction_id: str):
        return [
            {
                "id": "bid-123",
                "auction_id": auction_id,
                "barber_id": "barber-456",
                "price": 25.0,
                "eta_minutes": 15,
                "status": "pending",
                "status": "pending",
                "created_at": "2026-03-08T00:00:00Z",
                "distance_meters": 500.0,
                "barber_name": "Test Barber",
                "barber_rating": 4.5,
                "score": 0.85
            }
        ]

    monkeypatch.setattr("backend.routers.bids.get_bids_for_auction", mock_get_bids_for_auction)

    response = client.get("/auction/auction-123/bids")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bids"]) == 1
    assert body["bids"][0]["id"] == "bid-123"


def test_accept_bid_success(client, monkeypatch):
    async def mock_accept_winning_bid(auction_id: str, bid_id: str):
        return None

    monkeypatch.setattr("backend.routers.bids.accept_winning_bid", mock_accept_winning_bid)

    response = client.post(
        "/auction/auction-123/accept",
        json={"bid_id": "bid-123"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Bid accepted and auction closed"}