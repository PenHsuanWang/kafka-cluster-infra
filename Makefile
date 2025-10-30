.PHONY: help start stop restart status health topics test logs clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Start the Kafka cluster
	@chmod +x scripts/*.sh
	@./scripts/start-cluster.sh

stop: ## Stop the Kafka cluster
	@./scripts/stop-cluster.sh

restart: ## Restart the Kafka cluster
	@docker-compose restart

status: ## Show cluster status
	@docker-compose ps

health: ## Run health checks
	@./scripts/health-check.sh

topics: ## Create sample topics
	@./scripts/create-topics.sh

test: ## Run performance tests
	@./scripts/performance-test.sh

logs: ## View all logs
	@docker-compose logs -f

logs-kafka: ## View Kafka broker logs
	@docker-compose logs -f kafka-1 kafka-2 kafka-3

logs-zk: ## View ZooKeeper logs
	@docker-compose logs -f zookeeper-1 zookeeper-2 zookeeper-3

ui: ## Open Kafka UI
	@echo "Opening Kafka UI at http://localhost:8080"
	@command -v xdg-open && xdg-open http://localhost:8080 || open http://localhost:8080 || echo "Please open http://localhost:8080 in your browser"

shell-kafka: ## Open shell in kafka-1 broker
	@docker exec -it kafka-1 bash

shell-zk: ## Open shell in zookeeper-1
	@docker exec -it zookeeper-1 bash

clean: ## Remove all containers and volumes (DATA LOSS!)
	@docker-compose down -v
	@echo "All data removed"

pull: ## Pull latest Docker images
	@docker-compose pull

validate: ## Validate docker-compose.yml
	@docker-compose config --quiet && echo "✓ docker-compose.yml is valid"
