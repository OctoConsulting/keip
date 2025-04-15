from datetime import datetime
from typing import Mapping, List, MutableMapping

import pytest

import webhook.core.sync
from webhook.core.sync import (
    _compute_status,
    _get_status_ready_condition,
)

FIXED_ISO_TIMESTAMP = "2023-09-06T12:34:56Z"

STATUS_NOT_READY_CONDITION = {
    "lastTransitionTime": FIXED_ISO_TIMESTAMP,
    "message": "Some IntegrationRoute pod replicas are not ready",
    "reason": "ReplicasNotReady",
    "status": "False",
    "type": "Ready",
}

STATUS_READY_CONDITION = {
    "lastTransitionTime": FIXED_ISO_TIMESTAMP,
    "message": "All IntegrationRoute pod replicas are ready",
    "reason": "ReplicasReady",
    "status": "True",
    "type": "Ready",
}


def test_top_level_replica_status_fields(full_route):
    full_route["parent"]["spec"]["replicas"] = 3
    deployment_status = get_child_deployment(full_route)["status"]
    deployment_status["replicas"] = 2
    deployment_status["readyReplicas"] = 1

    status = _compute_status(full_route["parent"], full_route["children"])

    assert status["expectedReplicas"] == 3
    assert status["runningReplicas"] == 2
    assert status["readyReplicas"] == 1


def test_status_expected_vs_ready_replica_mismatch_results_in_unready_state(full_route):
    full_route["parent"]["spec"]["replicas"] = 3
    deployment_status = get_child_deployment(full_route)["status"]
    deployment_status["readyReplicas"] = 1

    status = _compute_status(full_route["parent"], full_route["children"])
    ready_condition = get_ready_condition(status["conditions"])

    assert status["expectedReplicas"] == 3
    assert status["readyReplicas"] == 1
    assert ready_condition["status"] == "False"


def test_status_with_no_active_child_deployment_use_defaults(full_route):
    del full_route["children"]["Deployment.apps/v1"]["testroute"]

    status = _compute_status(full_route["parent"], full_route["children"])

    expected_status = {
        "expectedReplicas": 2,
        "readyReplicas": 0,
        "runningReplicas": 0,
    }

    assert status == expected_status


def test_status_with_child_deployment_missing_status_field_use_defaults(full_route):
    deployment = get_child_deployment(full_route)
    del deployment["status"]

    status = _compute_status(full_route["parent"], full_route["children"])

    expected_status = {
        "expectedReplicas": 2,
        "readyReplicas": 0,
        "runningReplicas": 0,
    }

    assert status == expected_status


def test_status_with_child_deployment_missing_available_condition_ignored(full_route):
    deployment = get_child_deployment(full_route)
    deployment["status"]["conditions"] = [
        c for c in deployment["status"]["conditions"] if c["type"] != "Available"
    ]

    status = _compute_status(full_route["parent"], full_route["children"])
    conditions = status["conditions"]

    assert len(conditions) == 1
    assert conditions[0]["type"] == "Ready"


def test_status_with_child_deployment_missing_ready_replicas_field_default_to_unready(
    full_route,
):
    deployment = get_child_deployment(full_route)
    del deployment["status"]["readyReplicas"]

    status = _compute_status(full_route["parent"], full_route["children"])

    assert status["readyReplicas"] == 0


def test_ready_status_with_parent_missing_status_field_generate_new_status(
    patch_datetime,
):
    ready_condition = _get_status_ready_condition({}, False)

    assert ready_condition == STATUS_NOT_READY_CONDITION


def test_ready_status_with_parent_missing_ready_condition_generate_new_status(
    patch_datetime, full_route
):
    parent_status = full_route["parent"]["status"]

    parent_status["conditions"] = [
        c for c in full_route["parent"]["status"]["conditions"] if c["type"] != "Ready"
    ]

    ready_condition = _get_status_ready_condition(parent_status, True)

    assert ready_condition == STATUS_READY_CONDITION


@pytest.mark.parametrize(
    "computed_ready, parent_ready", [(True, "True"), (False, "False")]
)
def test_ready_status_with_parent_matching_ready_condition_reuse_parent_status(
    patch_datetime, full_route, computed_ready, parent_ready
):
    parent_status = full_route["parent"]["status"]
    parent_condition = get_ready_condition(parent_status["conditions"])
    parent_condition["status"] = parent_ready

    ready_condition = _get_status_ready_condition(parent_status, computed_ready)

    assert ready_condition == parent_condition


@pytest.mark.parametrize(
    "computed_ready, parent_ready", [(True, "False"), (False, "True")]
)
def test_ready_status_with_parent_different_ready_condition_generate_new_status(
    patch_datetime, full_route, computed_ready, parent_ready
):
    parent_status = full_route["parent"]["status"]
    parent_condition = get_ready_condition(parent_status["conditions"])
    parent_condition["status"] = parent_ready

    ready_condition = _get_status_ready_condition(parent_status, computed_ready)

    if computed_ready:
        assert ready_condition == STATUS_READY_CONDITION
    else:
        assert ready_condition == STATUS_NOT_READY_CONDITION


@pytest.fixture()
def patch_datetime(monkeypatch):
    monkeypatch.setattr(webhook.core.sync, "datetime", MockDateTime)


class MockDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime.fromisoformat(FIXED_ISO_TIMESTAMP)


def get_child_deployment(route_request: Mapping):
    return route_request["children"]["Deployment.apps/v1"]["testroute"]


def get_ready_condition(conditions: List[MutableMapping]) -> MutableMapping:
    return next(c for c in conditions if c["type"] == "Ready")
