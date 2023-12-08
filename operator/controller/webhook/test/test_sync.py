import copy
import json
from typing import Mapping

import pytest

from webhook.introute.sync import (
    sync,
    VolumeConfig,
    _get_updated_props_srcs,
    _spring_cloud_k8s_config,
    SECRETS_ROOT,
    _new_deployment,
)


def test_empty_parent_raises_exception(full_route):
    with pytest.raises(KeyError):
        sync({})


def test_full_integration_route(full_route):
    response = load_json("json/full-response.json")
    actual = sync(full_route)

    assert response == actual


def test_vol_config_missing_route_map_raise_exception(full_route):
    del full_route["parent"]["spec"]["routeConfigMap"]
    with pytest.raises(KeyError):
        VolumeConfig(full_route["parent"]["spec"])


def test_vol_config_missing_secrets_and_pvcs(full_route):
    del full_route["parent"]["spec"]["secretSources"]
    del full_route["parent"]["spec"]["persistentVolumeClaims"]
    vol_conf = VolumeConfig(full_route["parent"]["spec"])

    route_vol = {
        "name": "integration-route-config",
        "configMap": {"name": "testroute-xml"},
    }
    route_mnt = {"name": "integration-route-config", "mountPath": "/var/spring/xml"}

    assert vol_conf.get_volumes() == [route_vol]
    assert vol_conf.get_mounts() == [route_mnt]


def test_spring_app_config_json_missing_props_sources(full_route):
    del full_route["parent"]["spec"]["propSources"]

    spring_conf = _spring_cloud_k8s_config(full_route)

    assert spring_conf["spring"]["cloud"]["kubernetes"]["secrets"] == {
        "paths": SECRETS_ROOT
    }


def test_spring_app_config_json_missing_secret_sources(full_route):
    del full_route["parent"]["spec"]["secretSources"]

    spring_conf = _spring_cloud_k8s_config(full_route)

    assert spring_conf["spring"]["cloud"]["kubernetes"]["config"]["sources"] is not None


def test_spring_app_config_json_missing_props_and_secret_sources(full_route):
    del full_route["parent"]["spec"]["propSources"]
    del full_route["parent"]["spec"]["secretSources"]

    spring_conf = _spring_cloud_k8s_config(full_route)

    assert spring_conf is None


def test_update_props_missing_configmaps(full_route):
    updated_props = _get_updated_props_srcs(
        {}, full_route["parent"]["spec"]["propSources"]
    )

    assert updated_props == []


def test_update_props_missing_props(full_route):
    updated_props = _get_updated_props_srcs(full_route["related"]["ConfigMap.v1"], {})

    assert updated_props == []


def test_update_props_with_duplicates(full_route):
    """Duplicates refers to the scenario where a configmap has a matching
    basename as well as a matching label"""

    updated_props = _get_updated_props_srcs(
        full_route["related"]["ConfigMap.v1"],
        full_route["parent"]["spec"]["propSources"],
    )

    assert len(updated_props) == 1


def test_pod_template_no_annotations(full_route):
    del full_route["parent"]["spec"]["annotations"]

    deployment = _new_deployment(full_route)

    pod_template = deployment["spec"]["template"]
    assert pod_template["metadata"].get("annotations") is None


def test_pod_template_empty_annotations(full_route):
    full_route["parent"]["spec"]["annotations"] = {}

    deployment = _new_deployment(full_route)

    pod_template = deployment["spec"]["template"]
    assert pod_template["metadata"].get("annotations") is None


def test_pod_template_no_props_and_secrets_spring_config_not_present(full_route):
    del full_route["parent"]["spec"]["propSources"]
    del full_route["parent"]["spec"]["secretSources"]

    deployment = _new_deployment(full_route)

    pod_template = deployment["spec"]["template"]
    container = pod_template["spec"]["containers"][0]
    assert container.get("env") is None


def test_deployment_missing_labels(full_route):
    del full_route["parent"]["spec"]["labels"]

    deployment = _new_deployment(full_route)

    labels = deployment["metadata"]["labels"]
    assert len(labels) > 0


def test_deployment_empty_labels(full_route):
    full_route["parent"]["spec"]["labels"] = {}

    deployment = _new_deployment(full_route)

    labels = deployment["metadata"]["labels"]
    assert len(labels) > 0


@pytest.fixture()
def full_route(full_route_load: dict):
    return copy.deepcopy(full_route_load)


@pytest.fixture(scope="module")
def full_route_load() -> Mapping:
    return load_json("json/full-iroute-request.json")


def load_json(filepath: str) -> Mapping:
    with open(filepath, "r") as f:
        return json.load(f)
