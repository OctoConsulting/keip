# Kubernetes Enterprise Integration Patterns (Keip)

The goal of Keip is to provide a simple method for deploying Spring Integration routes using
Kuberenetes semantics.
Once installed on a Kubernetes cluster, creating SI routes is done by defining the route in XML and
bundling that
route into a Kubernetes Custom Resource. The resource is then created by using:

```shell
kubectl apply -f myCustomRoute.yaml
```

## Project Structure

The project consists of several pieces:

1. container - the container provided includes dependencies for *most* of the commonly-used Spring
   Integration
   components. Note that the container used here is a reference implementation which can be replaced
   in cases where
   custom components are required.
2. operator -
    1. resource - this is the Kubernetes custom resource definition, `IntegrationRoute`.
    2. operator - this is the operator which does the cluster work in reaction to the creation
       of `IntegrationRoutes`.

## Getting Started

### Prerequisites

- Kubernetes v1.24+
    - `kubectl` should also be installed and configured to communicate with the desired cluster.
- The `Make` utility

### Configure Private Image Registry

#TODO
**Note:** Until the project is made public, container image artifacts will be stored at
the `tempreg.local` private registry. Your Kubernetes cluster will have to be configured to pull from
that registry
using [imagePullSecrets](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/).

### Installing the Keip Operator

The Keip operator uses
the [Metacontroller](https://metacontroller.github.io/metacontroller/intro.html) framework, which
must be deployed first for the Keip lambda controller to function. Makefiles are provided
to install both the Metacontroller and Keip controller.

```shell
# Switch to namespace where IntegrationRoutes will be deployed
kubectl config set-context --current --namespace=<target-namespace>

cd operator
make all
```

The `make all` target creates the `keip` and `metacontroller` namespaces and deploys the Metacontroller and
IntegrationRoute webhook (lambda controller) pods.

Verify those two are running:

```shell
kubectl -n keip get po

NAME                                        READY   STATUS    RESTARTS   AGE
integrationroute-webhook-6644b989d5-r6htn   1/1     Running   0          2m30s

kubectl -n metacontroller get po

NAME                                        READY   STATUS    RESTARTS   AGE
metacontroller-0                            1/1     Running   0          2m31s
```

Finally, test the operator by deploying the
IntegrationRoute [example](operator%2Fexample%2FREADME.md).

### Clean up

The following command deletes the `keip` and `metacontroller` namespaces and all resources within them. Also,
deletes the Keip CRDs.

```shell
cd operator
make clean
```
