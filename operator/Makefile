VERSION ?= 0.7.0
GIT_TAG := operator_v$(VERSION)
# TODO: Change back to :latest when CI is fixed
KEIP_INTEGRATION_IMAGE ?= ghcr.io/octoconsulting/keip/minimal-app:0.0.4

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
	@rm -rf output
	@mkdir -p output/addons
	@echo "Running kustomize build on ./controller/"
	kustomize build ./controller/ > ./output/keip-core-controller.yaml
	@for dir in ./controller/addons/*/ ; do \
		echo "Running kustomize build on $$dir" ; \
		addon=$$(basename $$dir) ; \
		mkdir -p output/addons/$$addon ; \
		kustomize build $$dir >> ./output/addons/$$addon/keip-$${addon}-addon-controller.yaml ; \
		echo "---" >> ./output/addons/keip-addon-controllers.yaml ; \
		kustomize build $$dir >> ./output/addons/keip-addon-controllers.yaml ; \
	done
	@echo "Running kustomize build on ./crd/"
	kustomize build ./crd/ > ./output/crd.yaml
	@echo "Files that will be released:"
	@find ./output -type f

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

addons/certmanager/deploy:
	$(KUBECTL) apply -k controller/addons/certmanager

addons/certmanager/undeploy:
	$(KUBECTL_DELETE) -k controller/addons/certmanager

crd/deploy:
	$(KUBECTL) apply -k crd

crd/undeploy:
	-$(KUBECTL_DELETE) -k crd
