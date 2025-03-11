import logging
import sys
import os
from typing import Mapping, List

_LOGGER = logging.getLogger(__name__)

from webhook.core.sync import sync


def _new_certificate(parent) -> Mapping:
    metadata = parent.get("metadata", None)
    if metadata is None:
        _LOGGER.error("IntegrationRoute does not contain metadata.")
        return {}

    annotations = metadata.get("annotations", None)
    if annotations is None:
        _LOGGER.error("IntegrationRoute does not contain metadata.annotations.")
        return {}

    cluster_issuer = annotations.get("cert-manager.io/cluster-issuer", None)
    if cluster_issuer is None:
        _LOGGER.error(
            "IntegrationRoute does not contain metadata.annotations.cert-manager.io/cluster-issuer"
        )
        return {}

    common_name = annotations.get("cert-manager.io/common-name", None)
    if common_name is None:
        _LOGGER.error(
            "IntegrationRoute does not contain metadata.annotations.cert-manager.io/common-name"
        )
        return {}

    keystore_type = _get_keystore_type(parent)
    password_secret_ref_name = _get_password_secret_ref_name(parent)

    alt_names = (
        annotations.get("cert-manager.io/alt-names").split(",")
        if annotations.get("cert-manager.io/alt-names", None) is not None
        else []
    )
    organizational_units = (
        annotations.get("cert-manager.io/subject-organizationalunits").split(",")
        if annotations.get("cert-manager.io/subject-organizationalunits", None)
        is not None
        else []
    )
    countries = (
        annotations.get("cert-manager.io/subject-countries").split(",")
        if annotations.get("cert-manager.io/subject-countries", None) is not None
        else []
    )
    provinces = (
        annotations.get("cert-manager.io/subject-provinces").split(",")
        if annotations.get("cert-manager.io/subject-provinces", None) is not None
        else []
    )
    localities = (
        annotations.get("cert-manager.io/subject-localities").split(",")
        if annotations.get("cert-manager.io/subject-localities", None) is not None
        else []
    )

    dns_names = [
        f"{annotations['cert-manager.io/common-name']}.{metadata['namespace']}.svc.cluster.local",
        f"{annotations['cert-manager.io/common-name']}.{metadata['namespace']}.svc",
        annotations["cert-manager.io/common-name"],
        f"{metadata['name']}-actuator.{metadata['namespace']}.svc.cluster.local",
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

    cert = {
        "apiVersion": "cert-manager.io/v1",
        "kind": "Certificate",
        "metadata": {
            "name": f"{metadata['name']}-certs",
            "namespace": metadata["namespace"],
        },
        "spec": {
            "commonName": f"{common_name}.{metadata['namespace']}",
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
            "secretName": f"{metadata['name']}-certstore",
            "subject": subject,
        },
    }

    return cert


def _get_keystore_type(parent) -> str:
    return parent["spec"]["tls"]["keystore"]["type"]


def _get_password_secret_ref_name(parent) -> str:
    return parent["spec"]["tls"]["keystore"]["passwordSecretRef"]


def sync_certificate(parent) -> Mapping:
    _LOGGER.debug("\n\nRequest:\n%s", parent)
    # Status can be filled in with useful information about the state of managed children
    # desired_state = {"status": {}, "children": [sync(parent), _new_certificate(parent)]}
    desired_state = {"status": {}, "children": [_new_certificate(parent)]}
    _LOGGER.debug("\n\nDesired state:\n%s", desired_state)
    return desired_state
