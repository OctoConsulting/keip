# keip (Kubernetes Enterprise Integration Patterns)

[![operator](https://github.com/OctoConsulting/keip/actions/workflows/operator.yml/badge.svg?branch=main)](https://github.com/OctoConsulting/keip/actions/workflows/operator.yml)
[![webhook](https://github.com/OctoConsulting/keip/actions/workflows/webhook.yml/badge.svg?branch=main)](https://github.com/OctoConsulting/keip/actions/workflows/webhook.yml)
[![minimal-app](https://github.com/OctoConsulting/keip/actions/workflows/minimal-app.yml/badge.svg?branch=main)](https://github.com/OctoConsulting/keip/actions/workflows/minimal-app.yml)

keip is a Kubernetes operator that simplifies the deployment of Spring Integration routes on Kubernetes clusters. This
operator makes it easy to manage integration flows, enhancing scalability and resilience through Kubernetes.

## Key Features

- **Kubernetes Native**: Fully integrates with Kubernetes, using custom resources to manage Spring Integration routes.
- **Ease of Use**: Allows the definition and deployment of complex integration patterns with simple Kubernetes
  manifests.
- **Flexibility**: Supports a range of configurations to cater to different integration requirements.
- **Dynamic Route Definition**: Define and deploy Spring Integration routes at runtime without the need to compile code,
  enabling greater flexibility and faster iterations.

## Getting Started

### Prerequisites

- Kubernetes cluster (v1.24+ recommended)
- `kubectl` installed and configured to interact with your cluster
- The `Make` utility for deploying the operator

### Installation

1. **Clone the repository:**
   ```shell
   git clone https://github.com/OctoConsulting/keip.git && cd keip
   ```

2. **Deploy the keip operator:**
   ```shell
   cd operator && make deploy
   ```

3. The `make deploy` target creates the `keip` and `metacontroller` namespaces and deploys the Metacontroller and
   `IntegrationRoute` webhook pods.

Verify those two are running:

```shell
kubectl -n keip get po

NAME                                        READY   STATUS    RESTARTS   AGE
integrationroute-webhook-6644b989d5-r6htn   1/1     Running   0          2m30s
```

```
kubectl -n metacontroller get po

NAME                                        READY   STATUS    RESTARTS   AGE
metacontroller-0                            1/1     Running   0          2m31s
```

### Customizing Your keip Container

Note: If this is your first time through this installation process, it may be helpful to return to this step later. This
is generally needed for all but the simplest deployments, but it isn't necessary if you're just familiarizing yourself
with the installation process.

The default keip container provides only the basic components for Spring Integration. To fully utilize the potential of
your integration routes, you will need to include additional Spring Integration components or your own Java code. See
[README.md](keip-container-archetype%2FREADME.md) for instructions on how to create a custom container.

Once your new container is available, you'll need to set that name in the `keip-controller-props` ConfigMap. We'll need
to change the value for the `integration-image` key to set it to whatever the name of your custom keip container is.

```shell
kubectl -n keip edit configmap keip-controller-props
```

Once the ConfigMap is updated, you'll need to restart the `integrationroute-webhook` pod.

```shell
kubectl -n keip rollout restart deployment/integrationroute-webhook
```

### Deploying a Spring Integration Route

The keip operator requires a Spring Integration route defined in XML. This XML should be stored in a ConfigMap that the
IntegrationRoute custom resource will reference.

1. Create a ConfigMap with your XML configuration:

```shell
cat <<'EOF' | kubectl create -f -
apiVersion: v1
kind: ConfigMap
metadata:
    name: keip-route-xml
data:
    integrationRoute.xml: |
        <?xml version="1.0" encoding="UTF-8"?>
        <beans xmlns="http://www.springframework.org/schema/beans"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:int="http://www.springframework.org/schema/integration"
                xsi:schemaLocation="http://www.springframework.org/schema/beans
                    https://www.springframework.org/schema/beans/spring-beans.xsd
                    http://www.springframework.org/schema/integration
                    https://www.springframework.org/schema/integration/spring-integration.xsd">
            <int:channel id="output"/>

            <int:inbound-channel-adapter channel="output" expression="'print me every 5 seconds'">
              <int:poller fixed-rate="5000"/>
            </int:inbound-channel-adapter>
      
            <int:logging-channel-adapter
                  channel="output"
                  log-full-message="true"/>
        </beans>
EOF
```

2. Apply your IntegrationRoute using the created ConfigMap:

```shell
cat <<'EOF' | kubectl create -f -
apiVersion: keip.octo.com/v1alpha1
kind: IntegrationRoute
metadata:
  name: example-route
spec:
  routeConfigMap: keip-route-xml
EOF
```

For more in-depth examples, see the [operator/examples](./operator/example) directory.

## Clean up

To delete the example route:

```shell
kubectl delete ir example-route
kubectl delete cm keip-route-xml
```

To remove the keip operator and all related resources from your cluster:

```shell
cd operator && make undeploy
```

## Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for more details.

## Support

For assistance or to report issues, please open an issue in the GitHub repository.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.