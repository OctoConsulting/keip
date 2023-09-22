# VERSION = 0.1.0

KEIP_INTEGRATION_IMAGE ?= tempreg.local/keip-integration:0.0.1-SNAPSHOT

KUBECTL := kubectl
KUBECTL_DELETE := $(KUBECTL) delete --ignore-not-found
CONTROLLER_NAMESPACE := metacontroller
PULL_SECRET_NAME := local-registry-creds
DOCKER_CONFIG_PATH ?= $${HOME}/.docker/config.json

METACONTROLLER_VERSION := v4.10.7
METACONTROLLER_URL := https://github.com/metacontroller/metacontroller/manifests/production?ref=$(METACONTROLLER_VERSION)

.PHONY: all
all: metacontroller/deploy controller/deploy

.PHONY: clean
clean: controller/undeploy metacontroller/undeploy

metacontroller/deploy:
	$(KUBECTL) apply -k $(METACONTROLLER_URL)

metacontroller/undeploy:
	-$(KUBECTL_DELETE) -k $(METACONTROLLER_URL)

controller/deploy: .create-pull-secret .copy-pull-secret-to-namespace crd/deploy
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

.create-pull-secret:
	$(KUBECTL) -n $(CONTROLLER_NAMESPACE) create secret generic $(PULL_SECRET_NAME) --from-file=.dockerconfigjson=$(DOCKER_CONFIG_PATH) --type=kubernetes.io/dockerconfigjson -o yaml --dry-run=client | $(KUBECTL) apply -f -

# Copies the private registry pull secret to the currently active namespace
.copy-pull-secret-to-namespace:
	@$(KUBECTL_DELETE) secret $(PULL_SECRET_NAME)
	@CURRENT_NAMESPACE=$$($(KUBECTL) config view --minify -o jsonpath='{..namespace}') && echo "Copy secret $(PULL_SECRET_NAME) to active namespace [$$CURRENT_NAMESPACE]"
	@$(KUBECTL) -n $(CONTROLLER_NAMESPACE) get secret $(PULL_SECRET_NAME) -o yaml | grep -v '^\s*namespace:\s' | $(KUBECTL) apply -f -