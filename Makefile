.PHONY: up up-build down reset logs logs-all migrate seed test lint shell-be shell-db prod-up prod-down

up:                              ## Khởi động tất cả services
	docker compose up -d

up-build:                        ## Build lại images rồi khởi động
	docker compose up -d --build

down:                            ## Dừng tất cả services
	docker compose down

reset:                           ## Xóa volumes, khởi tạo lại từ đầu
	docker compose down -v
	docker compose up -d --build

logs:                            ## Xem logs realtime (backend + frontend)
	docker compose logs -f backend frontend

logs-all:                        ## Xem logs tất cả services
	docker compose logs -f

migrate:                         ## Chạy DB migration
	docker compose exec backend alembic upgrade head

seed:                            ## Seed reference data
	docker compose exec backend python -m app.seed

test:                            ## Chạy test suite
	docker compose exec backend pytest --cov=app --cov-report=term-missing

lint:                            ## Lint backend + frontend
	docker compose exec backend ruff check .
	docker compose exec frontend npm run lint

shell-be:                        ## Shell vào backend container
	docker compose exec backend bash

shell-db:                        ## Kết nối psql
	docker compose exec postgres psql -U $${POSTGRES_USER:-biosec} -d $${POSTGRES_DB:-biosecurity}

prod-up:                         ## Deploy production
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:                       ## Dừng production
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

help:                            ## Hiển thị help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
