# KEIP Operator

## Install Instructions TODO
- Metacontroller
- keip CRDs + controller
- Sample IntegrationRoute



### keip CRDs and Controller
```shell
# Deploy
make controller/deploy

# Clean up
make controller/undeploy
```

To deploy in a specific namespace, switch the kubectl namespace context before running the `make` commands above:
```shell
kubectl config set-context --current --namespace=test-ns
```
