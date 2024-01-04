import json
import logging
from pathlib import Path
from typing import List, Mapping, Optional

from webhook import config as cfg

_LOGGER = logging.getLogger(__name__)

SECRETS_ROOT = "/etc/secrets"

TRUSTSTORE_PATH = "/etc/cabundle"


class VolumeConfig:
    """
    Handles creating a pod's volumes and volumeMounts based on the following IntegrationRoute inputs:
        - routeConfigMap
        - secretSources
        - persistentVolumeClaims
    """

    _route_vol_name = "integration-route-config"
    _tls_vol_name = "truststore"

    def __init__(self, parent_spec) -> None:
        self._route_config = parent_spec["routeConfigMap"]
        self._secret_srcs = parent_spec.get("secretSources", [])
        self._pvcs = parent_spec.get("persistentVolumeClaims", [])
        self._tls_config = parent_spec.get("tls")

    def get_volumes(self) -> List[Mapping]:
        volumes = [
            {
                "name": self._route_vol_name,
                "configMap": {
                    "name": self._route_config,
                },
            }
        ]

        for secret in self._secret_srcs:
            volumes.append({"name": secret, "secret": {"secretName": secret}})

        for pvc_spec in self._pvcs:
            volumes.append(
                {
                    "name": pvc_spec["claimName"],
                    "persistentVolumeClaim": {"claimName": pvc_spec["claimName"]},
                }
            )

        if self._tls_config:
            volumes.append(
                {
                    "name": self._tls_vol_name,
                    "configMap": {
                        "name": self._tls_config["configMapName"],
                        "items": [
                            {
                                "key": self._tls_config["key"],
                                "path": self._tls_config["key"],
                            }
                        ],
                    },
                }
            )

        return volumes

    def get_mounts(self) -> List[Mapping]:
        volume_mounts = [
            {
                "name": self._route_vol_name,
                "mountPath": "/var/spring/xml",
            }
        ]

        for secret in self._secret_srcs:
            volume_mounts.append(
                {
                    "name": secret,
                    "readOnly": True,
                    "mountPath": str(Path(SECRETS_ROOT, secret)),
                }
            )

        for pvc_spec in self._pvcs:
            volume_mounts.append(
                {
                    "name": pvc_spec["claimName"],
                    "mountPath": pvc_spec["mountPath"],
                }
            )

        if self._tls_config:
            volume_mounts.append(
                {
                    "name": self._tls_vol_name,
                    "readOnly": True,
                    "mountPath": TRUSTSTORE_PATH,
                }
            )

        return volume_mounts


def _spring_cloud_k8s_config(parent) -> Optional[Mapping]:
    metadata = parent["metadata"]

    props_srcs = parent["spec"].get("propSources")
    secret_srcs = parent["spec"].get("secretSources")

    if not props_srcs and not secret_srcs:
        return None

    return {
        "kubernetes": {
            "config": {
                "fail-fast": True,
                "namespace": metadata["namespace"],
                "sources": props_srcs,
            },
            "secrets": {"paths": SECRETS_ROOT},
        }
    }


def _spring_app_config_env_var(parent) -> Mapping[str, str]:
    metadata = parent["metadata"]
    app_config = {
        "spring": {
            "application": {"name": metadata["name"]},
        }
    }

    if cloud_config := _spring_cloud_k8s_config(parent):
        app_config["spring"]["config.import"] = "kubernetes:"
        app_config["spring"]["cloud"] = cloud_config

    return {
        "name": "SPRING_APPLICATION_JSON",
        "value": json.dumps(app_config),
    }


def _get_java_jdk_options(parent) -> Optional[Mapping[str, str]]:
    tls_config = parent["spec"].get("tls")

    if not tls_config:
        return None

    tls_type = tls_config['type']
    assert tls_type in ["jks", "pkcs12"], \
        f"({tls_type}) is not a supported TLS type. Supported types: ('jks', 'pkcs12')"

    truststore_password = "changeit" if tls_type == "jks" else ""
    jdk_options = f"-Djavax.net.ssl.trustStore={str(Path(TRUSTSTORE_PATH, tls_config['key']))} -Djavax.net.ssl.trustStorePassword={truststore_password} -Djavax.net.ssl.trustStoreType={tls_type.upper()}"

    return {
        "name": "JDK_JAVA_OPTIONS",
        "value": jdk_options,
    }


def _generate_container_env_vars(parent) -> List[Mapping[str, str]]:
    env_vars = []

    if spring_app_config := _spring_app_config_env_var(parent):
        env_vars.append(spring_app_config)

    if jdk_options := _get_java_jdk_options(parent):
        env_vars.append(jdk_options)

    return env_vars


def _create_pod_template(parent, labels, integration_image):
    """TODO: Should add some resource constraints for containers. Add constraint values to CRD."""

    vol_config = VolumeConfig(parent["spec"])

    pod_template = {
        "metadata": {"labels": labels},
        "spec": {
            "serviceAccountName": "integrationroute-service",
            "containers": [
                {
                    "name": "integration-app",
                    "image": integration_image,
                    "volumeMounts": vol_config.get_mounts(),
                    "livenessProbe": {
                        "httpGet": {
                            "path": "/actuator/health/liveness",
                            "port": 8080,
                        },
                        "initialDelaySeconds": 10,
                    },
                    "readinessProbe": {
                        "httpGet": {
                            "path": "/actuator/health/readiness",
                            "port": 8080,
                        },
                        "initialDelaySeconds": 10,
                    },
                },
            ],
            "volumes": vol_config.get_volumes(),
        },
    }

    annotations = parent["spec"].get("annotations")
    if annotations:
        pod_template["metadata"]["annotations"] = annotations

    pod_template["spec"]["containers"][0]["env"] = _generate_container_env_vars(parent)

    return pod_template


def _new_deployment(parent):
    parent_metadata = parent["metadata"]

    autogenerated_labels = {
        "app.kubernetes.io/managed-by": "integrationroute-controller",
        "app.kubernetes.io/name": "integrationroute",
        "app.kubernetes.io/instance": f'integrationroute-{parent_metadata["name"]}',
        "app.kubernetes.io/version": "latest",
    }

    labels = autogenerated_labels | parent["spec"].get("labels", {})

    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": parent_metadata["name"],
            "labels": labels,
        },
        "spec": {
            "selector": {
                "matchLabels": {
                    "app.kubernetes.io/instance": labels["app.kubernetes.io/instance"]
                }
            },
            "replicas": parent["spec"]["replicas"],
            "template": _create_pod_template(
                parent, labels, cfg.INTEGRATION_CONTAINER_IMAGE
            ),
        },
    }

    return deployment


def _gen_children(parent) -> List[Mapping]:
    return [_new_deployment(parent)]


def sync(parent) -> Mapping:
    # Status can be filled in with useful about the state of managed children
    # (e.g. number of children pods currently running)
    _LOGGER.debug("Integration Route from request:\n%s", parent)
    desired_state = {"status": {}, "children": _gen_children(parent)}
    _LOGGER.debug("Desired state response:\n%s", desired_state)
    return desired_state
