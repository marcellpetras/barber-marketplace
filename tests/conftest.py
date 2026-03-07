import pytest
from fastapi.testclient import TestClient
import os




#dummy variables setting since they are validated at import
os.environ["SUPABASE_URL"] = "testurl"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["OPENAI_MODEL"] = "gpt-5-nano"

from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)



@pytest.fixture
def client():
    return TestClient(app)