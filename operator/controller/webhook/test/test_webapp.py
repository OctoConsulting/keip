import pytest
from starlette.testclient import TestClient

from webhook.app import app
from webhook.test.test_sync import load_json


def test_status_endpoint(test_client):
    response = test_client.get('/status')

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_sync_endpoint_success(test_client):
    request = load_json("json/full-iroute-request.json")
    request = request | {
        "controller": {},
        "children": [],
        "related": [],
        "finalizing": False,
    }

    response = test_client.post("/sync", json=request)
    expected = load_json("json/full-response.json")

    assert expected == response.json()
    assert response.status_code == 200


def test_sync_endpoint_invalid_json(test_client):
    response = test_client.post("/sync", json=None)

    assert response.status_code == 400


def test_sync_endpoint_empty_body(test_client):
    response = test_client.post("/sync", json={})

    assert response.status_code == 400


@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)
