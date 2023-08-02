# VERSION = 0.1.0

# kubectl commands
KUBECTL = kubectl


controller/deploy: crd/deploy
	$(KUBECTL) apply -k controller

controller/undeploy: crd/undeploy
	-$(KUBECTL) delete -k controller

crd/deploy:
	$(KUBECTL) apply -f crd/v1alpha1

crd/undeploy:
	-$(KUBECTL) delete -f crd/v1alpha1