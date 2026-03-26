SHELL := /bin/bash

ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
RUN_DIR := $(ROOT_DIR)/.run
LOG_DIR := $(ROOT_DIR)/logs

RUST_DIR := $(ROOT_DIR)/pinn-core
BACKEND_DIR := $(ROOT_DIR)/backend
FRONTEND_DIR := $(ROOT_DIR)/frontend

API_HOST ?= 0.0.0.0
API_PORT ?= 8000
FRONTEND_HOST ?= 127.0.0.1
FRONTEND_PORT ?= 38000

WORKER_PID := $(RUN_DIR)/worker.pid
API_PID := $(RUN_DIR)/api.pid
FRONTEND_PID := $(RUN_DIR)/frontend.pid

WORKER_LOG := $(LOG_DIR)/worker.log
API_LOG := $(LOG_DIR)/api.log
FRONTEND_LOG := $(LOG_DIR)/frontend.log

RUST_ARTIFACT := $(shell find $(RUST_DIR)/target/release -maxdepth 1 \( -name 'libpinn_core.so' -o -name 'libpinn_core.dylib' -o -name 'libpinn_core.rlib' -o -name 'pinn_core*.so' -o -name 'pinn_core*.pyd' \) 2>/dev/null | head -n 1)

WORKER_CMD := cd $(BACKEND_DIR) && source .venv/bin/activate && python -m celery -A tasks.celery_app worker --pool solo --loglevel INFO
API_CMD := cd $(BACKEND_DIR) && source .venv/bin/activate && python -m uvicorn main:app --host $(API_HOST) --port $(API_PORT)
FRONTEND_CMD := cd $(FRONTEND_DIR) && npm run dev -- --host $(FRONTEND_HOST) --port $(FRONTEND_PORT)
RUST_BUILD_CMD := cd $(RUST_DIR) && PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 cargo build --release && if [ -f target/release/libpinn_core.so ]; then cp target/release/libpinn_core.so target/release/pinn_core.so; elif [ -f target/release/libpinn_core.dylib ]; then cp target/release/libpinn_core.dylib target/release/pinn_core.so; fi

.PHONY: help init-dirs \
	rust-build rust-clean rust-rebuild rust-start rust-stop rust-restart rust-status \
	worker-start worker-stop worker-restart worker-status \
	api-start api-stop api-restart api-status \
	frontend-start frontend-stop frontend-restart frontend-status \
	start up stop down restart status logs logs-api logs-worker logs-frontend clean-runtime

define start_service
	@mkdir -p "$(RUN_DIR)" "$(LOG_DIR)"
	@if [ -f "$(1)" ] && kill -0 "$$(cat "$(1)")" 2>/dev/null; then \
		echo "$(2) is already running (PID $$(cat "$(1)"))"; \
	else \
		rm -f "$(1)"; \
		nohup bash -c '$(3)' >>"$(4)" 2>&1 & echo $$! >"$(1)"; \
		sleep 1; \
		if kill -0 "$$(cat "$(1)")" 2>/dev/null; then \
			echo "$(2) started (PID $$(cat "$(1)")) -> $(4)"; \
		else \
			echo "Failed to start $(2). See $(4)"; \
			rm -f "$(1)"; \
			exit 1; \
		fi; \
	fi
endef

define stop_service
	@if [ -f "$(1)" ]; then \
		PID="$$(cat "$(1)")"; \
		if kill -0 "$$PID" 2>/dev/null; then \
			kill "$$PID" 2>/dev/null || true; \
			sleep 1; \
			if kill -0 "$$PID" 2>/dev/null; then \
				kill -9 "$$PID" 2>/dev/null || true; \
			fi; \
			echo "$(2) stopped"; \
		else \
			echo "$(2) is not running, removing stale pid"; \
		fi; \
		rm -f "$(1)"; \
	else \
		echo "$(2) is not running"; \
	fi
endef

define status_service
	@if [ -f "$(1)" ] && kill -0 "$$(cat "$(1)")" 2>/dev/null; then \
		echo "$(2): running (PID $$(cat "$(1)"))"; \
	else \
		echo "$(2): stopped"; \
	fi
endef

