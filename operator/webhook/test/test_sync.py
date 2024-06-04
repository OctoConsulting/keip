import copy
import json
from typing import Mapping

import pytest

from webhook.introute.sync import (
    sync,
    VolumeConfig,
    _spring_cloud_k8s_config,
    SECRETS_ROOT,
    _new_deployment,
    _spring_app_config_env_var,
    _get_java_jdk_options,
    _generate_container_env_vars
    
)

JDK_OPTIONS_ENV_NAME = "JDK_JAVA_OPTIONS"

def test_empty_parent_raises_exception(full_route):
    with pytest.raises(KeyError):
        sync({})


def test_full_integration_route(full_route):
    response = load_json("json/full-response.json")
    actual = sync(full_route)

    assert response == actual


def test_vol_config_missing_route_map_raise_exception(full_route):
    del full_route["spec"]["routeConfigMap"]
    with pytest.raises(KeyError):
        VolumeConfig(full_route["spec"])


def test_vol_config_missing_optional_vols_no_fail(full_route):
    del full_route["spec"]["secretSources"]
    del full_route["spec"]["persistentVolumeClaims"]
    del full_route["spec"]["configMaps"]
    vol_conf = VolumeConfig(full_route["spec"])

    assert len(vol_conf.get_volumes()) > 0
    assert len(vol_conf.get_mounts()) > 0


def test_spring_app_config_json_missing_props_sources(full_route):
    del full_route["spec"]["propSources"]

    spring_conf = _spring_cloud_k8s_config(full_route)

    assert spring_conf["kubernetes"]["secrets"] == {"paths": SECRETS_ROOT}


def test_spring_app_config_json_missing_secret_sources(full_route):
    del full_route["spec"]["secretSources"]

    spring_conf = _spring_cloud_k8s_config(full_route)

    assert spring_conf["kubernetes"]["config"]["sources"] is not None


def test_spring_app_config_json_missing_props_and_secret_sources(full_route):
    del full_route["spec"]["propSources"]
    del full_route["spec"]["secretSources"]

    spring_conf = _spring_app_config_env_var(full_route)
    json_props = json.loads(spring_conf["value"])

    assert spring_conf["name"] == "SPRING_APPLICATION_JSON"

    expected_json = {"spring": {"application": {"name": "testroute"}}, "server": {"ssl": {"key-alias": "certificate", "key-store": "/etc/keystore/test-keystore.jks", "key-store-type": "JKS"}, "port": 8443}}

    assert json_props == expected_json


def test_pod_template_no_annotations(full_route):
    del full_route["spec"]["annotations"]

    deployment = _new_deployment(full_route)

    pod_template = deployment["spec"]["template"]
    assert pod_template["metadata"].get("annotations") is None


def test_pod_template_empty_annotations(full_route):
    full_route["spec"]["annotations"] = {}

    deployment = _new_deployment(full_route)

    pod_template = deployment["spec"]["template"]
    assert pod_template["metadata"].get("annotations") is None


def test_pod_template_no_tls(full_route):
    del full_route["spec"]["tls"]

    deployment = _new_deployment(full_route)

    check_pod_probe_protocol(deployment, "HTTP", 8080)
    check_volume_absent(deployment, "truststore")
    check_volume_mounts_absent(deployment, "truststore")
    check_volume_absent(deployment, "keystore")
    check_volume_mounts_absent(deployment, "keystore")


def test_pod_template_no_truststore(full_route):
    del full_route["spec"]["tls"]["truststore"]

    deployment = _new_deployment(full_route)

    check_pod_probe_protocol(deployment, "HTTPS", 8443)
    check_volume_absent(deployment, "truststore")
    check_volume_mounts_absent(deployment, "truststore")


def test_pod_template_no_keystore(full_route):
    del full_route["spec"]["tls"]["keystore"]

    deployment = _new_deployment(full_route)

    check_pod_probe_protocol(deployment, "HTTP", 8080)
    check_volume_absent(deployment, "keystore")
    check_volume_mounts_absent(deployment, "keystore")


