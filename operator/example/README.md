# IntegrationRoute Example

Deploys a pod that runs a simple Spring Integration app that periodically logs a string.

Prerequisites:

- Kubernetes cluster (v1.24+)
- Metacontroller
- Keip CRDs and controller
- Access to a `keip-integration` image

Run the example:
```shell
kubectl apply -k example
```
*_Note_*: The example uses a keystore.jks file and a certificate created by [Cert Manager](https://cert-manager.io/).

This should result in the creation of the following resources:

- IntegrationRoute `testroute`: The custom resource object.
- Deployment `testroute`: The controller-created deployment that starts up a pod running
  the `keip-integration` image and executes the configured integration route.
- ConfigMap `testroute-xml`: Contains the Spring Integration XML configuration.
- ConfigMap `testroute-props`: Contains the application's configurable properties.
- Secret `testroute-secret`: Confidential information that will be mounted as volume in the running
  pod.
- Self-Signed Certificate `certificate.cert-manager.io/selfsigned-cert`: A certificate resource that creates the `test-keystore` secret using the `jks-password` secret
- Cluster Issuer `clusterissuer.cert-manager.io/test-selfsigned`: A self-signed cluster issuer used to sign certificates.

Check for the running `testroute` pod:

```shell
kubectl get pod

NAME                         READY   STATUS    RESTARTS   AGE
testroute-74d574bf85-tbv9m   1/1     Running   0          99s
```
*_Note_*: Cert Manager takes a few seconds to create the certificate and keystore secret. The testroute pod will not start until the keystore.jks secret is available to mount.

Check the pod's logs for the configured greeting and secret:
```shell
# The pod will have a different id in the name
kubectl logs testroute-74d574bf85-tbv9m

GenericMessage [payload=Hello. I have a secret to share: (pass123), headers={id=2bc2a4e5-04e8-31e2-f885-25bdf9c6b369, timestamp=1694557405611}]

```

Port-forward the pod and verify `https://localhost:8443` returns the default Spring whitelabel error page.
```shell
kubectl port-forward testroute-74d574bf85-tbv9m 8443:8443
```

Clean up

```shell
kubectl delete -k example
```