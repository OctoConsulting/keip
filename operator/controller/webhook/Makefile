VERSION ?= latest
HOST_PORT ?= 7080

IMG_NAME := integration-route-lambda-controller
CONTAINER_NAME := integration-route-webhook
PYTHON := python3

.PHONY: start-dev
start-dev-server:
	$(PYTHON) -m uvicorn --port 7080 --reload --app-dir .. webhook.app:app

.PHONY: test
test:
	cd test && pytest

.PHONY: build
build:
	docker build \
	--tag $(IMG_NAME):$(VERSION) \
	.

.PHONY: run-container
run-container: build
	docker run \
	--name $(CONTAINER_NAME) \
	--publish $(HOST_PORT):7080 \
	$(IMG_NAME):$(VERSION)

.PHONY: kill
kill:
	-docker rm -f $(CONTAINER_NAME) > /dev/null 2>&1