def test_jdk_options_pkcs12_type(full_route):
    tls_config = full_route["spec"]["tls"]
    options = _get_java_jdk_options(tls_config)

    assert options["name"] == JDK_OPTIONS_ENV_NAME

    expected_options = "-Djavax.net.ssl.trustStore=/etc/cabundle/test-truststore.p12 -Djavax.net.ssl.trustStorePassword= -Djavax.net.ssl.trustStoreType=PKCS12"
    assert options["value"] == expected_options


def test_jdk_options_jks_type(full_route):
    tls_config = full_route["spec"]["tls"]
    tls_config["truststore"]["type"] = "jks"
    tls_config["truststore"]["key"] = "test-truststore.jks"

    options = _get_java_jdk_options(tls_config)
    assert options["name"] == JDK_OPTIONS_ENV_NAME

    expected_options = "-Djavax.net.ssl.trustStore=/etc/cabundle/test-truststore.jks -Djavax.net.ssl.trustStorePassword=changeit -Djavax.net.ssl.trustStoreType=JKS"
    assert options["value"] == expected_options


def test_env_vars_no_keystore(full_route):
    del full_route["spec"]["tls"]["keystore"]

    options = _generate_container_env_vars(full_route)

    assert not any(x for x in options if x.get('name') == 'SERVER_SSL_KEYSTOREPASSWORD')


def test_deployment_missing_labels(full_route):
    del full_route["spec"]["labels"]

    deployment = _new_deployment(full_route)

    labels = deployment["metadata"]["labels"]
    assert len(labels) > 0


def test_deployment_empty_labels(full_route):
    full_route["spec"]["labels"] = {}

    deployment = _new_deployment(full_route)

    labels = deployment["metadata"]["labels"]
    assert len(labels) > 0


def test_deployment_missing_annotations(full_route):
    del full_route["spec"]["annotations"]

    deployment = _new_deployment(full_route)

    assert "annotations" in deployment["metadata"]
    annotations = deployment["metadata"]["annotations"]
    assert len(annotations) == 0


def test_deployment_empty_annotations(full_route):
    full_route["spec"]["annotations"] = {}

    deployment = _new_deployment(full_route)

    assert "annotations" in deployment["metadata"]
    annotations = deployment["metadata"]["annotations"]
    assert len(annotations) == 0


@pytest.fixture()
def full_route(full_route_load: dict):
    return copy.deepcopy(full_route_load["parent"])


@pytest.fixture(scope="module")
def full_route_load() -> Mapping:
    return load_json("json/full-iroute-request.json")


def load_json(filepath: str) -> Mapping:
    with open(filepath, "r") as f:
        return json.load(f)


def check_env_var_absent(deployment: Mapping, name: str):
    container = get_container(deployment)
    env_var_names = [env_var["name"] for env_var in container.get("env")]
    assert name not in env_var_names


def check_volume_absent(deployment: Mapping, name: str):
    vols = deployment["spec"]["template"]["spec"]["volumes"]
    vol_names = [v["name"] for v in vols]
    assert name not in vol_names

def check_pod_probe_protocol(deployment: Mapping, scheme: str, port: int):
    liveness_probe = get_container(deployment)["livenessProbe"]
    readiness_probe = get_container(deployment)["readinessProbe"]

    assert liveness_probe["httpGet"]["port"] == port
    assert liveness_probe["httpGet"]["scheme"] == scheme

    assert readiness_probe["httpGet"]["port"] == port
    assert readiness_probe["httpGet"]["scheme"] == scheme


def check_volume_mounts_absent(deployment: Mapping, name: str):
    mounts = get_container(deployment)["volumeMounts"]
    mnt_names = [m["name"] for m in mounts]
    assert name not in mnt_names


def get_container(deployment: Mapping) -> Mapping:
    pod_template = deployment["spec"]["template"]
    return pod_template["spec"]["containers"][0]
