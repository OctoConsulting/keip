VERSION ?= 0.1.2
KEIP_INTEGRATION_IMAGE ?= ghcr.io/octoconsulting/keip/minimal-app:0.0.2

KUBECTL := kubectl
KUBECTL_DELETE := $(KUBECTL) delete --ignore-not-found
CONTROLLER_NAMESPACE := keip

.PHONY: all
all: metacontroller/deploy controller/deploy

.PHONY: clean
clean: controller/undeploy metacontroller/undeploy

.PHONY: get-version
get-version:
	@echo $(VERSION)

prep-release:
	rm -rf output
	mkdir output
	kustomize build ./controller > ./output/controller.yaml
	kustomize build ./crd > ./output/crd.yaml
	ls -al ./output

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
