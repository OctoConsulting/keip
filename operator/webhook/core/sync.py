import json
from pathlib import PurePosixPath
from typing import List, Mapping, Optional, Any

from webhook import config as cfg

SECRETS_ROOT = "/etc/secrets"

TRUSTSTORE_PATH = "/etc/cabundle"

KEYSTORE_PATH = "/etc/keystore"

HTTPS_PORT = 8443

HTTP_PORT = 8080

ACTUATOR_CONFIG_BLOCK = {
    "management": {
        "endpoint": {"health": {"enabled": True}, "prometheus": {"enabled": True}},
        "endpoints": {"web": {"exposure": {"include": "health,prometheus"}}},
    }
}


class VolumeConfig:
    """
    Handles creating a pod's volumes and volumeMounts based on the following IntegrationRoute inputs:
        - annotations
        - labels
        - routeConfigMap
        - propSources
        - secretSources
        - configMaps
        - env
        - envFrom
        - resources
        - replicas
        - persistentVolumeClaims
        - tls
        - services
    """

    _route_vol_name = "integration-route-config"
    _tls_truststore_name = "truststore"
    _tls_keystore_name = "keystore"

    def __init__(self, parent_spec) -> None:
        self._route_config = parent_spec["routeConfigMap"]
        self._secret_srcs = parent_spec.get("secretSources", [])
        self._pvcs = parent_spec.get("persistentVolumeClaims", [])
        self._config_maps = parent_spec.get("configMaps", [])
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

        for cm_spec in self._config_maps:
            volumes.append(
                {"name": cm_spec["name"], "configMap": {"name": cm_spec["name"]}}
            )

        if self._tls_config:
            truststore = self._tls_config.get("truststore")
            if truststore:
                volumes.append(
                    {
                        "name": self._tls_truststore_name,
                        "configMap": {
                            "name": truststore["configMapName"],
                            "items": [
                                {
                                    "key": truststore["key"],
                                    "path": truststore["key"],
                                }
                            ],
                        },
                    }
                )

            keystore = self._tls_config.get("keystore")
            if keystore:
                keystore_type = _get_keystore_type(keystore)
                volumes.append(
                    {
                        "name": self._tls_keystore_name,
                        "secret": {
                            "secretName": keystore[keystore_type]["secretName"],
                            "items": [
                                {
                                    "key": keystore[keystore_type]["key"],
                                    "path": keystore[keystore_type]["key"],
                                }
                            ],
                        },
                    }
                )

        return volumes

    def get_mounts(self) -> List[dict]:
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
                    "mountPath": str(PurePosixPath(SECRETS_ROOT, secret)),
                }
            )

        for pvc_spec in self._pvcs:
            volume_mounts.append(
                {
                    "name": pvc_spec["claimName"],
                    "mountPath": pvc_spec["mountPath"],
                }
            )

        for cm_spec in self._config_maps:
            volume_mounts.append(
                {
                    "name": cm_spec["name"],
                    "mountPath": cm_spec["mountPath"],
                }
            )
        if self._tls_config:
            if self._tls_config.get("truststore"):
                volume_mounts.append(
                    {
                        "name": self._tls_truststore_name,
                        "readOnly": True,
                        "mountPath": TRUSTSTORE_PATH,
                    }
                )
            if self._tls_config.get("keystore"):
                volume_mounts.append(
                    {
                        "name": self._tls_keystore_name,
                        "readOnly": True,
                        "mountPath": KEYSTORE_PATH,
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


def _get_server_ssl_config(parent) -> Optional[Mapping]:
    tls_config = parent["spec"].get("tls")
    if not tls_config:
        return None

    keystore = tls_config.get("keystore")

    if not keystore:
        return None

    if "jks" in keystore:
        alias = keystore["jks"].get("alias", "certificate")
        return {
            "ssl": {
                "key-alias": alias,
                "key-store": str(PurePosixPath(KEYSTORE_PATH, keystore["jks"]["key"])),
                "key-store-type": "JKS",
            },
            "port": HTTPS_PORT,
        }
    else:
        return {
            "ssl": {
                "key-alias": "1",
                "key-store": str(
                    PurePosixPath(KEYSTORE_PATH, keystore["pkcs12"]["key"])
                ),
                "key-store-type": "PKCS12",
            },
            "port": HTTPS_PORT,
        }


def _service_name_env_var(parent) -> Mapping[str, str]:
    return {"name": "SERVICE_NAME", "value": parent["metadata"]["name"]}


def _get_keystore_type(keystore) -> str:
    return "jks" if "jks" in keystore else "pkcs12"


def _spring_app_config_env_var(parent) -> Optional[Mapping]:
    metadata = parent["metadata"]
    app_config = {
        "spring": {
            "application": {"name": metadata["name"]},
        }
    }

    if tls_config := _get_server_ssl_config(parent):
        app_config["server"] = tls_config

    if cloud_config := _spring_cloud_k8s_config(parent):
        app_config["spring"]["config.import"] = "kubernetes:"
        app_config["spring"]["cloud"] = cloud_config

    app_config.update(ACTUATOR_CONFIG_BLOCK)

    return {
        "name": "SPRING_APPLICATION_JSON",
        "value": json.dumps(app_config),
    }


def _get_keystore_password_env(tls) -> Mapping[str, Any]:

    keystore = tls.get("keystore")

    if not keystore:
        return {}

    keystore_type = _get_keystore_type(keystore)

    return {
        "name": "SERVER_SSL_KEYSTOREPASSWORD",
        "valueFrom": {
            "secretKeyRef": {
                "name": keystore[keystore_type]["passwordSecretRef"],
                "key": "password",
            }
        },
    }


def _get_java_jdk_options(tls) -> Optional[Mapping[str, str]]:

    truststore = tls.get("truststore")

    if not truststore:
        return None

    tls_type = truststore["type"]
    truststore_password = "changeit" if tls_type == "jks" else ""

    return {
        "name": "JDK_JAVA_OPTIONS",
        "value": f"-Djavax.net.ssl.trustStore={str(PurePosixPath(TRUSTSTORE_PATH, truststore['key']))} -Djavax.net.ssl.trustStorePassword={truststore_password} -Djavax.net.ssl.trustStoreType={tls_type.upper()}",
    }


def _generate_container_env_vars(parent) -> List[Mapping[str, str]]:
    env_vars = []

    if spring_app_config := _spring_app_config_env_var(parent):
        env_vars.append(spring_app_config)

    if tls := parent["spec"].get("tls"):
        if jdk_options := _get_java_jdk_options(tls):
            env_vars.append(jdk_options)

        if keystore_password_env := _get_keystore_password_env(tls):
            env_vars.append(keystore_password_env)

    env_vars.append(_service_name_env_var(parent))

    env_vars.extend(parent["spec"].get("env", []))

    return env_vars


def _create_pod_template(parent, labels, integration_image) -> Mapping[str, Any]:

    vol_config = VolumeConfig(parent["spec"])

    has_tls = _has_tls(parent)

    scheme = _get_scheme(has_tls).upper()
    management_port = _get_management_port(has_tls)

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
                            "port": management_port,
                            "scheme": scheme,
                        },
                        "failureThreshold": 3,
                        "timeoutSeconds": 3,
                    },
                    "readinessProbe": {
                        "httpGet": {
                            "path": "/actuator/health/readiness",
                            "port": management_port,
                            "scheme": scheme,
                        },
                        "failureThreshold": 2,
                        "timeoutSeconds": 3,
                    },
                    "startupProbe": {
                        "httpGet": {
                            "path": "/actuator/health/liveness",
                            "port": management_port,
                            "scheme": scheme,
                        },
                        "failureThreshold": 12,
                        "timeoutSeconds": 3,
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

    resources = parent["spec"].get("resources")
    if resources:
        pod_template["spec"]["containers"][0]["resources"] = resources
    else:
        pod_template["spec"]["containers"][0]["resources"] = {
            "requests": {"cpu": "500m", "memory": "1Gi"},
            "limits": {"memory": "2Gi"},
        }

    envFrom = parent["spec"].get("envFrom")
    if envFrom:
        pod_template["spec"]["containers"][0]["envFrom"] = envFrom

    return pod_template


def _new_deployment(parent):
    parent_metadata = parent["metadata"]

    autogenerated_labels = {
        "app.kubernetes.io/managed-by": "keip-integrationroute-controller",
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
            "annotations": parent["spec"].get("annotations", {}),
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


def _new_actuator_service(parent):
    parent_metadata = parent["metadata"]

    has_tls = _has_tls(parent)
    scheme = _get_scheme(has_tls)
    management_port = _get_management_port(has_tls)

    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "labels": {
                "integration-route": parent_metadata["name"],
                "prometheus-metrics-enabled": "true",
            },
            "name": f'{parent_metadata["name"]}-actuator',
        },
        "spec": {
            "ports": [
                {
                    "name": scheme,
                    "port": management_port,
                    "protocol": "TCP",
                    "targetPort": management_port,
                }
            ],
            "selector": {
                "app.kubernetes.io/instance": f'integrationroute-{parent_metadata["name"]}'
            },
        },
    }

    return service


def _has_tls(parent) -> bool:
    return "tls" in parent["spec"] and "keystore" in parent["spec"]["tls"]


def _get_scheme(has_tls) -> str:
    return "https" if has_tls else "http"


def _get_management_port(has_tls) -> int:
    return HTTPS_PORT if has_tls else HTTP_PORT


def _gen_children(parent) -> List[Mapping]:
    return [_new_deployment(parent), _new_actuator_service(parent)]


def sync(body) -> Mapping:
    # Request API at https://metacontroller.github.io/metacontroller/api/compositecontroller.html#sync-hook-request
    parent = body["parent"]
    # Status can be filled in with useful about the state of managed children
    desired_state = {"status": {}, "children": _gen_children(parent)}
    return desired_state
