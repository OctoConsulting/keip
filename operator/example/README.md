# IntegrationRoute Examples

### Example Basic IntegrationRoute

Deploys a pod that runs a simple Spring Integration app that periodically logs a string.

Prerequisites:

- Kubernetes cluster (v1.24+)
- Metacontroller (see `metacontroller/deploy` in [Makefile](../Makefile))
- Keip CRDs and controller (see `controller/deploy` in [Makefile](../Makefile))
- Access to the `keip-integration` image (see `build` in [Makefile](../Makefile))

Run the example:

- Install the example `IntegrationRoute`
```shell
kubectl apply -k integration-routes/basic
```

This should result in the creation of the following resources:

- IntegrationRoute `keip.octo.com/v1alpha1/testroute`: The custom resource representing a Spring Integration application.
- Deployment `testroute`: The controller-created deployment that starts up a pod running
  the `keip-integration` image and executes the configured integration route.
- ConfigMap `testroute-xml`: Contains the Spring Integration XML configuration.
- ConfigMap `testroute-props`: Contains the application's configurable properties.
- Secret `testroute-secret`: Confidential information that will be mounted as a volume in the running
  pod.
- Service `testroute-actuator`: Exposes the Spring Actuator.
- IntegrationRoute Controller `metacontroller.k8s.io/v1alpha1/integrationroute-controller`: A `metacontroller.k8s.io/v1alpha1/CompositeController` that creates a `Deployment` and a `Service` from a `keip.octo.com/v1alpha1/IntegrationRoute`.

Check that pod `testroute` is `Running` and `1/1` is ready:
```shell
kubectl get pods -n default

NAME                         READY   STATUS    RESTARTS   AGE
testroute-74d574bf85-tbv9m   1/1     Running   0          99s
```

Get the `Secret`:
```shell
kubectl get secrets -n default
NAME                  TYPE                DATA   AGE
testroute-secret      Opaque              1      109s
```

Describe the `IntegrationRoute`:
```shell
kubectl describe ir -n default testroute
```

Check the pod's logs for the configured greeting and secret:
```shell
# The pod will have a different id in the name
kubectl logs -f -n default testroute-74d574bf85-tbv9m

GenericMessage [payload=Basic Integration Route. Testing the (basic) integration route., headers={id=ece17042-d99f-b866-0726-b6ef94bdc5af, timestamp=1742919572365}]

```

Port-forward the `testroute` pod.
```shell
# The pod will have a different id in the name
kubectl port-forward testroute-74d574bf85-tbv9m 8080:8080
```

Test the actuators at these URLs:
- Health
  - http://localhost:8080/actuator/health
  - http://localhost:8080/actuator/health/liveness
  - http://localhost:8080/actuator/health/readiness
- Prometheus
  - http://localhost:8080/actuator/prometheus

Clean up:

```shell
kubectl delete -k integration-routes/basic --ignore-not-found
```


### Example IntegrationRoute Using TLS and the CertManager Addon

Deploys a pod that runs a simple Spring Integration app that periodically logs a string. The example 
uses TLS and the `certmanager addon`.

Prerequisites:

- Kubernetes cluster (v1.24+)
- Metacontroller (see `metacontroller/deploy` in [Makefile](../Makefile))
- Keip CRDs and controller (see `controller/deploy` in [Makefile](../Makefile))
- Certmanager addon (see `addons/certmanager/deploy` in [Makefile](../Makefile))
- Access to the `keip-integration` image (see `build` in [Makefile](../Makefile))

Run the example:
- Install `cert-manager`
```shell
kubectl apply -k bases/certmanager
```

- Install the `ClusterIssuer`
```shell
kubectl apply -k bases/certmanager/issuer
```
*_Note_*: If the creating of the `ClusterIssuer` fails, wait a little bit and try again.

- Install the example `IntegrationRoute`
```shell
kubectl apply -k integration-routes/certmanager-addon
```
*_Note_*: The example uses a `keystore.jks` file and a certificate created by [Cert Manager](https://cert-manager.io/).

This should result in the creation of the following resources:

- IntegrationRoute `keip.octo.com/v1alpha1/testroute`: The custom resource representing a Spring Integration application.
- Deployment `testroute`: The controller-created deployment that starts up a pod running
  the `keip-integration` image and executes the configured integration route.
- ConfigMap `testroute-xml`: Contains the Spring Integration XML configuration.
- ConfigMap `testroute-props`: Contains the application's configurable properties.
- Secret `testroute-secret`: Confidential information that will be mounted as a volume in the running
  pod.
- Secret `testroute-certstore`: Private key and certificate signed by the denoted issuer.
- Secret `jks-password`: Password to the JKS keystore.
- Service `testroute-actuator`: Exposes the Spring Actuator.
- Self-Signed Certificate `certificate.cert-manager.io/testroute-certs`: A `certificate.cert-manager.io/Certificate` resource that creates the `testroute-certstore` `Secret` using the `jks-password` `Secret`.
- Cluster Issuer `clusterissuer.cert-manager.io/test-selfsigned`: A self-signed `cert-manager.io/v1/ClusterIssuer` used to sign certificates.
- IntegrationRoute Controller `metacontroller.k8s.io/v1alpha1/integrationroute-controller`: A `metacontroller.k8s.io/v1alpha1/CompositeController` that creates a `Deployment` and a `Service` from a `keip.octo.com/v1alpha1/IntegrationRoute`.
- Certmanager Controller `metacontroller.k8s.io/v1alpha1/certmanager-controller`: A `metacontroller.k8s.io/v1alpha1/DecoratorController` that creates a `Certificate` from a `keip.octo.com/v1alpha1/IntegrationRoute`.

Check that pod `testroute` is `Running` and `1/1` is ready:
```shell
kubectl get pods -n default

NAME                         READY   STATUS    RESTARTS   AGE
testroute-74d574bf85-tbv9m   1/1     Running   0          99s
```
*_Note_*: Cert Manager takes a few seconds to create the certificate and keystore secret. The testroute pod will not start until the `keystore.jks` secret is available to mount.

Describe the `Certificate`:
```shell
kubectl describe certificate -n default testroute-certs
```

Get the `Secrets`:
```shell
kubectl get secrets -n default
NAME                  TYPE                DATA   AGE
jks-password          Opaque              1      109s
testroute-certstore   kubernetes.io/tls   5      107s
testroute-secret      Opaque              1      109s
```

Describe the `IntegrationRoute`:
```shell
kubectl describe ir -n default testroute
```

Check the pod's logs for the configured greeting and secret:
```shell
# The pod will have a different id in the name
kubectl logs -f -n default testroute-74d574bf85-tbv9m

GenericMessage [payload=Using the certmanager addon. Testing the: (certmanager-addon) integration route., headers={id=eb1c2741-a914-0533-47fe-9ace25c134a5, timestamp=1742864017969}]

```

Port-forward the pod and verify https://localhost:8443 returns the default Spring whitelabel error page.
```shell
# The pod will have a different id in the name
kubectl port-forward testroute-74d574bf85-tbv9m 8443:8443
```

Test the actuators at these URLs:
- Heath
  - https://localhost:8443/actuator/health
  - https://localhost:8443/actuator/health/liveness
  - https://localhost:8443/actuator/health/readiness
- Prometheus
  - https://localhost:8443/actuator/prometheus

Clean up:

```shell
kubectl delete -k integration-routes/certmanager-addon --ignore-not-found
kubectl delete secret -n default testroute-certstore --ignore-not-found
kubectl delete -k bases/certmanager/issuer --ignore-not-found
kubectl delete -k bases/certmanager --ignore-not-found
```