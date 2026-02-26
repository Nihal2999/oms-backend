from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_open():
    response = client.get("/app")
    assert response.status_code == 200
    assert response.json() == {"status": "Welcome to OMS Backend API!"}