# Example: TLS-enabled Integration Route with Cert-Manager Addon

Deploys a pod that runs a simple Spring Integration web server with a `greeting` endpoint. The example server is secured
with TLS out-of-the-box with help from keip's cert-manager addon controller.

## Prerequisites

- Follow the first part of the [Getting Started](..%2F..%2F..%2FREADME.md#getting-started) guide to install the keip
  controller.

## Run the example

Install `cert-manager`

```shell
kubectl apply -k certmanager
```

Install the `cert-manager` addon controller (from the `operator/` directory)

```shell
make -f ../../Makefile addons/certmanager/deploy
```

Install the `ClusterIssuer`

```shell
kubectl apply -k certmanager/issuer
```

*_Note_*: If the creating of the `ClusterIssuer` fails, wait a bit for cert-manager to be ready and try again.

Install the example `IntegrationRoute`

```shell
kubectl apply -k .
```

*_Note_*: The example uses a `keystore.p12` file and a certificate created by [Cert Manager](https://cert-manager.io/).

This should result in the creation of the following resources:

- IntegrationRoute `keip.octo.com/v1alpha1/testroute`: The custom resource representing a Spring Integration
  application.
- ConfigMap `testroute-xml`: Contains the Spring Integration XML configuration.
- Secret `pkcs12-password`: Password to the PKCS12 keystore.
- Service `testroute`: Exposes the web server endpoint.
- Cluster Issuer `clusterissuer.cert-manager.io/test-selfsigned`: A self-signed `cert-manager.io/v1/ClusterIssuer` used
  to sign certificates.
- Managed by keip controllers:
    - Deployment `testroute`: Starts up pods running the `keip-integration`
      image (configured in the `keip-controller-props` ConfigMap) and executes the provided integration logic.
    - Secret `testroute-certstore`: Private key and certificate signed by the denoted issuer.
    - Service `testroute-actuator`: Exposes the Spring Actuator.
    - Certificate `testroute-certs`: A `certificate.cert-manager.io/Certificate`
      resource that creates the `testroute-certstore` `Secret`.

Check that pod `testroute` is `Running` and `1/1` is ready:

```shell
kubectl get pods -l app.kubernetes.io/instance=integrationroute-testroute

NAME                         READY   STATUS    RESTARTS   AGE
testroute-74d574bf85-tbv9m   1/1     Running   0          99s
```

*_Note_*: Cert Manager takes a few seconds to create the certificate and keystore secret. The testroute pod will not
start until the `keystore.p12` secret is available to mount.

Describe the `Certificate`:

```shell
kubectl describe certificate testroute-certs
```

Get the `Secrets`:

```shell
kubectl get secrets
NAME                  TYPE                DATA   AGE
pkcs12-password       Opaque              1      109s
testroute-certstore   kubernetes.io/tls   5      107s
```

Describe the `IntegrationRoute`:

```shell
kubectl describe ir testroute
```

Port-forward the pod's service:

```shell
kubectl port-forward svc/testroute 8443:8443
```

Verify a successful greeting is returned (using https):

```shell
curl -k https://localhost:8443/greeting/keip
```

You can also verify some actuator endpoints at these URLs:

- Heath
    - https://localhost:8443/actuator/health
    - https://localhost:8443/actuator/health/liveness
    - https://localhost:8443/actuator/health/readiness
- Prometheus
    - https://localhost:8443/actuator/prometheus

## Clean up

```shell
kubectl delete -k . --ignore-not-found
kubectl delete secret testroute-certstore --ignore-not-found
kubectl delete -k certmanager/issuer --ignore-not-found
kubectl delete -k certmanager --ignore-not-found
```