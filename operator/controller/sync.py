#!/usr/bin/env python

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List, Mapping

# TODO: Abstract configuration property resolution in a separate module
INTEGRATION_IMAGE = os.getenv("INTEGRATION_IMAGE", "keip-integration")


class VolumeConfig:
    _route_vol_name = "integration-route-config"
    _props_vol_name = "props-config"

    def __init__(self, parent_spec) -> None:
        self._route_config = parent_spec["routeConfigMap"]
        self._props_config = parent_spec.get("propsConfigMap")

    def get_volumes(self) -> List[Mapping]:
        volumes = [
            {
                "name": self._route_vol_name,
                "configMap": {
                    "name": self._route_config,
                },
            }
        ]

        if self._props_config is not None:
            volumes.append(
                {
                    "name": self._props_vol_name,
                    "configMap": {
                        "name": self._props_config,
                    },
                }
            )

        return volumes

    def get_mounts(self) -> List[Mapping]:
        volumeMounts = [
            {
                "name": self._route_vol_name,
                "mountPath": "/var/spring/xml",
            }
        ]

        if self._props_config is not None:
            volumeMounts.append(
                {
                    "name": self._props_vol_name,
                    "mountPath": "/var/spring/config",
                }
            )

        return volumeMounts


def create_pod_template(parent_spec, labels, integration_image):
    """TODO: Should add some resource constraints for containers. Add constraint values to CRD."""

    vol_config = VolumeConfig(parent_spec)

    return {
        "metadata": {"labels": labels},
        "spec": {
            "containers": [
                {
                    "name": "integration-app",
                    "image": integration_image,
                    "volumeMounts": vol_config.get_mounts(),
                }
            ],
            "volumes": vol_config.get_volumes(),
        },
    }


def new_deployment(parent):
    parent_metadata = parent["metadata"]
    parent_spec = parent["spec"]

    labels = {
        "app.kubernetes.io/managed-by": "integrationroute-controller",
        "app.kubernetes.io/name": "integrationroute",
        "app.kubernetes.io/instance": f'integrationroute-{parent_metadata["name"]}',
        "app.kubernetes.io/version": "latest",
    }

    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": f'{parent_metadata["name"]}',
            "labels": labels,
        },
        "spec": {
            "selector": {
                "matchLabels": {
                    "app.kubernetes.io/instance": labels["app.kubernetes.io/instance"]
                }
            },
            "replicas": parent_spec["replicas"],
            "template": create_pod_template(parent_spec, labels, INTEGRATION_IMAGE),
        },
    }

    return deployment


# TODO: Consider using a production-ready server rather than the built-in http.server
# TODO: Add some typing to request and response objects
class ServiceRouteController(BaseHTTPRequestHandler):
    def sync(self, parent):
        desired = {"status": {}, "children": []}
        desired["children"].append(new_deployment(parent))
        return desired

    def do_POST(self):
        try:
            observed = json.loads(
                self.rfile.read(int(self.headers.get("Content-Length")))
            )
            desired = self.sync(observed["parent"])
        except Exception as e:
            self.send_error(500, message=str(e))
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(desired).encode())


HTTPServer(("", 80), ServiceRouteController).serve_forever()
