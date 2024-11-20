VERSION ?= 0.4.2
GIT_TAG := operator_v$(VERSION)
KEIP_INTEGRATION_IMAGE ?= ghcr.io/octoconsulting/keip/minimal-app:latest

KUBECTL := kubectl
KUBECTL_DELETE := $(KUBECTL) delete --ignore-not-found
CONTROLLER_NAMESPACE := keip

.PHONY: all
all: metacontroller/deploy controller/deploy

.PHONY: clean
clean: controller/undeploy metacontroller/undeploy

.PHONY: get-tag
get-tag:
	@echo $(GIT_TAG)

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
	$(KUBECTL) apply -k crd

crd/undeploy:
	-$(KUBECTL_DELETE) -k crd
