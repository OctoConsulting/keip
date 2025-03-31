import logging
from typing import Mapping, List

_LOGGER = logging.getLogger(__name__)


def _new_certificate(obj) -> Mapping:
    metadata = obj["metadata"]

    name = metadata["name"]

    namespace = metadata["namespace"]

    annotations = metadata.get("annotations", None)
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

    cluster_issuer = annotations.get("cert-manager.io/cluster-issuer", None)
    if cluster_issuer is None:
        _LOGGER.error(
            "IntegrationRoute does not contain metadata.annotations.cert-manager.io/cluster-issuer"
        )
        return {}

    alt_names = _get_annotation_vals_as_list(
        annotations.get("cert-manager.io/alt-names")
    )
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

    dns_names = [
        f"{common_name}.{namespace}.svc.cluster.local",
        f"{common_name}.{namespace}.svc",
        f"{common_name}.{namespace}",
        common_name,
        f"{name}-actuator.{namespace}.svc.cluster.local",
    ]
    dns_names = dns_names + alt_names

    subject = {}
    if organizational_units:
        subject["organizationalUnits"] = organizational_units

    if countries:
        subject["countries"] = countries

    if provinces:
        subject["provinces"] = provinces

    if localities:
        subject["localities"] = localities

    keystore_type = _get_keystore_type(obj)
    password_secret_ref_name = _get_password_secret_ref_name(obj)

    cert = {
        "apiVersion": "cert-manager.io/v1",
        "kind": "Certificate",
        "metadata": {
            "name": f"{name}-certs",
            "namespace": namespace,
        },
        "spec": {
            "commonName": f"{common_name}.{namespace}",
            "dnsNames": dns_names,
            "issuerRef": {
                "group": "cert-manager.io",
                "kind": "ClusterIssuer",
                "name": cluster_issuer,
            },
            "keystores": {
                keystore_type: {
                    "create": True,
                    "passwordSecretRef": {
                        "key": "password",
                        "name": password_secret_ref_name,
                    },
                }
            },
            "secretName": f"{name}-certstore",
            "subject": subject,
        },
    }

    return cert


def _get_annotation_vals_as_list(annotation_val) -> List:
    return (
        [val for i in annotation_val.split(",") if (val := i.strip())]
        if annotation_val
        else []
    )


def _get_keystore_type(obj) -> str:
    return obj["spec"]["tls"]["keystore"]["type"]


def _get_password_secret_ref_name(obj) -> str:
    return obj["spec"]["tls"]["keystore"]["passwordSecretRef"]


def sync_certificate(body) -> Mapping:
    # Request API at for DecoratorController at https://metacontroller.github.io/metacontroller/api/decoratorcontroller.html#sync-hook-request
    obj = body["object"]
    certificate = _new_certificate(obj)
    attachments = [certificate] if certificate else []
    desired_state = {"status": {}, "attachments": attachments}
    _LOGGER.debug("\n\nDesired state:\n%s", desired_state)
    return desired_state
