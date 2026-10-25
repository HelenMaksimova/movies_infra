.PHONY: clean create_network db_init db_init_with_data nginx_init up up_with_data help

NETWORK_NAME ?= movies_net
CLEAN ?= false
PORTS ?= false
CLEAN_MODE ?= soft
CLEAN_TARGET ?= db

SHELL := /bin/bash
COMPOSE_PORTS := .docker/docker-compose.ports.yml

COMPOSE_DB    := .docker/docker-compose.databases.with_data.yml
COMPOSE_NGINX := .docker/docker-compose.nginx.yml
COMPOSE_ALL   := .docker/docker-compose.with_data.yml

COMPOSE_CLEAN := $(if $(filter nginx,$(CLEAN_TARGET)),$(COMPOSE_NGINX), \
                  $(if $(filter all,$(CLEAN_TARGET)),$(COMPOSE_ALL),$(COMPOSE_DB)))

clean:
	@echo "✅ Выполняем очистку (цель: $(CLEAN_TARGET), режим: $(CLEAN_MODE))..."
	@if [ "$(CLEAN_MODE)" = "volumes" ]; then \
		docker compose -f $(COMPOSE_CLEAN) down --volumes; \
	elif [ "$(CLEAN_MODE)" = "hard" ]; then \
		docker compose -f $(COMPOSE_CLEAN) down --volumes --rmi all; \
	else \
		docker compose -f $(COMPOSE_CLEAN) down; \
	fi
	@echo "✅ Готово!"

create_network:
	@docker network inspect $(NETWORK_NAME) >/dev/null 2>&1 || docker network create $(NETWORK_NAME)

db_init:
	@if [ "$(CLEAN)" = "true" ]; then \
		$(MAKE) clean CLEAN_MODE=volumes CLEAN_TARGET=db; \
	fi
	@$(MAKE) create_network
	@if [ "$(PORTS)" = "true" ]; then \
		docker compose -f .docker/docker-compose.databases.yml -f $(COMPOSE_PORTS) up -d; \
	else \
		docker compose -f .docker/docker-compose.databases.yml up -d; \
	fi

db_init_with_data:
	@if [ "$(CLEAN)" = "true" ]; then \
		$(MAKE) clean CLEAN_MODE=volumes CLEAN_TARGET=db; \
	fi
	@$(MAKE) create_network
	@if [ "$(PORTS)" = "true" ]; then \
		docker compose -f .docker/docker-compose.databases.with_data.yml -f $(COMPOSE_PORTS) up -d; \
	else \
		docker compose -f .docker/docker-compose.databases.with_data.yml up -d; \
	fi

nginx_init:
	@if [ "$(CLEAN)" = "true" ]; then \
		$(MAKE) clean CLEAN_MODE=volumes CLEAN_TARGET=nginx; \
	fi
	@$(MAKE) create_network
	@docker compose -f .docker/docker-compose.nginx.yml up -d

up:
	@if [ "$(CLEAN)" = "true" ]; then \
		$(MAKE) clean CLEAN_MODE=volumes CLEAN_TARGET=all; \
	fi
	@$(MAKE) create_network
	@docker compose -f .docker/docker-compose.yml up -d

up_with_data:
	@if [ "$(CLEAN)" = "true" ]; then \
		$(MAKE) clean CLEAN_MODE=volumes CLEAN_TARGET=all; \
	fi
	@$(MAKE) create_network
	@docker compose -f .docker/docker-compose.with_data.yml up -d

help:
	@echo "*********************************************************************"
	@echo "  Управление окружением"
	@echo "*********************************************************************"
	@echo ""
	@echo "  make create_network"
	@echo "      Создаёт внешнюю Docker-сеть $(NETWORK_NAME), если её ещё нет."
	@echo ""
	@echo "  make db_init [PORTS=true] [CLEAN=true]"
	@echo "      Поднимает базы без начальных данных."
	@echo "      PORTS=true  — публикует порты на хост."
	@echo "      CLEAN=true  — перед запуском удаляет контейнеры/тома баз (CLEAN_MODE=volumes)."
	@echo ""
	@echo "  make db_init_with_data [PORTS=true] [CLEAN=true]"
	@echo "      Поднимает базы с начальными данными."
	@echo "      PORTS=true  — публикует порты на хост."
	@echo "      CLEAN=true  — перед запуском удаляет контейнеры/тома баз (CLEAN_MODE=volumes)."
	@echo ""
	@echo "  make nginx_init [CLEAN=true]"
	@echo "      Поднимает nginx (порты публикуются всегда)."
	@echo "      CLEAN=true  — перед запуском удаляет контейнеры/тома nginx (CLEAN_MODE=volumes)."
	@echo ""
	@echo "  make up [CLEAN=true]"
	@echo "      Поднимает все сервисы без начальных данных."
	@echo "      CLEAN=true  — перед запуском удаляет контейнеры/тома всех сервисов (CLEAN_MODE=volumes)."
	@echo ""
	@echo "  make up_with_data [CLEAN=true]"
	@echo "      Поднимает все сервисы с начальными данными."
	@echo "      CLEAN=true  — перед запуском удаляет контейнеры/тома всех сервисов (CLEAN_MODE=volumes)."
	@echo ""
	@echo "  make clean [CLEAN_TARGET=db|nginx|all] [CLEAN_MODE=soft|volumes|hard]"
	@echo "      Останавливает и удаляет контейнеры выбранной цели."
	@echo "      CLEAN_TARGET=db     (по умолчанию) — .docker/docker-compose.databases.with_data.yml"
	@echo "      CLEAN_TARGET=nginx  — .docker/docker-compose.nginx.yml"
	@echo "      CLEAN_TARGET=all    — .docker/docker-compose.with_data.yml"
	@echo "      CLEAN_MODE=soft     (по умолчанию) — контейнеры и сети проекта."
	@echo "      CLEAN_MODE=volumes  — плюс тома проекта."
	@echo "      CLEAN_MODE=hard     — плюс тома и образы проекта."
	@echo ""
	@echo "  make help"
	@echo "      Показывает эту справку."
	@echo ""
	@echo "*********************************************************************"
