# Kubernetes Enterprise Integration Patterns (Keip)

The goal of Keip is to provide a simple method for deploying Spring Integration routes using Kuberenetes semantics.
Once installed on a Kubernetes cluster, creating SI routes is done by defining the route in XML and bundling that 
route into a Kubernetes Custom Resource. The resource is then created by using:

```shell
kubectl apply -f myCustomRoute.yaml
```

## Project Structure

The project consists of several pieces:

1. container - the container provided includes dependencies for *most* of the commonly-used Spring Integration 
components. Note that the container used here is a reference implementation which can be replaced in cases where 
custom components are required.
2. operator -
   1. resource - this is the Kubernetes custom resource definition, `IntegrationRoute`.
   2. operator - this is the operator which does the cluster work in reaction to the creation of `IntegrationRoutes`. 