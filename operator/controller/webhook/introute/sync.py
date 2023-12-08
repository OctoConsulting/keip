import json
import logging
from pathlib import Path
from typing import List, Mapping, Optional
from datetime import datetime

from webhook import config as cfg

_LOGGER = logging.getLogger(__name__)

SECRETS_ROOT = "/etc/secrets"

CM_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class VolumeConfig:
    """
    Handles creating a pod's volumes and volumeMounts based on the following IntegrationRoute inputs:
        - routeConfigMap
        - secretSources
        - persistentVolumeClaims
    """

    _route_vol_name = "integration-route-config"

    def __init__(self, parent_spec) -> None:
        self._route_config = parent_spec["routeConfigMap"]
        self._secret_srcs = parent_spec.get("secretSources", [])
        self._pvcs = parent_spec.get("persistentVolumeClaims", [])

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

        return volume_mounts


def _get_updated_props_srcs(related_configmaps, props_srcs) -> List:
    """Replaces each props_src name with the latest ConfigMap based on creationTimestamp and prop_src base name"""
    updated_props = []

    if not props_srcs or not related_configmaps:
        _LOGGER.debug(
            f"Either props_srcs or configmaps were missing\n Props Sources: {props_srcs} \nConfigmaps: {related_configmaps}"
        )
        return updated_props

    for prop_src in props_srcs:
        matching_configmaps = {}
        for cm_name, cm in related_configmaps.items():
            if "name" in prop_src and prop_src["name"] in cm_name:
                matching_configmaps[cm_name] = cm
            elif "labels" in prop_src:
                labels = prop_src["labels"]
                for label in labels:
                    if (
                        label in cm["metadata"]["labels"].keys()
                        and labels[label] == cm["metadata"]["labels"][label]
                    ):
                        matching_configmaps[cm_name] = cm
        if not matching_configmaps:
            # No updates
            continue

        # Get the most recent Configmap
        updated_cm = max(
            matching_configmaps.values(),
            key=lambda cm: datetime.strptime(
                cm["metadata"]["creationTimestamp"], CM_DATETIME_FORMAT
            ),
        )

        _LOGGER.debug(f"Updated ConfigMap: {updated_cm}")
        updated_prop = {"name": updated_cm["metadata"]["name"]}
        if updated_prop not in updated_props:
            updated_props.append(updated_prop)

    _LOGGER.info(f"Updated Props: {updated_props}")
    return updated_props


def _spring_cloud_k8s_config(observed) -> Optional[Mapping]:
    """Generates the spring-cloud-kubernetes config that's passed as an env var to the Spring app"""
    parent = observed["parent"]
    metadata = parent["metadata"]
    props_srcs = parent["spec"].get("propSources")
    secret_srcs = parent["spec"].get("secretSources")
    _LOGGER.info(observed)
    related_configmaps = observed["related"]["ConfigMap.v1"]

    if not props_srcs and not secret_srcs:
        return None

    props_srcs = _get_updated_props_srcs(related_configmaps, props_srcs)

    return {
        "spring": {
            "config.import": "kubernetes:",
            "application": {"name": metadata["name"]},
            "cloud": {
                "kubernetes": {
                    "config": {
                        "fail-fast": True,
                        "namespace": metadata["namespace"],
                        "sources": props_srcs,
                    },
                    "secrets": {"paths": SECRETS_ROOT},
                }
            },
        }
    }


def _create_pod_template(observed, labels, integration_image):
    """TODO: Should add some resource constraints for containers. Add constraint values to CRD."""

    parent = observed["parent"]
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

    spring_app_config = _spring_cloud_k8s_config(observed)
    if spring_app_config:
        pod_template["spec"]["containers"][0]["env"] = [
            {
                "name": "SPRING_APPLICATION_JSON",
                "value": json.dumps(spring_app_config),
            }
        ]

    return pod_template


def _new_deployment(observed):
    parent = observed["parent"]
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
                observed, labels, cfg.INTEGRATION_CONTAINER_IMAGE
            ),
        },
    }

    return deployment


def _gen_children(observed) -> List[Mapping]:
    return [_new_deployment(observed)]


def sync(observed) -> Mapping:
    # Status can be filled in with useful about the state of managed children
    # (e.g. number of children pods currently running)
    _LOGGER.debug("Observed state:\n%s", observed)
    desired_state = {"status": {}, "children": _gen_children(observed)}
    _LOGGER.debug("Desired state response:\n%s", desired_state)
    return desired_state
