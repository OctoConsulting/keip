VERSION ?= 0.7.0
HOST_PORT ?= 7080
GIT_TAG := webhook_v$(VERSION)

IMG_REGISTRY := ghcr.io/octoconsulting
IMG_NAME := keip/route-webhook
FULL_IMAGE_NAME := $(IMG_REGISTRY)/$(IMG_NAME):$(VERSION)
CONTAINER_NAME := integration-route-webhook
PYTHON := python3
TEST_COVERAGE_DIR := .test_coverage
TEST_COVERAGE_FILE := $(TEST_COVERAGE_DIR)/.coverage

.PHONY: get-tag
get-tag:
	@echo $(GIT_TAG)

.PHONY: get-registry
get-registry:
	@echo $(IMG_REGISTRY)

.PHONY: get-image-name
get-image-name:
	@echo $(FULL_IMAGE_NAME)

.PHONY: start-dev
start-dev-server:
	$(PYTHON) -m uvicorn --port 7080 --reload --app-dir .. webhook.app:app

.PHONY: test
test:
	cd test && mkdir -p $(TEST_COVERAGE_DIR) && coverage run --data-file=$(TEST_COVERAGE_FILE) -m pytest -vv

.PHONY: win-test
win-test:
	cd test && (if not exist $(TEST_COVERAGE_DIR) mkdir $(TEST_COVERAGE_DIR)) && coverage run --data-file=$(TEST_COVERAGE_FILE) -m pytest -vv

.PHONY: report-test-coverage
report-test-coverage: test
	cd test && coverage report --data-file $(TEST_COVERAGE_FILE)

.PHONY: win-report-test-coverage
win-report-test-coverage: win-test
	cd test && coverage report --data-file $(TEST_COVERAGE_FILE)

.PHONY: report-test-coverage-html
report-test-coverage-html: test
	cd test && coverage html --data-file $(TEST_COVERAGE_FILE) --directory $(TEST_COVERAGE_DIR)/html && open $(TEST_COVERAGE_DIR)/html/index.html

.PHONY: win-report-test-coverage-html
win-report-test-coverage-html: win-test
	cd test && coverage html --data-file $(TEST_COVERAGE_FILE) --directory $(TEST_COVERAGE_DIR)/html && start "" $(TEST_COVERAGE_DIR)/html/index.html

.PHONY: deploy
deploy: build
	docker push $(FULL_IMAGE_NAME)

.PHONY: build
build:
	docker build \
  --tag $(FULL_IMAGE_NAME) \
  .

.PHONY: run-container
run-container: build
	docker run \
	--name $(CONTAINER_NAME) \
	--publish $(HOST_PORT):7080 \
	$(FULL_IMAGE_NAME)

.PHONY: kill
kill:
	-docker rm -f $(CONTAINER_NAME)
