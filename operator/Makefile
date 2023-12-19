# VERSION = 0.1.0

KEIP_INTEGRATION_IMAGE ?= ghcr.io/octoconsulting/keip-default-image:0.0.1-SNAPSHOT

KUBECTL := kubectl
KUBECTL_DELETE := $(KUBECTL) delete --ignore-not-found
CONTROLLER_NAMESPACE := keip

.PHONY: all
all: metacontroller/deploy controller/deploy


.PHONY: clean
clean: controller/undeploy metacontroller/undeploy

metacontroller/deploy:
	$(KUBECTL) apply -k metacontroller

metacontroller/undeploy:
	-$(KUBECTL_DELETE) -k metacontroller

controller/deploy: crd/deploy
	$(KUBECTL) apply -k controller
	$(KUBECTL) -n $(CONTROLLER_NAMESPACE) create cm keip-controller-props --from-literal=integration-image=$(KEIP_INTEGRATION_IMAGE) -o yaml --dry-run=client | $(KUBECTL) apply -f -

controller/undeploy: crd/undeploy
	-$(KUBECTL_DELETE) -n $(CONTROLLER_NAMESPACE) cm keip-controller-props
	-$(KUBECTL_DELETE) -k controller

crd/deploy:
	$(KUBECTL) apply -k crd/v1alpha1

crd/undeploy:
	-$(KUBECTL_DELETE) -k crd/v1alpha1