help: ## 显示所有可用命令
	@printf "\nPINN-Solve Makefile Commands\n\n"
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf "\nLogs directory: %s\nPID directory:  %s\n\n" "$(LOG_DIR)" "$(RUN_DIR)"

init-dirs: ## 创建运行时目录和日志目录
	@mkdir -p "$(RUN_DIR)" "$(LOG_DIR)"
	@echo "Initialized $(RUN_DIR) and $(LOG_DIR)"

rust-build: ## 编译 Rust 核心
	@bash -lc '$(RUST_BUILD_CMD)'

rust-clean: ## 清理 Rust 构建产物
	@cd "$(RUST_DIR)" && cargo clean

rust-rebuild: rust-clean rust-build ## 重新编译 Rust 核心

rust-start: rust-build ## Rust 核心不是常驻服务，此命令执行编译

rust-stop: rust-clean ## Rust 核心不是常驻服务，此命令清理构建产物

rust-restart: rust-rebuild ## Rust 核心不是常驻服务，此命令执行重新编译

rust-status: ## 查看 Rust 构建状态
	@if [ -n "$(RUST_ARTIFACT)" ]; then \
		echo "Rust core: built ($(RUST_ARTIFACT))"; \
	else \
		echo "Rust core: not built"; \
	fi

worker-start: init-dirs ## 启动 Celery worker
	$(call start_service,$(WORKER_PID),Worker,$(WORKER_CMD),$(WORKER_LOG))

worker-stop: ## 停止 Celery worker
	$(call stop_service,$(WORKER_PID),Worker)

worker-restart: worker-stop worker-start ## 重启 Celery worker

worker-status: ## 查看 Celery worker 状态
	$(call status_service,$(WORKER_PID),Worker)

api-start: init-dirs ## 启动 Python API 后端
	$(call start_service,$(API_PID),API,$(API_CMD),$(API_LOG))

api-stop: ## 停止 Python API 后端
	$(call stop_service,$(API_PID),API)

api-restart: api-stop api-start ## 重启 Python API 后端

api-status: ## 查看 Python API 后端状态
	$(call status_service,$(API_PID),API)

frontend-start: init-dirs ## 启动前端开发服务器
	$(call start_service,$(FRONTEND_PID),Frontend,$(FRONTEND_CMD),$(FRONTEND_LOG))

frontend-stop: ## 停止前端开发服务器
	$(call stop_service,$(FRONTEND_PID),Frontend)

frontend-restart: frontend-stop frontend-start ## 重启前端开发服务器

frontend-status: ## 查看前端开发服务器状态
	$(call status_service,$(FRONTEND_PID),Frontend)

start: up ## 一键启动全部组件

up: rust-build worker-start api-start frontend-start ## 一键编译 Rust 并启动 worker/API/前端

stop: down ## 一键关闭全部组件

down: frontend-stop api-stop worker-stop ## 一键关闭 worker/API/前端

restart: down up ## 一键重启全部组件

status: rust-status worker-status api-status frontend-status ## 查看全部组件状态

logs: ## 同时跟踪 worker/API/前端日志
	@mkdir -p "$(LOG_DIR)"
	@touch "$(WORKER_LOG)" "$(API_LOG)" "$(FRONTEND_LOG)"
	@tail -n 50 -f "$(WORKER_LOG)" "$(API_LOG)" "$(FRONTEND_LOG)"

logs-api: ## 跟踪 API 日志
	@mkdir -p "$(LOG_DIR)"
	@touch "$(API_LOG)"
	@tail -n 50 -f "$(API_LOG)"

logs-worker: ## 跟踪 worker 日志
	@mkdir -p "$(LOG_DIR)"
	@touch "$(WORKER_LOG)"
	@tail -n 50 -f "$(WORKER_LOG)"

logs-frontend: ## 跟踪前端日志
	@mkdir -p "$(LOG_DIR)"
	@touch "$(FRONTEND_LOG)"
	@tail -n 50 -f "$(FRONTEND_LOG)"

clean-runtime: ## 清理 PID 文件和日志文件
	@rm -f "$(WORKER_PID)" "$(API_PID)" "$(FRONTEND_PID)"
	@rm -f "$(WORKER_LOG)" "$(API_LOG)" "$(FRONTEND_LOG)"
	@echo "Runtime files cleaned"
