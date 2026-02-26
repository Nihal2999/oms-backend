from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test():
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}