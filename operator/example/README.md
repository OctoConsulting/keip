# IntegrationRoute Example

Deploys a pod that runs a simple Spring Integration app that periodically logs a string.

Prerequisites:

- Kubernetes cluster (v1.24+)
- Metacontroller
- Keip CRDs and controller
- Access to a `keip-integration` image

Run example:

```shell
kubectl apply -k example
```

This should result in the creation of the following resources:

- IntegrationRoute `testroute`: The custom resource object.
- Deployment `testroute`: The controller-created deployment that starts up a pod running
  the `keip-integration` image and executes the configured integration route.
- ConfigMap `testroute-xml`: Contains the Spring Integration XML configuration.
- ConfigMap `testroute-props`: Contains the application's configurable properties.
- Secret `testroute-secret`: Confidential information that will be mounted as volume in the running
  pod.

Check for the running `testroute` pod:

```shell
kubectl get pod

NAME                         READY   STATUS    RESTARTS   AGE
testroute-74d574bf85-tbv9m   1/1     Running   0          99s
```

Check the pod's logs for the configured greeting and secret:
```shell
# The pod will have a different id in the name
kubectl logs testroute-74d574bf85-tbv9m

GenericMessage [payload=Hello. I have a secret to share: (pass123), headers={id=2bc2a4e5-04e8-31e2-f885-25bdf9c6b369, timestamp=1694557405611}]

```

Clean up

```shell
kubectl delete -k example
```