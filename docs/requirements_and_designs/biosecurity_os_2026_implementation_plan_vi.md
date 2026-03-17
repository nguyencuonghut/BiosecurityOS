# KẾ HOẠCH TRIỂN KHAI CHI TIẾT — BIOSECURITY OS 2026

> **Phiên bản:** 1.0 · **Ngày tạo:** 2026-03-14
> **Tham chiếu:** requirements_v3, api_contracts_v2, erd_v2, postgres_schema_v1, wireframes_v2

---

## MỤC LỤC

1. [Tổng quan kiến trúc & Tech Stack](#1-tổng-quan-kiến-trúc--tech-stack)
2. [Cấu trúc source code](#2-cấu-trúc-source-code)
3. [Quy ước chung](#3-quy-ước-chung)
4. [Phân pha triển khai (Phase)](#4-phân-pha-triển-khai)
5. [Chi tiết từng Sprint](#5-chi-tiết-từng-sprint)
6. [Ma trận phụ thuộc giữa các module](#6-ma-trận-phụ-thuộc-giữa-các-module)
7. [Chiến lược kiểm thử](#7-chiến-lược-kiểm-thử)
8. [Hạ tầng & DevOps](#8-hạ-tầng--devops)
9. [Rủi ro & Biện pháp giảm thiểu](#9-rủi-ro--biện-pháp-giảm-thiểu)
10. [Definition of Done (DoD)](#10-definition-of-done)
11. [Checklist trước Go-Live](#11-checklist-trước-go-live)

---

## 1. TỔNG QUAN KIẾN TRÚC & TECH STACK

### 1.1 Sơ đồ kiến trúc tổng thể

```
┌────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                 │
│  Vue.js 3 + PrimeVue (SPA)     │    Mobile Web (responsive)    │
└──────────────────┬─────────────┴───────────────────────────────┘
                   │  HTTPS / TLS 1.2+
┌──────────────────▼─────────────────────────────────────────────┐
│                   REVERSE PROXY (Nginx / Caddy)                │
│         Rate limiting · CORS · Static file serving             │
└──────────────────┬─────────────────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────────────────┐
│                   FASTAPI APPLICATION                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Auth &  │ │  Farm &  │ │ Case &   │ │ Scar & Lesson    │   │
│  │  IAM     │ │ Assess.  │ │ Task     │ │ Memory           │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────────────┘   │
│       │            │            │            │                 │
│  ┌────▼─────────────▼────────────▼─────────────▼────────────┐  │
│  │               SHARED SERVICES LAYER                      │  │
│  │  RBAC · Audit Logger · File Service · Notification Svc   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────┬──────────┬─────────────┬──────────────────────────────┘
         │          │             │
    ┌────▼───┐ ┌────▼───┐    ┌────▼───┐
    │Postgres│ │  Redis │    │  MinIO │
    │(biosec)│ │ Cache  │    │ Object │
    │        │ │ Queue  │    │Storage │
    └────────┘ └────────┘    └────────┘
                                  │
                            ┌─────▼───┐
                            │   n8n   │
                            │  (Notif │
                            │  only)  │
                            └─────────┘
```

### 1.2 Tech Stack chi tiết

| Layer | Công nghệ | Phiên bản tối thiểu | Ghi chú |
|-------|-----------|---------------------|---------|
| **Backend** | Python + FastAPI | Python 3.12+, FastAPI 0.115+ (latest) | async, Pydantic v2-native; **tránh dùng pattern/code style của FastAPI ≤0.99 (on_event, Depends cũ, Response model cũ)** |
| **ORM** | SQLAlchemy 2.0 + Alembic | SQLAlchemy 2.0+ | async session |
| **Validation** | Pydantic v2 | 2.x (latest) | schema validation, model_config thay cho class Config |
| **Frontend** | Vue.js 3 + PrimeVue 4 | Vue 3.5+, PrimeVue 4.x (latest) | **Composition API + JavaScript** (không dùng TypeScript) |
| **Charts** | Apache ECharts | 5.x | Spider chart, trend chart |
| **Database** | PostgreSQL | 15+ | schema `biosec`, pgcrypto |
| **Cache** | Redis | 7+ | session, rate limit, cache |
| **Object Storage** | MinIO | latest | presigned URL upload |
| **Automation** | n8n | latest | notification workflow only |
| **Reverse Proxy** | Nginx hoặc Caddy | — | TLS termination, rate limit |
| **Container** | Docker + Docker Compose | — | dev & prod |
| **CI/CD** | GitHub Actions / GitLab CI | — | lint → test → build → deploy |
| **Migration** | Flyway hoặc Alembic | — | versioned SQL |

---

## 2. CẤU TRÚC SOURCE CODE

### 2.0 Cấu trúc gốc (monorepo)

```
BiosecurityOS/
├── docker-compose.yml           # Dev: tất cả services (1 lệnh docker compose up)
├── docker-compose.prod.yml      # Prod override: resource limits, restart policy, TLS
├── .env.example                 # Template biến môi trường
├── .env                         # Biến môi trường thực (git-ignored)
├── Makefile                     # Shortcuts: make up, make down, make migrate, make seed, make logs
│
├── backend/                     # FastAPI application
│   ├── Dockerfile               # Multi-stage: builder → runner (python:3.12-slim)
│   ├── pyproject.toml
│   └── app/
│
├── frontend/                    # Vue.js 3 SPA
│   ├── Dockerfile               # Multi-stage: node build → nginx serve
│   ├── nginx.conf               # Reverse proxy /api → backend:8000
│   └── src/
│
├── nginx/                       # (Prod) Reverse proxy + TLS termination
│   ├── nginx.conf
│   └── certs/                   # TLS certificates (git-ignored)
│
├── n8n/                         # n8n workflow backup
│   └── workflows/               # Exported JSON workflows
│
├── scripts/
│   ├── init-db.sh               # Chạy migration + seed khi container postgres lần đầu
│   ├── backup-db.sh             # pg_dump cron script
│   └── restore-db.sh            # Restore từ backup
│
├── docs/
│   └── requirements_and_designs/
│
└── README.md
```

### 2.1 Backend (FastAPI latest)

> **⚠️ LƯU Ý QUAN TRỌNG — Tránh pattern cũ của FastAPI:**
> - Dùng `lifespan` context manager thay cho `@app.on_event("startup"/"shutdown")` (deprecated)
> - Dùng `Annotated[Dependency, Depends()]` thay cho `param: Type = Depends(func)` (new style)
> - Dùng `model_config = ConfigDict(...)` trong Pydantic v2 thay cho `class Config:` (legacy)
> - Dùng `response_model` với Pydantic v2 model (không dùng `schema_extra`, dùng `json_schema_extra`)
> - Dùng `from fastapi import Query, Path, Body` với `Annotated` type hints
> - Không dùng `fastapi.encoders.jsonable_encoder` cho response — FastAPI tự serialize Pydantic v2
> - Dùng async endpoint + async SQLAlchemy session (không mix sync/async)

```
backend/
├── alembic/                     # DB migrations
│   └── versions/
├── app/
│   ├── main.py                  # FastAPI app factory, lifespan context manager
│   ├── config.py                # Settings (pydantic-settings, model_config)
│   ├── database.py              # Async engine, async session factory
│   │
│   ├── auth/                    # Module: Authentication & Authorization
│   │   ├── router.py            #   POST /auth/login, /refresh, /logout
│   │   ├── service.py           #   Login logic, token mgmt
│   │   ├── dependencies.py      #   get_current_user, require_permission
│   │   ├── schemas.py           #   LoginRequest, TokenResponse
│   │   └── security.py          #   JWT encode/decode, password hash
│   │
│   ├── users/                   # Module: User & Role management
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py            #   AppUser, AppRole, UserRole, etc.
│   │
│   ├── farms/                   # Module: Farm master data
│   │   ├── router.py            #   /farms, /farms/{id}/areas, /routes, /external-risk-points
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py            #   Farm, FarmArea, FarmRoute, ExternalRiskPoint
│   │
│   ├── floorplans/              # Module: Floorplan / Digital Twin
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py            #   FloorplanVersion, FloorplanMarker
│   │
│   ├── scorecards/              # Module: Scorecard template
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py            #   ScorecardTemplate, Section, Item
│   │
│   ├── assessments/             # Module: Assessment & Spider Chart
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py            #   Assessment, AssessmentItemResult
│   │
│   ├── killer_metrics/          # Module: Killer Metric Definition & Event
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py
│   │
│   ├── trust_scores/            # Module: Trust Score
│   │   ├── router.py
│   │   ├── service.py           #   FR-09a algorithm implementation
│   │   ├── schemas.py
│   │   └── models.py            #   TrustScoreSnapshot
│   │
│   ├── cases/                   # Module: Risk Case & RCA
│   │   ├── router.py            #   /cases, /cases/{id}/rca-records
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py            #   RiskCase, CaseParticipant, RcaRecord, RcaFactor
│   │
│   ├── tasks/                   # Module: Corrective Task
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── state_machine.py     #   Task status transitions
│   │   ├── schemas.py
│   │   └── models.py            #   CorrectiveTask, TaskAssignee, TaskReview, etc.
│   │
│   ├── attachments/             # Module: Evidence / File upload
│   │   ├── router.py            #   /attachments/presign, /finalize, /download
│   │   ├── service.py           #   MinIO presigned URL, watermark, hash
│   │   ├── schemas.py
│   │   └── models.py            #   Attachment
│   │
│   ├── scars/                   # Module: Scar Memory
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py            #   ScarRecord, ScarLink
│   │
│   ├── lessons/                 # Module: Lesson Learned
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py            #   LessonLearned, LessonReference, SimilarityTag
│   │
│   ├── dashboards/              # Module: Dashboard & Analytics
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   ├── reports/                 # Module: Report generation
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   ├── notifications/           # Module: Notification & Audit Log
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   └── shared/                  # Cross-cutting concerns
│       ├── audit_logger.py      #   Middleware audit log → audit_log table
│       ├── rbac.py              #   Permission checker, scope filter
│       ├── pagination.py        #   Page, PageSize, Sort params
│       ├── exceptions.py        #   Standardized error response
│       ├── optimistic_lock.py   #   ETag / If-Match / version check
│       ├── file_policy.py       #   MIME type, size, rate limit validation
│       └── models_base.py       #   BaseModel with id, created_at, updated_at
│
├── tests/
│   ├── conftest.py              # Fixtures: test DB, test client, auth token
│   ├── factories/               # Test data factories (factory_boy)
│   ├── unit/                    # Unit tests per module
│   ├── integration/             # API integration tests
│   └── e2e/                     # End-to-end scenarios
│
├── pyproject.toml               # Dependencies, linting config
└── Dockerfile                   # Multi-stage build
```

### 2.2 Frontend (Vue.js 3 + JavaScript + PrimeVue 4)

> **⚠️ QUY ƯỚC FRONTEND:**
> - **Composition API only** (`<script setup>`) — không dùng Options API
> - **JavaScript** — không dùng TypeScript (giảm complexity, tăng tốc dev)
> - **PrimeVue 4 latest** — dùng unstyled mode + Tailwind preset hoặc Aura theme; tham khảo PrimeVue 4 docs (không dùng API của PrimeVue 3)
> - **Pinia** cho state management (không Vuex)
> - **Vue Router 4** với `<script setup>` guards
> - File `.vue` dùng `<script setup>`, file logic thuần dùng `.js`
>
> **⚠️ TÁCH LOGIC KHỎI .VUE:**
> - File `.vue` (`<script setup>`) chỉ chứa: import store/composable, bind template, xử lý UI event ngắn gọn.
> - **`services/*.js`** — business logic: gọi API, transform/validate data, xử lý error mapping. Mỗi module 1 file (vd: `authService.js`, `farmService.js`).
> - **`stores/*.js`** — Pinia store: giữ state + actions gọi service. Không gọi `apiClient` trực tiếp trong store.
> - **`api/client.js`** — chỉ chứa axios instance + interceptor. Không chứa logic nghiệp vụ.
> - **`composables/*.js`** — shared reactive logic dùng lại giữa nhiều view (vd: `usePagination`, `useOptimisticLock`).
> - Flow: **View → Store → Service → API client**

```
frontend/
├── public/
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/
│   │   └── index.js             # Vue Router with route guards (RBAC)
│   ├── stores/                  # Pinia stores
│   │   ├── auth.js
│   │   ├── farm.js
│   │   ├── assessment.js
│   │   ├── case.js
│   │   ├── task.js
│   │   └── notification.js
│   │
│   ├── api/                     # Axios instance — transport layer only
│   │   └── client.js            #   Base axios config, interceptors, token refresh
│   │
│   ├── services/                # Business logic — gọi API + transform data
│   │   ├── authService.js
│   │   ├── farmService.js
│   │   ├── assessmentService.js
│   │   ├── caseService.js
│   │   ├── taskService.js
│   │   ├── attachmentService.js
│   │   ├── scarService.js
│   │   ├── lessonService.js
│   │   └── dashboardService.js
│   │
│   ├── views/                   # Page-level components
│   │   ├── auth/
│   │   │   └── LoginView.vue
│   │   ├── dashboard/
│   │   │   └── ExecutiveDashboard.vue
│   │   ├── farms/
│   │   │   ├── FarmListView.vue
│   │   │   └── FarmDetailView.vue
│   │   ├── assessments/
│   │   │   ├── AssessmentListView.vue
│   │   │   ├── AssessmentFormView.vue
│   │   │   └── SpiderChartView.vue
│   │   ├── killer-metrics/
│   │   │   └── KillerMetricEventList.vue
│   │   ├── cases/
│   │   │   ├── CaseQueueView.vue
│   │   │   ├── CaseDetailView.vue
│   │   │   └── RcaWorkspaceView.vue
│   │   ├── tasks/
│   │   │   ├── TaskListView.vue
│   │   │   └── TaskDetailView.vue
│   │   ├── scars/
│   │   │   └── ScarMapView.vue
│   │   ├── lessons/
│   │   │   └── LessonLibraryView.vue
│   │   ├── reports/
│   │   │   └── ReportView.vue
│   │   ├── admin/
│   │   │   ├── UserManagementView.vue
│   │   │   ├── RoleManagementView.vue
│   │   │   └── AuditLogView.vue
│   │   └── notifications/
│   │       └── NotificationListView.vue
│   │
│   ├── components/              # Reusable UI components
│   │   ├── layout/
│   │   │   ├── AppSidebar.vue
│   │   │   ├── AppTopbar.vue
│   │   │   └── AppLayout.vue
│   │   ├── common/
│   │   │   ├── DataTableWrapper.vue
│   │   │   ├── StatusBadge.vue
│   │   │   ├── PriorityBadge.vue
│   │   │   ├── SlaIndicator.vue
│   │   │   ├── ConfidenceBadge.vue
│   │   │   └── FileUploader.vue
│   │   ├── charts/
│   │   │   ├── SpiderChart.vue
│   │   │   ├── TrendChart.vue
│   │   │   └── HeatmapChart.vue
│   │   ├── evidence/
│   │   │   ├── EvidenceGallery.vue
│   │   │   ├── EvidenceReviewPanel.vue
│   │   │   └── WatermarkCameraCapture.vue
│   │   └── floorplan/
│   │       ├── FloorplanCanvas.vue
│   │       └── MarkerOverlay.vue
│   │
│   ├── composables/             # Shared logic (useAuth, usePagination, etc.)
│   │   ├── useAuth.js
│   │   ├── usePagination.js
│   │   ├── useOptimisticLock.js
│   │   └── useFileUpload.js
│   │
│   └── utils/
│       └── formatters.js
│
├── package.json
├── jsconfig.json
├── vite.config.js
├── Dockerfile                   # Multi-stage: node build → nginx serve
└── nginx.conf                   # SPA fallback + reverse proxy /api
```

---

## 3. QUY ƯỚC CHUNG

### 3.1 Quy ước code

| Hạng mục | Quy ước |
|----------|---------|
| **Python style** | `ruff` lint + `ruff format` (thay `black`), `mypy` basic type check |
| **JavaScript style** | `eslint` + `prettier` |
| **Commit message** | Conventional Commits: `feat(module):`, `fix(module):`, `chore:` |
| **Branch strategy** | `main` → `develop` → `feature/{module}-{ticket}` → PR → `develop` |
| **API response** | `{ data: T, meta: { page, page_size, total } }` (list); `{ data: T }` (detail) |
| **Error response** | `{ error: { code: string, message: string, details: any[] }, meta: { request_id, timestamp } }` |
| **Naming** | snake_case (Python, SQL), camelCase (JavaScript, JSON payload) |
| **Enum values** | lowercase snake_case trong DB (`in_progress`), camelCase trong Frontend |

### 3.2 Quy ước Database

| Hạng mục | Quy ước |
|----------|---------|
| **Schema** | Tất cả trong `biosec` schema |
| **PK** | `id UUID DEFAULT gen_random_uuid()` |
| **Timestamps** | `created_at`, `updated_at` (trigger tự động) |
| **Soft delete** | `archived_at TIMESTAMPTZ` (NULL = active) |
| **Optimistic lock** | `version INTEGER DEFAULT 1` |
| **FK convention** | `fk_{table}_{column}` |
| **Index convention** | `idx_{table}_{columns}` |
| **Check convention** | `ck_{table}_{number}` |
| **Unique convention** | `uq_{table}_{columns}` |

### 3.3 Quy ước API

| Hạng mục | Quy ước |
|----------|---------|
| **Base path** | `/api/v1` |
| **Auth** | Bearer JWT trong `Authorization` header |
| **Optimistic lock** | GET trả `ETag` (= version), PATCH yêu cầu `If-Match` header |
| **Idempotency** | POST nhận `Idempotency-Key` header |
| **Pagination** | Query params: `page` (default 1), `page_size` (default 20, max 100), `sort` |
| **Filter** | Query params theo field: `?farm_id=...&status=open&priority=P0` |
| **Upload** | Presigned URL flow: POST `/attachments/presign` → PUT to MinIO → POST `/attachments/{id}/finalize` |

---

## 4. PHÂN PHA TRIỂN KHAI

### Tổng quan 6 Phase — 12 Sprint (mỗi sprint 2 tuần)

```
Phase A ─ Foundation          [Sprint 01–02]   Hạ tầng, Auth, Farm Master Data
Phase B ─ Assessment Core     [Sprint 03–04]   Scorecard, Assessment, Spider Chart, Trust Score
Phase C ─ Case & Task         [Sprint 05–06]   Killer Metric, Case, RCA, Task, Evidence
Phase D ─ Scar & Lesson       [Sprint 07–08]   Scar Memory, Lesson Learned, Digital Twin
Phase E ─ Dashboard & Report  [Sprint 09–10]   Dashboard, Report, Notification, Audit Log
Phase F ─ Harden & Go-Live    [Sprint 11–12]   Performance, Security, UAT, Deploy
```

### Dependency flow

```
Phase A ──→ Phase B ──→ Phase C ──→ Phase D
                                       │
                          Phase E ◄────┘
                             │
                          Phase F
```

---

## 5. CHI TIẾT TỪNG SPRINT

---

### SPRINT 01 — Hạ tầng & Authentication

**Mục tiêu:** Dựng skeleton project, DB migration, Auth module hoạt động đầy đủ.

#### Backend Tasks

| # | Task | FR/NFR | Output | Acceptance Criteria |
|---|------|--------|--------|---------------------|
| B01.1 | Setup project skeleton + Docker Compose | — | `docker-compose.yml`, `.env.example`, Makefile, Backend Dockerfile, Frontend Dockerfile, `main.py`, `config.py`, `database.py` | `make up` → tất cả 6 services healthy, `curl localhost:8000/health` trả 200 |
| B01.2 | Implement Alembic migration | — | Alembic config + initial migration từ V001 SQL | `alembic upgrade head` tạo đủ tables trong `biosec` schema |
| B01.3 | Seed reference data | — | Seed script tương đương V002 | Roles, permissions, lookup_code, killer_metric_definition có dữ liệu |
| B01.4 | Module `auth`: Login / Refresh / Logout | FR-34, NFR-07 | `POST /auth/login`, `/refresh`, `/logout`, `GET /auth/me` | JWT access (1h) + refresh (7d), bcrypt password hash, token blacklist qua Redis |
| B01.5 | Module `auth`: Password lockout | NFR-07 | `app_user_credential.failed_attempts`, `locked_until` | Sau 5 lần sai → lock 15 phút, exponential backoff |
| B01.6 | RBAC dependency injection | NFR-07 | `get_current_user()`, `require_permission(code)`, scope filter | Endpoint trả 401/403 chính xác theo role + scope |
| B01.7 | Shared: Audit logger middleware | FR-34 | Mọi request ghi vào `audit_log` | Log đủ: actor, action, entity, before/after JSON, IP, user-agent |
| B01.8 | Shared: Error handler & pagination | — | `exceptions.py`, `pagination.py` | Response format đúng spec: `{ error: {code, message}, meta: {} }` |
| B01.9 | Shared: Optimistic lock utility | BR-09, NFR-08 | `optimistic_lock.py` | Raise 409 nếu `If-Match` ≠ `version`; tự tăng version sau UPDATE |

#### Frontend Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| F01.1 | Setup Vue 3 + Vite + PrimeVue 4 + JavaScript | Scaffold project | `npm run dev` chạy, PrimeVue 4 theme load, Composition API |
| F01.2 | Axios client + interceptor | `api/client.js` | Auto attach Bearer token, auto refresh khi 401, redirect login khi refresh fail |
| F01.3 | Login page | `LoginView.vue` | Đăng nhập → lưu token → redirect dashboard |
| F01.4 | App layout shell | `AppLayout.vue`, `AppSidebar.vue`, `AppTopbar.vue` | Sidebar menu theo role, topbar user info + notification bell |
| F01.5 | Route guard (RBAC) | `router/index.js` | Chặn route không có quyền, redirect 403 page |

#### Kiểm thử Sprint 01

- Unit test: Auth service (login success, fail, lockout, refresh, logout)
- Integration test: Full login → access protected endpoint → refresh → logout flow
- RBAC test: SYSTEM_ADMIN truy cập tất cả, VIEWER chỉ đọc, FARM_MANAGER chỉ farm mình

---

### SPRINT 02 — Farm Master Data & User Management

**Mục tiêu:** CRUD Farm, Area, Route, External Risk Point, User management.

#### Backend Tasks

| # | Task | FR/NFR | Output | Acceptance Criteria |
|---|------|--------|--------|---------------------|
| B02.1 | Module `users`: CRUD user | — | `GET/POST /users`, `GET/PATCH /users/{id}` | Admins quản lý user, filter by region/farm/role |
| B02.2 | Module `users`: Role assignment | — | `POST/DELETE /users/{id}/roles` | Gán role với scope (global/region/farm), kiểm tra conflict |
| B02.3 | Module `farms`: CRUD farm | FR-01 | `GET/POST /farms`, `GET/PATCH /farms/{id}` | Filter by region, type, ownership; RBAC scope |
| B02.4 | Module `farms`: Area management | FR-02 | `GET/POST /farms/{id}/areas`, `PATCH /areas/{id}` | Cây cha-con (parent_area_id), clean/dirty class |
| B02.5 | Module `farms`: Route management | FR-02 | `GET/POST /farms/{id}/routes` | Validate from_area_id, to_area_id thuộc cùng farm |
| B02.6 | Module `farms`: External risk point | FR-02 | `GET/POST /farms/{id}/external-risk-points` | GPS, distance, confidence level |
| B02.7 | Module `regions`: CRUD region | — | `GET/POST /regions`, `GET/PATCH /regions/{id}` | Chỉ SYSTEM_ADMIN tạo/sửa |

#### Frontend Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| F02.1 | Farm listing page | `FarmListView.vue` | DataTable với filter (region, type, ownership), sort, pagination |
| F02.2 | Farm profile page | `FarmDetailView.vue` | Header info + tabs: Overview, Areas, Routes, Floorplan(placeholder) |
| F02.3 | Farm create/edit form | Dialog/modal | Validate required fields, dropdown cho region/type/ownership |
| F02.4 | Area tree component | Nested tree trong Farm Profile | Hiển thị cây area, CRUD inline, drag-drop nếu cần |
| F02.5 | User management page | `UserManagementView.vue` | DataTable CRUD user, role assignment dialog |
| F02.6 | Reusable components | `StatusBadge`, `PriorityBadge`, `DataTableWrapper` | Dùng được cho tất cả module sau |

#### Kiểm thử Sprint 02

- CRUD test đủ cho farms, areas, routes, users, roles
- RBAC test: FARM_MANAGER chỉ thấy farm mình, REGION_MANAGER thấy farm trong region
- Validation test: Missing required fields, invalid enum values

---

### SPRINT 03 — Scorecard & Assessment Entry

**Mục tiêu:** Scorecard template builder, Assessment entry form, tính điểm.

#### Backend Tasks

| # | Task | FR/NFR | Output | Acceptance Criteria |
|---|------|--------|--------|---------------------|
| B03.1 | Module `scorecards`: Template CRUD | FR-04, FR-05 | `GET/POST /scorecard-templates`, activate, archive | Template có version, status (draft/active/archived), filter by farm_type |
| B03.2 | Module `scorecards`: Section & Item CRUD | FR-04 | Nested CRUD sections → items | Weight validation (tổng weight = 1.0 mỗi level), threshold_warning < threshold_fail |
| B03.3 | Module `assessments`: Create assessment | FR-06 | `POST /assessments` | Snapshot template_id tại thời điểm tạo (BR-07), validate assessment_type |
| B03.4 | Module `assessments`: Bulk upsert item results | FR-06 | `POST /assessments/{id}/items/bulk-upsert` | Gửi list item results, validate item thuộc template, tính awarded_score |
| B03.5 | Module `assessments`: Submit assessment | FR-06 | `POST /assessments/{id}/submit` | Transition draft → submitted, tính overall + 4 section scores |
| B03.6 | Module `assessments`: Score calculation | FR-06, FR-07 | Service method | `overall_score`, `hardware_score`, `process_score`, `behavior_score`, `monitoring_score` tính đúng từ weights |
| B03.7 | Module `assessments`: Spider chart data | FR-07 | `GET /assessments/{id}/spider-chart` | Trả 4 trục score + optional comparison assessment |
| B03.8 | Assessment state machine | FR-06 | draft → submitted → reviewed → locked | Validate transition hợp lệ, version check |

#### Frontend Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| F03.1 | Scorecard template builder | Admin page | Tạo template → sections → items, drag-drop reorder, preview |
| F03.2 | Assessment entry form | `AssessmentFormView.vue` | Progressive form: chọn farm → template auto-select → fill từng section → photo attach → submit |
| F03.3 | Section navigator | Sidebar trong assessment form | Hiện progress % mỗi section, click nhảy section |
| F03.4 | Assessment list page | `AssessmentListView.vue` | Filter by farm, type, date range, status; sort by date/score |
| F03.5 | Spider Chart component | `SpiderChart.vue` (ECharts) | 4 trục radar, toggle self/audit overlay, tooltip score |

#### Kiểm thử Sprint 03

- Score calculation: Verify weight-based scoring với nhiều dataset
- Template snapshot: Sửa template sau khi assessment tạo → assessment không bị ảnh hưởng
- State machine: Chỉ transition hợp lệ, reject invalid transitions

---

### SPRINT 04 — Trust Score & Killer Metrics

**Mục tiêu:** Trust Score algorithm (FR-09a), Killer Metric definitions & events.

#### Backend Tasks

| # | Task | FR/NFR | Output | Acceptance Criteria |
|---|------|--------|--------|---------------------|
| B04.1 | Module `trust_scores`: Calculate | FR-09, FR-09a | `POST /trust-scores/calculate` | Input: self_assessment_id + audit_assessment_id → trả Trust Score đúng formula |
| B04.2 | Trust Score formula | FR-09a | Implement đúng: `max(0, 100 - \|gap\| × penalty × severity_factor)` | penalty=1.5 nếu gap>0, 1.0 nếu gap≤0; severity_factor=1.0 Phase 1 |
| B04.3 | Trust Score snapshot storage | FR-09a | Lưu vào `trust_score_snapshot` | Lưu trust_score, absolute_gap_score, severity_factor, snapshot_date |
| B04.4 | Get latest trust score | FR-09 | `GET /farms/{id}/trust-score/latest` | Trả snapshot mới nhất cho farm |
| B04.5 | Module `killer_metrics`: Definition CRUD | FR-08 | `GET/POST /killer-metric-definitions`, `PATCH /{id}` | Admin quản lý, có severity_level, default_case_priority |
| B04.6 | Module `killer_metrics`: Event CRUD | FR-08 | `GET/POST /killer-metric-events`, `GET/PATCH /{id}` | Tạo event → auto status `open`, validate definition_id |
| B04.7 | Killer Metric Event state machine | FR-08 | open → under_review → contained → closed | BR-03: Phải có case trước khi close |
| B04.8 | Killer Metric → Auto alert | FR-29 | Khi tạo killer event → tạo notification | Alert đến expert + region manager |

#### Frontend Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| F04.1 | Trust Score display | Thêm vào Farm Profile + Dashboard | Badge màu (xanh ≥80, vàng 60-79, đỏ <60) |
| F04.2 | Trust Score comparison | Spider Chart overlay | Self vs Audit overlay trên spider chart |
| F04.3 | Killer Metric definition admin | Admin page | CRUD definitions, severity badge |
| F04.4 | Killer Metric event list | `KillerMetricEventList.vue` | Filter by farm, status, severity; SLA indicator |

#### Kiểm thử Sprint 04

- Trust Score: Verify tất cả ví dụ trong FR-09a (92/90→97, 60/95→65, 95/60→47.5, 80/80→100)
- Killer event: Tạo event → notification gửi → event không close được khi chưa có case

---

### SPRINT 05 — Risk Case & RCA

**Mục tiêu:** Case management, RCA workspace, case queue cho expert.

#### Backend Tasks

| # | Task | FR/NFR | Output | Acceptance Criteria |
|---|------|--------|--------|---------------------|
| B05.1 | Module `cases`: Create case | FR-10 | `POST /cases` | Source: assessment, killer_event, scar, hoặc manual; auto generate case_no |
| B05.2 | Module `cases`: Case queue | FR-11 | `GET /cases/queue/review` | Filter: pending, priority, region, SLA; chỉ expert thấy |
| B05.3 | Module `cases`: Case detail & timeline | FR-35 | `GET /cases/{id}`, `/timeline` | Timeline: all events chronological (assessment → case → rca → tasks → evidence → scar) |
| B05.4 | Case state machine | FR-10 | open → triage → in_analysis → actioning → monitoring → closed/cancelled | Version check, validate transitions |
| B05.5 | Module `cases`: Assign expert | FR-11 | `POST /cases/{id}/assign-expert` | Chỉ admin/region_manager gán, validate expert role |
| B05.6 | Module `cases`: RCA record CRUD | FR-12, FR-13 | `GET/POST /cases/{id}/rca-records`, `PATCH /rca-records/{id}` | Support 5Why, Fishbone, CAPA methods |
| B05.7 | Module `cases`: RCA factors | FR-13 | `POST/PATCH /rca-records/{id}/factors`, `DELETE /rca-factors/{id}` | Factor groups: people, process, place, equipment, environment, monitoring, external |
| B05.8 | Module `cases`: RCA approve | FR-12 | `POST /rca-records/{id}/approve` | Chỉ expert approved_by, set approved_at |
| B05.9 | Case → Killer event link | BR-03, FR-08 | Auto liên kết | Nếu case từ killer event → killer event chuyển under_review |

#### Frontend Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| F05.1 | Case queue page | `CaseQueueView.vue` | Sortable table, SLA countdown, priority badge, quick preview panel |
| F05.2 | Case detail page | `CaseDetailView.vue` | Header info + tabs: Summary, RCA, Tasks, Timeline, Participants |
| F05.3 | RCA workspace | `RcaWorkspaceView.vue` | Method selector (5Why/Fishbone/CAPA), factor entry form, approve button |
| F05.4 | Case timeline | Timeline component | Vertical timeline, icon per event type, expandable detail |
| F05.5 | Case create dialog | Modal from assessment/killer event | Pre-fill source, select priority, assign expert |

#### Kiểm thử Sprint 05

- Case lifecycle: open → triage → in_analysis → actioning → monitoring → closed
- BR-03: Killer event case phải review trước khi close
- RBAC: Chỉ expert tạo RCA, chỉ expert approve
- Timeline: Verify đủ events theo thứ tự thời gian

---

### SPRINT 06 — Corrective Task & Evidence

**Mục tiêu:** Task management, evidence upload/review, task state machine.

#### Backend Tasks

| # | Task | FR/NFR | Output | Acceptance Criteria |
|---|------|--------|--------|---------------------|
| B06.1 | Module `tasks`: Create task | FR-14 | `POST /tasks` | Phải linked to case, có source_rca_id; BR-02: không auto-generate từ score |
| B06.2 | Module `tasks`: Task state machine | FR-17 | open → accepted → in_progress → pending_review → closed/cancelled; needs_rework loop | Version check, validate mỗi transition |
| B06.3 | Module `tasks`: Assignee CRUD | FR-14 | `POST/DELETE /tasks/{id}/assignees` | Responsibility type: owner, support, approver |
| B06.4 | Module `tasks`: Submit for review | FR-21 | `POST /tasks/{id}/submit-for-review` | Transition in_progress → pending_review, yêu cầu ít nhất 1 evidence |
| B06.5 | Module `tasks`: Review (approve/reject) | FR-21, FR-22 | `POST /tasks/{id}/reviews` | BR-04: Không close khi chưa có evidence + expert review |
| B06.6 | Module `tasks`: Comments | FR-14 | `POST /tasks/{id}/comments` | Comment type: note, question, update |
| B06.7 | Module `attachments`: Presigned URL | FR-19 | `POST /attachments/presign` | Return presigned PUT URL, validate upload policy (NFR-08a) |
| B06.8 | Module `attachments`: Finalize | FR-20, FR-23 | `POST /attachments/{id}/finalize` | Tính SHA256 hash, store watermark metadata, validate MIME + size |
| B06.9 | Module `attachments`: Download | FR-19 | `GET /attachments/{id}/download` | Presigned GET URL, RBAC check |
| B06.10 | Module `attachments`: Soft delete | NFR-06a, NFR-08 | `DELETE /attachments/{id}` | Set archived_at, không xóa physical file |
| B06.11 | Upload policy enforcement | NFR-08a | `file_policy.py` | MIME whitelist, 50MB image/500MB video/20MB PDF, 30 files/min rate limit |
| B06.12 | Task escalation rules | FR-18 | Background check hoặc n8n trigger | Auto alert nếu overdue, missing evidence, repeated rejection |

#### Frontend Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| F06.1 | Task list page | `TaskListView.vue` | Filter by case, status, priority, assignee; SLA indicator |
| F06.2 | Task detail page | `TaskDetailView.vue` | Info, criteria, evidence gallery, review history, action buttons |
| F06.3 | Task create form | Dialog trong Case detail | Fill title, description, criteria, evidence requirement, SLA, assignees |
| F06.4 | File uploader component | `FileUploader.vue` | Presigned URL flow, progress bar, MIME/size validation client-side |
| F06.5 | Evidence gallery | `EvidenceGallery.vue` | Grid/list view, lightbox preview, metadata overlay (hash, GPS, time) |
| F06.6 | Evidence review panel | `EvidenceReviewPanel.vue` | Approve/reject buttons, review note, rework deadline |
| F06.7 | Task status transition buttons | Bottom bar | Chỉ hiện button hợp lệ theo state machine + role |

#### Kiểm thử Sprint 06

- Task lifecycle: full happy path + rework loop
- BR-04: Task không close khi chưa có evidence + approved review
- Upload policy: Reject file sai MIME, quá size, vượt rate limit
- Evidence integrity: SHA256 hash consistent, watermark data lưu đúng

---

### SPRINT 07 — Scar Memory & Digital Twin

**Mục tiêu:** Scar record, scar map trên floorplan, digital twin visualization.

#### Backend Tasks

| # | Task | FR/NFR | Output | Acceptance Criteria |
|---|------|--------|--------|---------------------|
| B07.1 | Module `floorplans`: CRUD | FR-03 | `GET/POST /farms/{id}/floorplans`, `GET/PATCH /floorplans/{id}` | Version management, status (draft/active/archived) |
| B07.2 | Module `floorplans`: Markers | FR-24 | `GET/POST /floorplans/{id}/markers`, `PATCH/DELETE /{marker_id}` | x_percent, y_percent, marker_type, metadata_json |
| B07.3 | Module `scars`: CRUD scar record | FR-25 | `GET/POST /scars`, `GET/PATCH /scars/{id}` | scar_type, confidence_level, x_percent/y_percent, recurrence tracking |
| B07.4 | Module `scars`: Validate scar | FR-28, BR-05 | `POST /scars/{id}/validate` | Chỉ authorized user validate, transition suspected → confirmed |
| B07.5 | Module `scars`: Scar links | FR-25 | `POST /scars/{id}/links` | Polymorphic link to case/task/assessment/attachment; BR-08: validate at app layer |
| B07.6 | Module `scars`: Scar map data | FR-24 | `GET /farms/{id}/scar-map` | Trả floorplan + all scars + markers, filter by date range, type, confidence |
| B07.7 | Scar recurrence detection | FR-25 | Service method | Auto increment recurrence_count khi tạo scar cùng area + type |

#### Frontend Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| F07.1 | Floorplan upload & management | Tab trong Farm Profile | Upload image, manage versions, activate/archive |
| F07.2 | Floorplan canvas component | `FloorplanCanvas.vue` | Load image, zoom/pan, marker overlay, click to add |
| F07.3 | Scar map page | `ScarMapView.vue` | Floorplan + colored markers per scar type/confidence, filter panel, click → detail drawer |
| F07.4 | Scar detail drawer | Side drawer | Scar info, linked cases/tasks, confidence badge, validate button |
| F07.5 | Marker overlay | `MarkerOverlay.vue` | Icon per type, pulsing animation for active scars, tooltip on hover |

#### Kiểm thử Sprint 07

- Polymorphic link: Validate tất cả link types (case, task, assessment, attachment)
- Scar confidence: Chỉ authorized user validate
- Scar map: Load floorplan + overlay markers chính xác vị trí
- Recurrence: Tạo scar cùng area/type → count tăng

---

### SPRINT 08 — Lesson Learned & Knowledge

**Mục tiêu:** Lesson library, similar search, knowledge confidence.

#### Backend Tasks

| # | Task | FR/NFR | Output | Acceptance Criteria |
|---|------|--------|--------|---------------------|
| B08.1 | Module `lessons`: CRUD | FR-26 | `GET/POST /lessons`, `GET/PATCH /lessons/{id}` | Lesson structure: problem → root_cause → action → outcome |
| B08.2 | Module `lessons`: Validate | FR-28, BR-05 | `POST /lessons/{id}/validate` | draft → validated, yêu cầu confirmed_by + ít nhất 1 reference |
| B08.3 | Module `lessons`: References | FR-26 | `POST /lessons/{id}/references` | Polymorphic ref to scar/case/task/assessment; BR-08 validate |
| B08.4 | Module `lessons`: Similarity tags | FR-27 | `POST /lessons/{id}/tags` | Tag types: farm_type, issue_type, route_type, season, etc. |
| B08.5 | Module `lessons`: Similar search | FR-27 | `GET /lessons/search/similar` | Filter by tags, applicability_scope, confidence_level; ranked results |
| B08.6 | Lesson confidence workflow | FR-28 | draft → validated → archived/obsolete | Prevent rumor: chỉ validated mới hiện trong search mặc định |

#### Frontend Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| F08.1 | Lesson library page | `LessonLibraryView.vue` | Search/filter bar, result list with confidence badges, detail drawer |
| F08.2 | Lesson create/edit form | Dialog | Structured form: problem → root cause → action → outcome |
| F08.3 | Lesson detail drawer | Side drawer | Full info, references (clickable links to case/scar), similar lessons |
| F08.4 | Similar search panel | Trong lesson library | Tag-based filter, relevance ranking, "Apply to my case" button |
| F08.5 | Thêm tab Lessons vào Farm Profile | Tab trong Farm Detail | Lessons áp dụng cho farm, sorted by relevance |

#### Kiểm thử Sprint 08

- Lesson lifecycle: draft → validated → archived
- Similar search: Verify tag matching, kết quả đúng
- Reference validation: Polymorphic FK types tất cả valid
- BR-05: Chỉ validated lessons hiện mặc định

---

### SPRINT 09 — Dashboard & Analytics

**Mục tiêu:** Executive dashboard, farm dashboard, benchmark, trend visualization.

#### Backend Tasks

| # | Task | FR/NFR | Output | Acceptance Criteria |
|---|------|--------|--------|---------------------|
| B09.1 | Dashboard: Executive summary | FR-31 | `GET /dashboards/executive-summary` | System-wide KPIs: avg score, open cases, overdue tasks, trust distribution |
| B09.2 | Dashboard: Farm detail | FR-31 | `GET /dashboards/farm/{id}` | Farm-specific: scores over time, open cases/tasks, scars, trust trend |
| B09.3 | Dashboard: Benchmark | FR-31 | `GET /dashboards/benchmark` | Farm comparison: score by type, rank, percentile |
| B09.4 | Dashboard: Trust gaps | FR-09, FR-31 | `GET /dashboards/trust-gaps` | Farms sorted by trust score, highlight low trust (<60) |
| B09.5 | Dashboard: Killer metrics trend | FR-08, FR-31 | `GET /dashboards/killer-metrics-trend` | Timeline chart of events by type, farm, status |
| B09.6 | Dashboard: Scar hotspots | FR-24, FR-31 | `GET /dashboards/scar-hotspots` | Aggregated scar count by area type, farm, recurrence |
| B09.7 | Redis caching cho dashboard | NFR-02 | Cache dashboard results 5 phút | P95 ≤ 3s |

#### Frontend Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| F09.1 | Executive dashboard page | `ExecutiveDashboard.vue` | KPI cards (live numbers), trend charts, risk heatmap, backlog summary |
| F09.2 | Trend chart component | `TrendChart.vue` | ECharts line/bar chart, date range selector, multi-series |
| F09.3 | Heatmap chart | `HeatmapChart.vue` | Farm × section score heatmap, color gradient |
| F09.4 | Trust gap view | Section trong dashboard | Ranked farm list, color-coded trust badge |
| F09.5 | Killer metric trend chart | Section trong dashboard | Stacked area chart theo thời gian |
| F09.6 | Farm dashboard tab | Thêm vào Farm Profile | Overview tab với KPI, spider chart, trends |

#### Kiểm thử Sprint 09

- Dashboard performance: P95 ≤ 3s với 20 farms, 5000 assessments
- Data accuracy: Dashboard numbers match raw query
- RBAC: FARM_MANAGER chỉ thấy farm mình, REGION_MANAGER thấy region mình

---

### SPRINT 10 — Reports, Notifications & Audit Log

**Mục tiêu:** Report generation, notification system, audit log admin.

#### Backend Tasks

| # | Task | FR/NFR | Output | Acceptance Criteria |
|---|------|--------|--------|---------------------|
| B10.1 | Module `reports`: Generate report | FR-32, FR-33 | `POST /reports` | Monthly biosecurity summary, backlog, trust gap, killer metric report |
| B10.2 | Module `reports`: PDF export | FR-33 | `GET /reports/{id}/download` | WeasyPrint hoặc ReportLab, đúng format |
| B10.3 | Module `reports`: Excel/CSV export | FR-33 | `GET /reports/{id}/download?format=xlsx` | openpyxl output |
| B10.4 | Module `notifications`: CRUD | FR-29, FR-30 | `GET /notifications`, mark read | In-app notification list, filter unread |
| B10.5 | Module `notifications`: Trigger rules | FR-29 | Service events → notification | Low score, killer event, overdue task, case status change |
| B10.6 | n8n integration for email | FR-30 | n8n webhook trigger | n8n workflow nhận event → send email template |
| B10.7 | Audit log admin API | FR-34 | `GET /audit-logs` | Filter by actor, action, entity, date range; paginated |

#### Frontend Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| F10.1 | Report page | `ReportView.vue` | Chọn loại report → date range → farm/region → generate → download |
| F10.2 | Notification dropdown | Bell icon trong topbar | Badge count, dropdown danh sách, mark read, click → navigate to entity |
| F10.3 | Notification list page | `NotificationListView.vue` | Full list, filter by type, bulk mark read |
| F10.4 | Audit log admin page | `AuditLogView.vue` | DataTable, filter by action/entity/date, detail drawer (before/after JSON diff) |

#### Kiểm thử Sprint 10

- Report: Verify data accuracy trong PDF/Excel
- Notification: Trigger rule → notification created → user sees it
- Audit log: Mọi CRUD action đều log đủ thông tin
- n8n: Email gửi thành công (mock SMTP)

---

### SPRINT 11 — Performance, Security & Mobile

**Mục tiêu:** Tối ưu hiệu năng, hardening bảo mật, responsive mobile.

#### Tasks

| # | Task | NFR | Output | Acceptance Criteria |
|---|------|-----|--------|---------------------|
| 11.1 | Database query optimization | NFR-02 | EXPLAIN ANALYZE cho top 20 queries | Tất cả P95 ≤ 500ms |
| 11.2 | Redis caching strategy | NFR-02 | Cache lookup_code, scorecard_template, dashboard | Cache hit ratio > 80% |
| 11.3 | Connection pooling tuning | NFR-01 | SQLAlchemy pool_size, max_overflow | Handle 100 concurrent users |
| 11.4 | API rate limiting | NFR-08a | Redis-based rate limiter | Global: 100 req/min/user, Upload: 30 files/min/user |
| 11.5 | Security audit | NFR-07 | OWASP Top 10 checklist | SQL injection, XSS, CSRF, auth bypass — tất cả PASS |
| 11.6 | TLS configuration | NFR-07 | Nginx TLS 1.2+, HSTS, CSP headers | SSL Labs grade A |
| 11.7 | Mobile responsive UI | NFR-03, NFR-09 | CSS responsive cho tất cả pages | Hoạt động trên mobile 375px+, touch-friendly buttons |
| 11.8 | Evidence capture (mobile) | FR-20 | Camera capture with watermark | GPS + timestamp + user info overlay trên photo |
| 11.9 | Offline queue (basic) | NFR-10 | Service worker + IndexedDB queue | Lưu pending actions khi offline, retry khi online |
| 11.10 | Penetration testing | NFR-07 | Test report | Không có critical/high vulnerability |

---

### SPRINT 12 — UAT, Bug Fix & Go-Live

**Mục tiêu:** User Acceptance Testing, fix bugs, deploy production.

#### Tasks

| # | Task | Output | Acceptance Criteria |
|---|------|--------|---------------------|
| 12.1 | UAT test plan | Tài liệu test plan | Cover tất cả FR, BR, state machines |
| 12.2 | UAT execution (2 tuần) | Bug report list | User (expert, farm manager, admin) test trên staging |
| 12.3 | Bug fix — critical/high | Code fixes | Tất cả P0/P1 bugs resolved |
| 12.4 | Bug fix — medium/low | Code fixes | P2 resolved, P3 accept/defer |
| 12.5 | Data migration (nếu có) | Migration script | Dữ liệu cũ import đúng vào hệ thống mới |
| 12.6 | Production deploy | Running system | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build` trên production server |
| 12.7 | Monitoring setup | Prometheus + Grafana, Sentry | Alert khi error rate > 1%, P95 > 3s |
| 12.8 | User training | Training session | Farm managers, experts, admins biết sử dụng |
| 12.9 | Operation handbook | Tài liệu vận hành | Backup, restore, troubleshooting, escalation |
| 12.10 | Go-live sign-off | Approval document | Stakeholder ký duyệt |

---

## 6. MA TRẬN PHỤ THUỘC GIỮA CÁC MODULE

```
Module                Phụ thuộc vào
──────────────────    ─────────────────────────────────
auth                  (không phụ thuộc)
users                 auth
regions               auth
farms                 auth, regions
floorplans            farms, attachments
scorecards            auth
assessments           farms, scorecards, attachments
killer_metrics        farms
trust_scores          assessments
cases                 farms, assessments, killer_metrics
tasks                 cases, attachments
scars                 farms, floorplans, cases, tasks, assessments
lessons               scars, cases, tasks, assessments
dashboards            assessments, cases, tasks, trust_scores, scars, killer_metrics
reports               dashboards
notifications         cases, tasks, killer_metrics, assessments
```

### Sơ đồ dependency (bottom-up build order)

```
Layer 0:  auth
Layer 1:  users, regions
Layer 2:  farms, scorecards
Layer 3:  floorplans, assessments, killer_metrics
Layer 4:  trust_scores, cases
Layer 5:  tasks
Layer 6:  scars
Layer 7:  lessons
Layer 8:  dashboards, notifications
Layer 9:  reports
```

---

## 7. CHIẾN LƯỢC KIỂM THỬ

### 7.1 Các tầng kiểm thử

| Tầng | Công cụ | Coverage target | Chạy khi nào |
|------|---------|----------------|--------------|
| **Unit test** | pytest + pytest-asyncio | ≥ 80% business logic | Mỗi commit |
| **Integration test** | pytest + httpx (TestClient) | ≥ 70% API endpoints | Mỗi PR |
| **E2E test** | Playwright (hoặc Cypress) | Critical paths (10 scenarios) | Nightly + trước release |
| **Performance test** | Locust hoặc k6 | NFR-01, NFR-02 benchmarks | Sprint 11 |
| **Security test** | OWASP ZAP, manual pentest | OWASP Top 10 | Sprint 11 |

### 7.2 Critical E2E scenarios

| # | Scenario | Covers |
|---|----------|--------|
| 1 | Login → Farm list → Farm profile | Auth, RBAC, Farm |
| 2 | Create assessment → Fill scores → Submit → Spider chart | Scorecard, Assessment, Score calculation |
| 3 | Calculate trust score (self vs audit) | Trust Score FR-09a |
| 4 | Killer event → Auto alert → Create case | Killer Metric, Notification, Case |
| 5 | Case → Triage → RCA → Create task | Case state machine, RCA, Task |
| 6 | Task → Upload evidence → Submit review → Approve → Close | Task state machine, Evidence, Review |
| 7 | Create scar → Link to case → View on scar map | Scar, Floorplan, Polymorphic FK |
| 8 | Create lesson → Add references → Validate → Search similar | Lesson, Tags, Confidence |
| 9 | Executive dashboard loads in ≤ 3s | Dashboard, Performance |
| 10 | Full traceability: assessment → case → task → scar → lesson | FR-35 |

### 7.3 Test data strategy

- **Factory pattern:** Dùng `factory_boy` (Python) tạo test data
- **Fixtures:** `conftest.py` cung cấp: test DB schema, auth tokens per role, base farm/user data
- **Seed script:** Reuse V002 seed data cho integration test

---

## 8. HẠ TẦNG & DEVOPS

### 8.1 Môi trường

| Env | Mục đích | Cấu hình |
|-----|---------|----------|
| **Local** | Dev | `docker compose up` — FastAPI (hot-reload) + Vue (HMR) + Postgres + Redis + MinIO + n8n |
| **Staging** | QA + UAT | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` trên server nội bộ, data gần prod |
| **Production** | Go-live | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` + TLS + backup cron |

### 8.2 Docker Compose (chi tiết)

#### `docker-compose.yml` (Development)

```yaml
version: "3.9"

services:
  # ── DATABASE ──────────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-biosecurity}
      POSTGRES_USER: ${POSTGRES_USER:-biosec}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-biosec_dev_2026}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-biosec}"]
      interval: 5s
      retries: 5

  # ── CACHE ─────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD:-redis_dev}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "${REDIS_PASSWORD:-redis_dev}", "ping"]
      interval: 5s
      retries: 5

  # ── OBJECT STORAGE ────────────────────────────────────────
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minio_dev}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minio_dev_2026}
    ports:
      - "9000:9000"   # API
      - "9001:9001"   # Console
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      retries: 3

  # ── BACKEND (FastAPI) ─────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development           # Dev stage: uvicorn --reload
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-biosec}:${POSTGRES_PASSWORD:-biosec_dev_2026}@postgres:5432/${POSTGRES_DB:-biosecurity}
      REDIS_URL: redis://:${REDIS_PASSWORD:-redis_dev}@redis:6379/0
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER:-minio_dev}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-minio_dev_2026}
      MINIO_BUCKET: ${MINIO_BUCKET:-biosec-evidence}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-dev-secret-change-in-prod}
      ENVIRONMENT: development
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app/app       # Hot-reload: code thay đổi → tự restart
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      retries: 3

  # ── FRONTEND (Vue.js 3 dev server) ───────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development           # Dev stage: vite dev server
    environment:
      VITE_API_BASE_URL: http://localhost:8000/api/v1
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src     # HMR: code thay đổi → tự cập nhật browser
    depends_on:
      - backend

  # ── n8n (Notification workflow) ──────────────────────────
  n8n:
    image: n8nio/n8n:latest
    environment:
      N8N_BASIC_AUTH_ACTIVE: "true"
      N8N_BASIC_AUTH_USER: ${N8N_USER:-admin}
      N8N_BASIC_AUTH_PASSWORD: ${N8N_PASSWORD:-n8n_dev_2026}
      WEBHOOK_URL: http://n8n:5678
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  postgres_data:
  redis_data:
  minio_data:
  n8n_data:
```

#### `docker-compose.prod.yml` (Production override)

```yaml
# Chạy: docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
version: "3.9"

services:
  backend:
    build:
      target: production             # Prod stage: gunicorn + uvicorn worker
    environment:
      ENVIRONMENT: production
    restart: always
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G

  frontend:
    build:
      target: production             # Prod stage: nginx serving static build
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/certs:/etc/nginx/certs:ro
    restart: always

  postgres:
    restart: always
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 4G

  redis:
    restart: always

  minio:
    restart: always

  n8n:
    restart: always
```

#### `.env.example`

```bash
# ── Database
POSTGRES_DB=biosecurity
POSTGRES_USER=biosec
POSTGRES_PASSWORD=your_password

# ── Redis
REDIS_PASSWORD=your_password

# ── MinIO
MINIO_ROOT_USER=minio_admin
MINIO_ROOT_PASSWORD=your_password
MINIO_BUCKET=biosec-evidence

# ── JWT
JWT_SECRET_KEY="ee379553c1ed96c8d4a97119cb628ab83c0c043097462b65ad65e499408ad29d"#(openssl rand -hex 32)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ── n8n
N8N_USER=admin
N8N_PASSWORD=your_password

# ── App
ENVIRONMENT=development    # development | staging | production
```

#### Dockerfile — Backend (multi-stage)

```dockerfile
# ── Stage 1: Base ───────────────────────────────────────────
FROM python:3.12-slim AS base
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .

# ── Stage 2: Development (uvicorn --reload) ─────────────────
FROM base AS development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Stage 3: Production (gunicorn + uvicorn workers) ────────
FROM base AS production
RUN pip install gunicorn
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
```

#### Dockerfile — Frontend (multi-stage)

```dockerfile
# ── Stage 1: Dependencies ───────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ── Stage 2: Development (Vite dev server + HMR) ───────────
FROM deps AS development
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ── Stage 3: Build ──────────────────────────────────────────
FROM deps AS build
COPY . .
RUN npm run build

# ── Stage 4: Production (Nginx serving static files) ────────
FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80 443
```

#### Makefile (dev shortcuts)

```makefile
.PHONY: up down logs migrate seed reset test lint

up:                              ## Khởi động tất cả services
	docker compose up -d

up-build:                        ## Build lại images rồi khởi động
	docker compose up -d --build

down:                            ## Dừng tất cả services
	docker compose down

reset:                           ## Xóa volumes, khởi tạo lại từ đầu
	docker compose down -v
	docker compose up -d --build

logs:                            ## Xem logs realtime
	docker compose logs -f backend frontend

logs-all:                        ## Xem logs tất cả services
	docker compose logs -f

migrate:                         ## Chạy DB migration
	docker compose exec backend alembic upgrade head

seed:                            ## Seed reference data
	docker compose exec postgres psql -U biosec -d biosecurity -f /docker-entrypoint-initdb.d/V002_seed.sql

test:                            ## Chạy test suite
	docker compose exec backend pytest --cov=app --cov-report=term-missing

lint:                            ## Lint backend + frontend
	docker compose exec backend ruff check .
	docker compose exec frontend npm run lint

shell-be:                        ## SSH vào backend container
	docker compose exec backend bash

shell-db:                        ## Kết nối psql
	docker compose exec postgres psql -U biosec -d biosecurity

prod-up:                         ## Deploy production
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:                       ## Dừng production
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### 8.3 CI/CD Pipeline

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐
│  Commit  │───▶│  Lint &  │───▶│  Unit &  │───▶│  Build   │───▶│ Deploy  │
│  Push    │    │  Format  │    │  Integ.  │    │  Docker  │    │ Staging │
└─────────┘    │  Check   │    │  Tests   │    │  Images  │    └────┬────┘
               └──────────┘    └──────────┘    └──────────┘         │
                                                              ┌─────▼─────┐
                                                              │  Manual   │
                                                              │  Promote  │
                                                              │  to Prod  │
                                                              └───────────┘
```

**Pipeline steps:**
1. **Lint:** `ruff check`, `eslint`
2. **Test:** `pytest` (unit + integration), coverage report
3. **Build:** Docker images cho backend + frontend
4. **Deploy Staging:** Auto deploy khi merge vào `develop`
5. **Deploy Prod:** Manual trigger khi release, sau UAT approval

### 8.4 Backup & Recovery

| Hạng mục | Chiến lược | Tần suất | Lưu trữ |
|----------|-----------|---------|---------|
| **PostgreSQL** | `pg_dump` compressed | Daily 02:00 | 30 ngày retention, offsite copy |
| **MinIO** | Bucket replication | Continuous | Mirror bucket |
| **Config** | Git repository | Mỗi commit | Git history |
| **RPO** | ≤ 1 giờ | WAL archiving | — |
| **RTO** | ≤ 4 giờ | Restore playbook tested monthly | — |

### 8.5 Monitoring

| Tool | Mục đích |
|------|---------|
| **Prometheus + Grafana** | Metrics: request rate, latency, error rate, DB connections, Redis hit ratio |
| **Sentry** | Error tracking, exception alerts |
| **PostgreSQL pg_stat** | Slow query log (> 200ms), connection pool usage |
| **Uptime monitor** | Healthcheck endpoint, alert if down > 5 min |

---

## 9. RỦI RO & BIỆN PHÁP GIẢM THIỂU

| # | Rủi ro | Xác suất | Tác động | Biện pháp |
|---|--------|----------|----------|-----------|
| R1 | User adoption thấp (farm manager không quen công nghệ) | Cao | Cao | UI field-friendly (nút lớn, workflow ngắn), training hands-on, hỗ trợ onsite |
| R2 | Kết nối mạng yếu tại farm | Cao | Trung bình | Offline queue + retry (Sprint 11), photo compress trước upload |
| R3 | Data quality thấp (self-assessment không trung thực) | Cao | Cao | Trust Score algorithm detect gap, blind audit random, scar memory cross-check |
| R4 | Scope creep (yêu cầu AI/auto-task trong Phase 1) | Trung bình | Cao | Tài liệu rõ "NOT in Phase 1", backlog Phase 2 items riêng |
| R5 | Performance chậm với dữ liệu lớn | Thấp | Trung bình | Indexing strategy đã thiết kế, Redis cache, pagination enforce |
| R6 | Evidence file lớn (video 500MB) | Trung bình | Trung bình | Presigned URL direct upload, async processing, CDN nếu cần |
| R7 | Mất dữ liệu | Thấp | Rất cao | Daily backup, WAL archiving, soft delete, RPO ≤1h test hàng tháng |
| R8 | Security breach | Thấp | Rất cao | OWASP audit Sprint 11, pentest, RBAC multi-layer, audit trail |
| R9 | Key person dependency (expert biosecurity) | Trung bình | Cao | Lesson Learned library để codify knowledge, cross-training |

---

## 10. DEFINITION OF DONE (DoD)

Mỗi task/story được coi là **Done** khi đáp ứng **tất cả** tiêu chí sau:

### Code

- [ ] Code review passed (≥ 1 reviewer approve)
- [ ] Lint clean (`ruff`, `eslint` — zero error)
- [ ] Unit tests pass, coverage ≥ 80% cho business logic mới
- [ ] Integration tests pass cho API endpoint mới

### Chức năng

- [ ] Acceptance criteria trong task đều satisfied
- [ ] RBAC hoạt động đúng (test với ≥ 2 roles)
- [ ] Optimistic locking hoạt động (nếu entity có version)
- [ ] Audit log ghi đúng (nếu có mutation)
- [ ] Error response đúng format spec

### Triển khai

- [ ] Migration script chạy thành công (`make migrate`)
- [ ] `docker compose up --build` thành công, healthcheck pass tất cả services
- [ ] Deploy staging: `make prod-up` thành công, smoke test pass

---

## 11. CHECKLIST TRƯỚC GO-LIVE

### Hạ tầng

- [ ] Production server provisioned, Docker + Docker Compose installed
- [ ] `.env` file cấu hình đúng cho production (passwords, secrets mạnh)
- [ ] `make prod-up` chạy thành công, tất cả 6 services healthy
- [ ] TLS certificate configured (Let's Encrypt hoặc custom) trong `nginx/certs/`
- [ ] PostgreSQL container healthy, `biosec` schema created
- [ ] Redis container healthy, password đã set
- [ ] MinIO container healthy, bucket `biosec-evidence` tạo sẵn, access policy
- [ ] n8n container healthy, notification workflows imported
- [ ] Frontend Nginx reverse proxy hoạt động: TLS, rate limit, CORS, `/api` → backend
- [ ] Monitoring: Prometheus + Grafana dashboards live
- [ ] Sentry project created, DSN configured
- [ ] Backup: `scripts/backup-db.sh` cron job running, tested `scripts/restore-db.sh` ≥ 1 lần
- [ ] Docker volumes backed up hoặc mounted external storage

### Dữ liệu

- [ ] V001 migration chạy thành công
- [ ] V002 seed data chạy thành công
- [ ] Admin user tạo sẵn (SYSTEM_ADMIN)
- [ ] Region, Farm master data import sẵn (nếu có)
- [ ] Scorecard templates cấu hình sẵn (ít nhất 1 active)
- [ ] Killer metric definitions seed sẵn (4 items)

### Bảo mật

- [ ] JWT secret key generated (≥ 256-bit random)
- [ ] Database password strong, not default
- [ ] MinIO access key/secret rotated
- [ ] CORS whitelist chỉ allowed domains
- [ ] Rate limiting active
- [ ] OWASP Top 10 audit passed
- [ ] Penetration test report — no critical/high issues

### Chức năng

- [ ] UAT passed, sign-off từ stakeholder
- [ ] Tất cả P0/P1 bugs resolved
- [ ] 10 E2E scenarios pass trên staging
- [ ] Dashboard load ≤ 3s (P95)
- [ ] API CRUD ≤ 500ms (P95)

### Vận hành

- [ ] Operation handbook hoàn thành
- [ ] Backup/restore playbook tested
- [ ] Disaster recovery drill ≤ 4h
- [ ] User training sessions completed
- [ ] Support contact & escalation matrix defined

---

## PHỤ LỤC A — MAPPING FR → SPRINT

| FR | Mô tả | Sprint |
|----|-------|--------|
| FR-01 | Farm Inventory | 02 |
| FR-02 | Farm Internal Structure | 02 |
| FR-03 | Floorplan Versioning | 07 |
| FR-04 | Scorecard Configuration | 03 |
| FR-05 | Multiple Scorecard Variants | 03 |
| FR-06 | Assessment Recording | 03 |
| FR-07 | Spider Chart & Dashboard | 03 |
| FR-08 | Killer Metrics | 04 |
| FR-09 | Trust Score Calculation | 04 |
| FR-09a | Trust Score Algorithm | 04 |
| FR-10 | Risk Case Creation | 05 |
| FR-11 | Case Review Queue | 05 |
| FR-12 | Root Cause Analysis | 05 |
| FR-13 | RCA Templates | 05 |
| FR-14 | Manual Task Creation | 06 |
| FR-15 | No Auto-Task Phase 1 | 06 |
| FR-16 | Priority & SLA | 06 |
| FR-17 | Task State Machine | 06 |
| FR-18 | Escalation Rules | 06 |
| FR-19 | Evidence Upload | 06 |
| FR-20 | Watermark & Metadata | 06 |
| FR-21 | Expert Verification | 06 |
| FR-22 | Rework Request | 06 |
| FR-23 | Evidence Integrity | 06 |
| FR-24 | Digital Twin Mapping | 07 |
| FR-25 | Scar Record | 07 |
| FR-26 | Lesson Learned Engine | 08 |
| FR-27 | Similar Case Search | 08 |
| FR-28 | Knowledge Confidence | 07, 08 |
| FR-29 | System Alerts | 10 |
| FR-30 | Multi-Channel Notifications | 10 |
| FR-31 | Executive Dashboard | 09 |
| FR-32 | Reports | 10 |
| FR-33 | Export Formats | 10 |
| FR-34 | Audit Trail | 01 |
| FR-35 | Traceability | 05 |

## PHỤ LỤC B — MAPPING BR → SPRINT

| BR | Mô tả | Sprint kiểm tra |
|----|-------|-----------------|
| BR-01 | Spider Chart = alert tool, not auto-prescriber | 03, 09 |
| BR-02 | Task phải link RCA/expert decision | 06 |
| BR-03 | Killer metric → mandatory case review | 04, 05 |
| BR-04 | Task close = evidence + expert review | 06 |
| BR-05 | Scar = confirmed by authorized person | 07, 08 |
| BR-06 | Low Trust Score → priority inspection | 04, 09 |
| BR-07 | Assessment snapshot template version | 03 |
| BR-08 | Polymorphic FK validate at app layer | 07, 08 |
| BR-09 | Optimistic locking (version column) | 01 (shared), 03-06 |

---

> **Ghi chú:**
> - Kế hoạch này là Phase 1 (MVP). Phase 2 (AI, IoT, PostGIS, TimescaleDB) sẽ lập kế hoạch riêng sau Go-Live.
> - Mỗi sprint 2 tuần. Timeline tổng: ~24 tuần (6 tháng) cho Phase 1.
> - Ưu tiên chất lượng (DoD) hơn tốc độ. Defer feature sang sprint sau nếu chưa đạt DoD.
