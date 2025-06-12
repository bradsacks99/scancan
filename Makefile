# Variables
DOCKER_COMPOSE = docker compose
PYLINT_CMD = pytest --pylint scancan/
PYTEST_CMD = pytest tests/
MYPY_CMD = pytest --mypy scancan/
AWS_REGION = YOUR_AWS_REGION
ECR_URL = YOUR_ECR_URL

# Targets
.PHONY: build
build:
	$(DOCKER_COMPOSE) build

.PHONY: up
up:
	$(DOCKER_COMPOSE) up

.PHONY: down
down:
	$(DOCKER_COMPOSE) down

.PHONY: restart
restart:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up --build

.PHONY: test
test:
	$(PYLINT_CMD)
	$(MYPY_CMD)
	$(PYTEST_CMD)

.PHONY: pylint
pylint:
	$(PYLINT_CMD)

.PHONY: pytest
pytest:
	$(PYTEST_CMD)

.PHONY: mypy
mypy:
	$(MYPY_CMD)

.PHONY: push
push:
	# Build and tag scancan image
	docker build -t scancan .
	docker tag scancan $(ECR_URL)/scancan:latest
	# Build and tag fresh_clam image
	docker build -t fresh_clam -f Dockerfile.cron .
	docker tag fresh_clam $(ECR_URL)/fresh_clam:latest
	# Push images to AWS ECR
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_URL)
	docker push $(ECR_URL)/scancan:latest
	docker push $(ECR_URL)/fresh_clam:latest