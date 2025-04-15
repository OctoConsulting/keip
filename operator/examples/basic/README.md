# Example: Basic IntegrationRoute

Deploys a pod that runs a simple Spring Integration app that periodically logs a string. Also, shows how to use
properties defined in `ConfigMap` and `Secret` resources.

## Prerequisites

- Follow the first part of the [Getting Started](..%2F..%2F..%2FREADME.md#getting-started) guide to install the keip
  controller.

## Run the example

Install the example `IntegrationRoute`

```shell
kubectl apply -k .
```

This should result in the creation of the following resources:

- IntegrationRoute `keip.octo.com/v1alpha1/testroute`: The custom resource representing a Spring Integration
  application.
- ConfigMap `testroute-xml`: Contains the Spring Integration XML configuration.
- ConfigMap `testroute-props`: Contains the application's configurable properties.
- Secret `testroute-secret`: Confidential information that will be mounted as a volume in the running
  pod.
- Managed by keip controllers:
    - Deployment `testroute`: Starts up pods running the `keip-integration`
      image (configured in the `keip-controller-props` ConfigMap) and executes the provided integration logic.
    - Service `testroute-actuator`: Exposes the Spring Actuator.

Check that `testroute` is `Ready`:

```shell
kubectl get ir testroute

NAME        READY   REPLICAS   DEPLOYMENT   AGE
testroute   True    1          testroute    72s
```

Get the `Secret`:

```shell
kubectl get secret testroute-secret

NAME               TYPE     DATA   AGE
testroute-secret   Opaque   1      109s
```

Describe the `IntegrationRoute`:

```shell
kubectl describe ir testroute
```

Check the pod's logs for the configured greeting and secret:

```shell
kubectl logs -f deployment/testroute
```

Port-forward the `testroute` pod.

```shell
kubectl port-forward svc/testroute-actuator 8080:8080
```

Test the actuators at these URLs:

- Health
    - http://localhost:8080/actuator/health
    - http://localhost:8080/actuator/health/liveness
    - http://localhost:8080/actuator/health/readiness
- Prometheus Metrics
    - http://localhost:8080/actuator/prometheus

## Clean up

```shell
kubectl delete -k . --ignore-not-found
```