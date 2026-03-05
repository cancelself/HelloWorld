PROJECT      := helloworld-lang
REGION       := us-central1
REGISTRY     := $(REGION)-docker.pkg.dev/$(PROJECT)/helloworld
IMAGE        := $(REGISTRY)/mcp-server
TAG          := latest
SERVICE      := helloworld
BUCKET       := $(PROJECT)-litestream
CLOUD_RUN_URL := https://helloworld-997317080791.us-central1.run.app

.PHONY: lint test build push deploy run run-local clean auth infra

lint:
	python3 -m compileall src

test:
	python3 -m pytest tests

build:
	docker build --platform linux/amd64 -t $(IMAGE):$(TAG) .

push: build
	docker push $(IMAGE):$(TAG)

deploy: push
	gcloud run deploy $(SERVICE) \
		--image $(IMAGE):$(TAG) \
		--region $(REGION) \
		--project $(PROJECT) \
		--port 8080 \
		--max-instances 1 \
		--set-env-vars HELLOWORLD_SERVER_URL=$(CLOUD_RUN_URL)

run:
	docker run --rm -p 8080:8080 \
		-e HW_TRANSPORT=sqlite \
		-v $$(pwd)/storage:/app/storage \
		$(IMAGE):$(TAG)

run-local:
	HW_TRANSPORT=file python3 helloworld.py --mcp --port 8080

auth:
	gcloud auth configure-docker $(REGION)-docker.pkg.dev

infra:
	gcloud storage buckets create gs://$(BUCKET) \
		--project $(PROJECT) \
		--location $(REGION) \
		--uniform-bucket-level-access
	@echo "Granting Cloud Run service account access to GCS bucket..."
	$(eval SA := $(shell gcloud iam service-accounts list --project=$(PROJECT) --format='value(email)' --filter='displayName:Default compute'))
	gcloud storage buckets add-iam-policy-binding gs://$(BUCKET) \
		--member="serviceAccount:$(SA)" \
		--role="roles/storage.objectAdmin"

clean:
	docker rmi $(IMAGE):$(TAG) 2>/dev/null || true
