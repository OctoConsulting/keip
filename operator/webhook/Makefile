VERSION ?= 0.11.0
HOST_PORT ?= 7080
GIT_TAG := webhook_v$(VERSION)

IMG_REGISTRY := ghcr.io/octoconsulting
IMG_NAME := keip/route-webhook
FULL_IMAGE_NAME := $(IMG_REGISTRY)/$(IMG_NAME):$(VERSION)
CONTAINER_NAME := integration-route-webhook
TEST_COVERAGE_DIR := .test_coverage
TEST_COVERAGE_FILE := $(TEST_COVERAGE_DIR)/.coverage

HOST_PYTHON ?= python3.11

PYTHON = venv/bin/python3
PIP = venv/bin/pip

.PHONY: get-tag
get-tag:
	@echo $(GIT_TAG)

.PHONY: get-registry
get-registry:
	@echo $(IMG_REGISTRY)

.PHONY: get-image-name
get-image-name:
	@echo $(FULL_IMAGE_NAME)

.PHONY: clean
clean:
	rm -rf venv

venv: venv/touchfile

venv/touchfile: requirements.txt requirements-dev.txt
	$(HOST_PYTHON) -m venv venv
	$(PIP) install -r requirements-dev.txt; $(PIP) install -r requirements.txt
	touch venv/touchfile

.PHONY: format
format: venv/touchfile
	$(PYTHON) -m black .

.PHONY: lint
lint: venv/touchfile
	$(PYTHON) -m ruff check

# Suppress Starlette warning when '.env' file is missing
.env:
	touch ./.env

.PHONY: test
test: venv/touchfile .env
	mkdir -p $(TEST_COVERAGE_DIR) && $(PYTHON) -m coverage run --data-file=$(TEST_COVERAGE_FILE) -m pytest

.PHONY: win-test
win-test:
	(if not exist $(TEST_COVERAGE_DIR) mkdir $(TEST_COVERAGE_DIR)) && $(PYTHON) -m coverage run --data-file=$(TEST_COVERAGE_FILE) -m pytest

.PHONY: report-test-coverage
report-test-coverage: test
	$(PYTHON) -m coverage report --data-file $(TEST_COVERAGE_FILE)

.PHONY: win-report-test-coverage
win-report-test-coverage: win-test
	$(PYTHON) -m coverage report --data-file $(TEST_COVERAGE_FILE)

.PHONY: report-test-coverage-html
report-test-coverage-html: test
	$(PYTHON) -m coverage html --data-file $(TEST_COVERAGE_FILE) --directory $(TEST_COVERAGE_DIR)/html && open $(TEST_COVERAGE_DIR)/html/index.html

.PHONY: win-report-test-coverage-html
win-report-test-coverage-html: win-test
	$(PYTHON) -m coverage html --data-file $(TEST_COVERAGE_FILE) --directory $(TEST_COVERAGE_DIR)/html && start "" $(TEST_COVERAGE_DIR)/html/index.html

.PHONY: precommit
precommit: test format lint

.PHONY: win-precommit
win-precommit: win-test format lint

.PHONY: start-dev-server
start-dev-server:
	$(PYTHON) -m uvicorn --port 7080 --reload --app-dir .. webhook.app:app

.PHONY: deploy
deploy: build
	docker push $(FULL_IMAGE_NAME)

.PHONY: build
build:
	docker build --tag $(FULL_IMAGE_NAME) .

.PHONY: run-container
run-container: build
	docker run \
	--name $(CONTAINER_NAME) \
	--publish $(HOST_PORT):7080 \
	$(FULL_IMAGE_NAME)

.PHONY: kill
kill:
	-docker rm -f $(CONTAINER_NAME)
