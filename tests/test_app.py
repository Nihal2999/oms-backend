from fastapi.testclient import TestClient

client = TestClient()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}