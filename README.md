# TaskHub API - Multi-User Task Management System

TaskHub là dự án Backend RESTful API Quản lý công việc đa người dùng xây dựng bằng **FastAPI**, **Pydantic v2**, **SQLAlchemy 2.x async**, **PostgreSQL** và **Redis**, tuân thủ kiến trúc phân tầng chuẩn (**Layered Architecture**).

---

## 📅 Lộ trình phát triển (Development Roadmap)

| Ngày | Trọng tâm công việc | Trạng thái |
| :--- | :--- | :---: |
| **Day 1** | Core Setup & Kiến trúc phân tầng (In-memory CRUD Task) | ✅ Hoàn thành |
| **Day 2** | **Database, Async SQLAlchemy 2.x & Alembic Migrations** | ✅ Hoàn thành |
| **Day 3** | Authentication (JWT), User Management & RBAC Core | ⏳ Sắp tới |
| **Day 4** | Workspace & Project Management (Resource Ownership) | ⏳ Sắp tới |
| **Day 5** | Task Lifecycle, Labels Assignment & Comments | ⏳ Sắp tới |
| **Day 6** | Advanced Filtering, Redis Caching & Background Tasks | ⏳ Sắp tới |
| **Day 7** | Structured Logging, Multi-stage Docker & OpenAPI Docs | ⏳ Sắp tới |
| **Day 8** | Code Review, Refactor, Linting & Production Hardening | ⏳ Sắp tới |

---

## 🌟 Chi tiết thực hiện Day 2: Database & Migrations

- **Async Database Connection:**
  - Cấu hình SQLAlchemy 2.0 Async engine với `postgresql+asyncpg`.
  - Quản lý phiên làm việc qua `async_sessionmaker` và dependency `get_db`.
- **8 ORM Models & Enums:**
  - `User`, `Workspace`, `WorkspaceMember`, `Project`, `Task`, `Label`, `Comment`, `task_labels`.
  - Đánh index cho toàn bộ các cột Foreign Key và `label_id` trong bảng trung gian.
  - Sử dụng `server_default` cho timestamps và các trường enum mặc định.
- **Generic Base Repository:**
  - `BaseRepository[T]` async CRUD: `get_by_id`, `get_multi`, `count`, `create`, `update`, `delete`.
  - `TaskRepository` kế thừa BaseRepository với phân trang và sắp xếp tie-breaker `id desc`.
- **Alembic Migrations:**
  - File cấu hình `env.py` async sạch, không dùng `# noqa: F401`.
  - Migration script đầu tiên tạo toàn bộ 8 bảng và xử lý DROP ENUM an toàn khi downgrade.

---

## ⚙️ Hướng dẫn cài đặt và thiết lập môi trường

```bash
# 1. Kích hoạt môi trường ảo
python -m venv .venv
.venv\Scripts\activate  # Trên Windows

# 2. Cài đặt thư viện phụ thuộc
pip install -r requirements.txt

# 3. Chạy migration tạo bảng
alembic upgrade head

# 4. Khởi chạy Development Server
uvicorn app.main:app --reload

# 5. Chạy kiểm thử tự động
pytest -v

# 6. Kiểm tra Linting với Ruff
ruff check .
ruff format .
```
