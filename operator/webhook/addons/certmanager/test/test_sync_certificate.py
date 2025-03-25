import copy
import json
import logging
import os
from typing import Mapping

import pytest

from webhook.addons.certmanager.main import (
    sync_certificate,
)

_LOGGER = logging.getLogger(__name__)


def test_sync_certificate(full_route):
    expected_desired_state_dict = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-response.json"
    )
    expected_desired_state_json = json.dumps(expected_desired_state_dict)

    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


def test_sync_certificate_no_route(full_route):
    full_route = {}
    with pytest.raises(KeyError):
        sync_certificate(full_route)


def test_sync_certificate_no_cert_manager_annotations(full_route):
    del full_route["object"]["metadata"]["annotations"]
    expected_desired_state_json = json.dumps({"status": {}, "attachments": []})
    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


def test_sync_certificate_no_alt_names(full_route):
    del full_route["object"]["metadata"]["annotations"]["cert-manager.io/alt-names"]
    expected_desired_state_dict = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-response.json"
    )
    expected_desired_state_dict["attachments"][0]["spec"]["dnsNames"].remove(
        "cloud-integration-route-actuator.testnamespace.svc.cluster.local"
    )
    expected_desired_state_json = json.dumps(expected_desired_state_dict)

    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


def test_sync_certificate_no_cluster_issuer(full_route):
    del full_route["object"]["metadata"]["annotations"][
        "cert-manager.io/cluster-issuer"
    ]
    expected_desired_state_json = json.dumps({"status": {}, "attachments": []})
    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


def test_sync_certificate_no_common_name(full_route):
    del full_route["object"]["metadata"]["annotations"]["cert-manager.io/common-name"]
    expected_desired_state_json = json.dumps({"status": {}, "attachments": []})
    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


def test_sync_certificate_no_organizational_units(full_route):
    del full_route["object"]["metadata"]["annotations"][
        "cert-manager.io/subject-organizationalunits"
    ]
    expected_desired_state_dict = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-response.json"
    )
    del expected_desired_state_dict["attachments"][0]["spec"]["subject"][
        "organizationalUnits"
    ]
    expected_desired_state_json = json.dumps(expected_desired_state_dict)

    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


def test_sync_certificate_no_countries(full_route):
    del full_route["object"]["metadata"]["annotations"][
        "cert-manager.io/subject-countries"
    ]
    expected_desired_state_dict = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-response.json"
    )
    del expected_desired_state_dict["attachments"][0]["spec"]["subject"]["countries"]
    expected_desired_state_json = json.dumps(expected_desired_state_dict)

    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


def test_sync_certificate_no_provinces(full_route):
    del full_route["object"]["metadata"]["annotations"][
        "cert-manager.io/subject-provinces"
    ]
    expected_desired_state_dict = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-response.json"
    )
    del expected_desired_state_dict["attachments"][0]["spec"]["subject"]["provinces"]
    expected_desired_state_json = json.dumps(expected_desired_state_dict)

    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


def test_sync_certificate_no_localities(full_route):
    del full_route["object"]["metadata"]["annotations"][
        "cert-manager.io/subject-localities"
    ]
    expected_desired_state_dict = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-response.json"
    )
    del expected_desired_state_dict["attachments"][0]["spec"]["subject"]["localities"]
    expected_desired_state_json = json.dumps(expected_desired_state_dict)

    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


def test_sync_certificate_jks_keystore(full_route):
    expected_desired_state_dict = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-response.json"
    )
    expected_desired_state_json = json.dumps(expected_desired_state_dict)

    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


def test_sync_certificate_pkcs12_keystore(full_route):
    full_route["object"]["spec"]["tls"]["keystore"]["key"] = "keystore.p12"
    full_route["object"]["spec"]["tls"]["keystore"][
        "passwordSecretRef"
    ] = "pkcs12-password"
    full_route["object"]["spec"]["tls"]["keystore"]["type"] = "pkcs12"
    expected_desired_state_dict = load_json_as_dict(
        f"{os.path.dirname(os.path.abspath(__file__))}/json/full-response.json"
    )
    del expected_desired_state_dict["attachments"][0]["spec"]["keystores"]["jks"]
    expected_desired_state_dict["attachments"][0]["spec"]["keystores"] = {
        "pkcs12": {
            "create": True,
            "passwordSecretRef": {"key": "password", "name": "pkcs12-password"},
        }
    }
    expected_desired_state_json = json.dumps(expected_desired_state_dict)

    actual_desired_state_json = json.dumps(sync_certificate(full_route))

    assert actual_desired_state_json == expected_desired_state_json


@pytest.fixture()
def full_route(full_route_load: dict):
    return copy.deepcopy(full_route_load)


@pytest.fixture(scope="module")
def full_route_load() -> Mapping:
    cwd = os.path.dirname(os.path.abspath(__file__))
    return load_json_as_dict(f"{cwd}/json/full-iroute-request.json")


def load_json_as_dict(filepath: str) -> Mapping:
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError as e:
        _LOGGER.error(f"File not found: {filepath}\n{e}")
