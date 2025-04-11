import logging
from typing import Mapping, List, Any

_LOGGER = logging.getLogger(__name__)


def _new_certificate(obj) -> Mapping[str, Any]:
    metadata = obj["metadata"]

    name = metadata["name"]

    namespace = metadata["namespace"]

    annotations = metadata.get("annotations")
    if annotations is None:
        _LOGGER.debug(
            "IntegrationRoute does not contain metadata.annotations. No certificate will be generated."
        )
        return {}

    cert_manager_io_annotations = [
        annotation for annotation in annotations if "cert-manager.io" in annotation
    ]

    if not cert_manager_io_annotations:
        return {}

    common_name = annotations.get("cert-manager.io/common-name", name)

    issuer = _get_issuer_ref(annotations)
    if not issuer:
        return {}

    cert = {
        "apiVersion": "cert-manager.io/v1",
        "kind": "Certificate",
        "metadata": {
            "name": f"{name}-certs",
            "namespace": namespace,
        },
        "spec": {
            "commonName": f"{common_name}.{namespace}",
            "dnsNames": _get_dns_names(annotations, name, common_name, namespace),
            "issuerRef": issuer,
            "keystores": _get_keystores(obj["spec"]["tls"]["keystore"]),
            "secretName": f"{name}-certstore",
            "subject": _get_subject(annotations, name, common_name, namespace),
        },
    }

    return cert


def _get_dns_names(annotations, name, common_name, namespace) -> List[str]:
    alt_names = _get_annotation_vals_as_list(
        annotations.get("cert-manager.io/alt-names")
    )

    dns_names = [
        f"{common_name}.{namespace}.svc.cluster.local",
        f"{common_name}.{namespace}.svc",
        f"{common_name}.{namespace}",
        common_name,
        f"{name}-actuator.{namespace}.svc.cluster.local",
    ]
    dns_names = dns_names + alt_names
    return dns_names


def _get_issuer_ref(annotations) -> Mapping[str, str]:
    issuer = annotations.get("cert-manager.io/issuer")
    cluster_issuer = annotations.get("cert-manager.io/cluster-issuer")

    if issuer is not None and cluster_issuer is not None:
        _LOGGER.error(
            "IntegrationRoute cannot have metadata.annotations.cert-manager.io/issuer and metadata.annotations.cert-manager.io/cluster-issuer"
        )
        return {}

    if issuer is None and cluster_issuer is None:
        _LOGGER.error(
            "IntegrationRoute must have metadata.annotations.cert-manager.io/issuer or metadata.annotations.cert-manager.io/cluster-issuer"
        )
        return {}

    if issuer is not None:
        issuer_kind = "Issuer"
    else:
        issuer_kind = "ClusterIssuer"
        issuer = cluster_issuer

    return {
        "group": "cert-manager.io",
        "kind": issuer_kind,
        "name": issuer,
    }


def _get_subject(annotations, name, common_name, namespace) -> Mapping[str, List[str]]:
    organizational_units = _get_annotation_vals_as_list(
        annotations.get("cert-manager.io/subject-organizationalunits")
    )
    countries = _get_annotation_vals_as_list(
        annotations.get("cert-manager.io/subject-countries")
    )
    provinces = _get_annotation_vals_as_list(
        annotations.get("cert-manager.io/subject-provinces")
    )
    localities = _get_annotation_vals_as_list(
        annotations.get("cert-manager.io/subject-localities")
    )

    subject = {}
    if organizational_units:
        subject["organizationalUnits"] = organizational_units

    if countries:
        subject["countries"] = countries

    if provinces:
        subject["provinces"] = provinces

    if localities:
        subject["localities"] = localities

    return subject


def _get_keystores(keystore) -> Mapping[str, Mapping[str, Any]]:
    keystore_type = _get_keystore_type(keystore)
    password_secret_ref_name = keystore[keystore_type]["passwordSecretRef"]

    return {
        keystore_type: {
            "create": True,
            "passwordSecretRef": {
                "key": "password",
                "name": password_secret_ref_name,
            },
        },
    }


def _get_annotation_vals_as_list(annotation_val) -> List[str]:
    return (
        [val for i in annotation_val.split(",") if (val := i.strip())]
        if annotation_val
        else []
    )


def _get_keystore_type(keystore) -> str:
    return "jks" if "jks" in keystore else "pkcs12"


def sync_certificate(body) -> Mapping[str, List[Mapping[str, Any]]]:
    # Request API at for DecoratorController at https://metacontroller.github.io/metacontroller/api/decoratorcontroller.html#sync-hook-request
    obj = body["object"]
    certificate = _new_certificate(obj)
    attachments = [certificate] if certificate else []
    desired_state = {"attachments": attachments}
    return desired_state
