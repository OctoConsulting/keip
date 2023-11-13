# VERSION = 0.1.0

KEIP_INTEGRATION_IMAGE ?= tempreg.local/keip-integration:0.0.1-SNAPSHOT

KUBECTL := kubectl
KUBECTL_DELETE := $(KUBECTL) delete --ignore-not-found
CONTROLLER_NAMESPACE := keip

.PHONY: all
all: controller/deploy

.PHONY: clean
clean: controller/undeploy

controller/deploy: crd/deploy
	$(KUBECTL) -n $(CONTROLLER_NAMESPACE) create cm keip-controller-props --from-literal=integration-image=$(KEIP_INTEGRATION_IMAGE) -o yaml --dry-run=client | $(KUBECTL) apply -f -
	$(KUBECTL) apply -k controller

controller/undeploy: crd/undeploy
	-$(KUBECTL_DELETE) -n $(CONTROLLER_NAMESPACE) cm keip-controller-props
	-$(KUBECTL_DELETE) -k controller
	-$(KUBECTL_DELETE) secret $(PULL_SECRET_NAME)
	-$(KUBECTL_DELETE) -n $(CONTROLLER_NAMESPACE) secret $(PULL_SECRET_NAME)

crd/deploy:
	$(KUBECTL) apply -f crd/v1alpha1

crd/undeploy:
	-$(KUBECTL_DELETE) -f crd/v1alpha1
