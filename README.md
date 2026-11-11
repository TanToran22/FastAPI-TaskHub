# TaskHub API - Task Management System

TaskHub là dự án Backend xây dựng theo kiến trúc phân tầng (**Layered Architecture**) sử dụng **FastAPI**, **Pydantic v2**, **SQLAlchemy 2.x async**, và kiểm soát chất lượng code nghiêm ngặt bằng **Ruff** và **pytest**.

---

## 📅 Lộ trình phát triển (Development Roadmap)

| Ngày | Trọng tâm công việc | Trạng thái |
| :--- | :--- | :---: |
| **Day 1** | **Core Setup & Kiến trúc phân tầng (In-memory CRUD Task)** | ✅ Hoàn thành |
| **Day 2** | Database, Async SQLAlchemy 2.x & Alembic Migrations | ⏳ Sắp tới |
| **Day 3** | Authentication (JWT), User Management & RBAC Core | ⏳ Sắp tới |
| **Day 4** | Workspace & Project Management (Resource Ownership) | ⏳ Sắp tới |
| **Day 5** | Task Lifecycle, Labels Assignment & Comments | ⏳ Sắp tới |
| **Day 6** | Advanced Filtering, Redis Caching & Background Tasks | ⏳ Sắp tới |
| **Day 7** | Structured Logging, Multi-stage Docker & OpenAPI Docs | ⏳ Sắp tới |
| **Day 8** | Code Review, Refactor, Linting & Production Hardening | ⏳ Sắp tới |

---

## 🌟 Chi tiết thực hiện theo từng ngày

### Day 1: Core Setup & Layered Architecture
- **Kiến trúc phân tầng (Layered Architecture):**
  - Tách bạch rõ ràng 4 tầng: `endpoints` → `services` → `repositories` → `schemas` & `models`.
  - Tách biệt Domain Model nội bộ (`InternalTask`) khỏi Schema API (`TaskResponse`).
- **Cấu hình & Vòng đời ứng dụng:**
  - Khởi tạo FastAPI instance kèm `lifespan` context manager quản lý startup/shutdown.
  - Quản lý biến môi trường fail-fast qua `pydantic-settings` (`BaseSettings`).
  - Định tuyến phiên bản hóa tập trung qua APIRouter prefix `/api/v1` và endpoint `GET /api/v1/health`.
- **Resource Task CRUD & Pydantic v2 Validation:**
  - Triển khai đầy đủ CRUD Task: `POST`, `GET` list, `GET` by id, `PATCH`, `DELETE`.
  - Endpoint `GET /api/v1/tasks` sử dụng `Annotated` với `ge`/`le` validation, trả về cấu trúc chuẩn `{items, total}`.
  - Kế thừa `CoreBaseSchema` bật `str_strip_whitespace=True` để tự động làm sạch khoảng trắng.
  - Chặn truyền `null` tường minh ở method PATCH (`{"title": null}`) bằng `@field_validator`, trả về mã lỗi HTTP `422 Unprocessable Entity`.
- **Dependency Injection & Xử lý ngoại lệ:**
  - Áp dụng Dependency Injection qua FastAPI `Depends` để inject repository và service.
  - Gom toàn bộ ngoại lệ kế thừa `AppException` về 1 exception handler duy nhất trong `main.py`, phản hồi mã lỗi linh hoạt dựa trên `status_code` của exception.
- **Code Quality & Testing:**
  - Viết bộ kiểm thử tự động với `pytest`, `pytest-asyncio` và `httpx`.
  - Vượt qua kiểm tra linter và định dạng mã nguồn chuẩn PEP 8 bằng `ruff`.

### Day 2: Database, ORM & Migrations
*(Chưa cập nhật - Sẽ triển khai kết nối Async PostgreSQL qua SQLAlchemy 2.x, định nghĩa 8 models, thiết lập Alembic migrations và BaseRepository)*

### Day 3: Authentication & RBAC Core
*(Chưa cập nhật - Sẽ triển khai Password hashing passlib/bcrypt, cấp/thu hồi JWT Access/Refresh tokens, API Auth & User profile)*

### Day 4: Workspace & Project Management
*(Chưa cập nhật - Sẽ triển khai nghiệp vụ phân quyền sở hữu tài nguyên, Workspace roles: OWNER, EDITOR, VIEWER)*

### Day 5: Task Lifecycle, Labels & Comments
*(Chưa cập nhật - Sẽ triển khai gán nhãn, bình luận công việc và quan hệ liên kết dữ liệu)*

### Day 6: Filtering, Redis Caching & Background Tasks
*(Chưa cập nhật - Sẽ triển khai lọc nâng cao, phân trang động, Redis cache invalidation và background task gửi email)*

### Day 7: DevOps, Structured Logging & Docker
*(Chưa cập nhật - Sẽ triển khai Middleware request logging, tối ưu Dockerfile multi-stage và docker-compose full stack)*

### Day 8: Final Review & Polish
*(Chưa cập nhật - Sẽ tổng duyệt toàn bộ dự án, type-check mypy strict và tối ưu hiệu năng)*

---

## 🏗️ Cấu trúc thư mục hiện tại

```text
FastAPI-TaskHub/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app instance, lifespan & central error handler
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api_router.py       # API v1 Router aggregate
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py       # GET /health
│   │           └── tasks.py        # CRUD /tasks (Annotated ge/le, responses, {items, total})
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic BaseSettings
│   │   ├── constants.py            # Pagination bounds & validation limits
│   │   ├── dependencies.py        # Dependency Injection providers
│   │   ├── exceptions.py          # AppException, NotFoundException có status_code
│   │   └── messages.py            # Error & warning messages
│   ├── models/
│   │   ├── __init__.py
│   │   └── internal_task.py       # Domain Model (InternalTask)
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── task_repository.py     # In-memory Task Repository (hỗ trợ count, CRUD)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py                # CoreBaseSchema (strip_whitespace)
│   │   └── task.py                # TaskCreate, TaskUpdate (null check 422), TaskListResponse
│   └── services/
│       ├── __init__.py
│       └── task_service.py        # Task Business Logic Service
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest async fixture setup
│   ├── test_health.py             # Unit test health check
│   └── test_tasks.py              # CRUD & validation test cases
├── .env.example
├── .gitignore
├── pyproject.toml                 # Ruff lint & pytest-asyncio settings
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development & testing tools (ruff, pytest, httpx)
└── README.md