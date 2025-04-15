import json
import os
from typing import Mapping

import pytest
from starlette.testclient import TestClient

from webhook.app import app


def test_status_endpoint(test_client):
    response = test_client.get("/status")

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_sync_endpoint_success(test_client):
    request = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-route-request.json"
    )

    response = test_client.post("/sync", json=request)
    expected = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-route-response.json"
    )

    assert expected == response.json()
    assert response.status_code == 200


def test_sync_certificate_endpoint_success(test_client):
    request = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-cert-request.json"
    )

    response = test_client.post("/addons/certmanager/sync", json=request)
    expected = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-cert-response.json"
    )

    assert expected == response.json()
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint, status_code",
    [
        ("/sync", 400),
        ("/addons/certmanager/sync", 400),
    ],
)
def test_sync_endpoint_invalid_json(test_client, endpoint, status_code):
    response = test_client.post(endpoint, json=None)

    assert response.status_code == status_code


@pytest.mark.parametrize(
    "endpoint, status_code",
    [
        ("/sync", 400),
        ("/addons/certmanager/sync", 400),
    ],
)
def test_sync_endpoint_empty_body(test_client, endpoint, status_code):
    response = test_client.post(endpoint, json={})

    assert response.status_code == status_code


def load_json_as_dict(filepath: str) -> Mapping:
    with open(filepath, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)
