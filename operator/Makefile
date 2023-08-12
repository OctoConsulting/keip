# VERSION = 0.1.0
KEIP_INTEGRATION_IMAGE ?= keip-integration:0.0.1-SNAPSHOT

# kubectl commands
KUBECTL = kubectl

controller/deploy: crd/deploy
	$(KUBECTL) create cm keip-controller-props --from-literal=integration-image=$(KEIP_INTEGRATION_IMAGE)
	$(KUBECTL) apply -k controller

controller/undeploy: crd/undeploy
	-$(KUBECTL) delete cm keip-controller-props
	-$(KUBECTL) delete -k controller

crd/deploy:
	$(KUBECTL) apply -f crd/v1alpha1

crd/undeploy:
	-$(KUBECTL) delete -f crd/v1alpha1