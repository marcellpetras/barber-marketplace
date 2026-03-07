from datetime import datetime, timezone
from backend.schemas import ParsedIntent


def test_broadcast_success(client, monkeypatch):
    parsed = ParsedIntent(
        service_category="haircut",
        preferences=["skin fade"],
        is_urgent=True,
        requested_time=None,
    )

    async def mock_parse_user_text(text: str):
        return parsed

    def mock_resolve_request_times(parsed_intent):
        now = datetime.now(timezone.utc)
        return now, None, now

    def mock_build_auction_payload(req, parsed, point, requested_at, service_time, expires_at):
        return {
            "customer_id": req.user_id,
            "service_category": parsed.service_category,
            "structured_intent": parsed.model_dump(),
            "location": point,
            "created_at": requested_at.isoformat(),
            "scheduled_at": None,
            "expires_at": expires_at.isoformat(),
            "status": "open",
        }

    async def mock_create_auction(payload: dict):
        return "auction-123"

    async def mock_find_nearby_barbers(lat: float, lng: float):
        return 4

    monkeypatch.setattr("backend.routers.broadcast.parse_user_text", mock_parse_user_text)
    monkeypatch.setattr("backend.routers.broadcast.resolve_request_times", mock_resolve_request_times)
    monkeypatch.setattr("backend.routers.broadcast.build_auction_payload", mock_build_auction_payload)
    monkeypatch.setattr("backend.routers.broadcast.create_auction", mock_create_auction)
    monkeypatch.setattr("backend.routers.broadcast.find_nearby_barbers", mock_find_nearby_barbers)

    response = client.post(
        "/broadcast",
        json={
            "user_id": "user-1",
            "text": "Need a haircut near the station",
            "lat": 47.3769,
            "lng": 8.5417,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "Auction Live"
    assert body["auction_id"] == "auction-123"
    assert body["notified_barbers"] == 4
    assert body["ai_parsed_as"]["service_category"] == "haircut"


def test_broadcast_invalid_request_body(client):
    response = client.post(
        "/broadcast",
        json={
            "user_id": "user-1",
            "text": "",
            "lat": 200,
            "lng": 8.5417,
        },
    )

    assert response.status_code == 422


def test_broadcast_ai_parse_failure(client, monkeypatch):
    async def mock_parse_user_text(text: str):
        raise Exception("LLM parsing failed")

    monkeypatch.setattr("backend.routers.broadcast.parse_user_text", mock_parse_user_text)

    response = client.post(
        "/broadcast",
        json={
            "user_id": "user-1",
            "text": "Need a haircut near the station",
            "lat": 47.3769,
            "lng": 8.5417,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "AI could not understand intent"