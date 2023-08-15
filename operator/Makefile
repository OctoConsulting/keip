# VERSION = 0.1.0
KEIP_INTEGRATION_IMAGE ?= keip-integration:0.0.1-SNAPSHOT

# kubectl commands
KUBECTL := kubectl
CONTROLLER_NAMESPACE := metacontroller

controller/deploy: crd/deploy
	$(KUBECTL) create cm keip-controller-props --from-literal=integration-image=$(KEIP_INTEGRATION_IMAGE) -n $(CONTROLLER_NAMESPACE)
	$(KUBECTL) apply -k controller

controller/undeploy: crd/undeploy
	-$(KUBECTL) delete cm keip-controller-props -n $(CONTROLLER_NAMESPACE)
	-$(KUBECTL) delete -k controller

crd/deploy:
	$(KUBECTL) apply -f crd/v1alpha1

crd/undeploy:
	-$(KUBECTL) delete -f crd/v1alpha1