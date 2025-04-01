import pytest
from fastapi.testclient import TestClient
from url_shortener.app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    # Предполагается, что root возвращает основную информацию о сервисе
    assert response.status_code == 200

def test_create_link_invalid_url():
    # Пример невалидного URL
    response = client.post("/links/shorten", json={"original_url": "not-a-valid-url"})
    assert response.status_code == 422  # Unprocessable Entity
