# IntegrationRoute Example

Deploys a pod that runs a simple Spring Integration app that periodically logs a string.

Prerequisites:

- Kubernetes cluster
- Install Metacontroller
- Install keip CRDs and controller
- Access to a `keip-integration` image

Run example:

```shell
kubectl apply -k example
```

This should result in the creation of the following resources:

- `testroute` IntegrationRoute object
- `testroute` Deployment
- `testroute` Pod
- `test-props` and `test-route-xml` ConfigMaps


Clean up
```shell
kubectl delete -k example
```