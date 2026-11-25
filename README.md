# TaskHub API (Day 5: Task Lifecycle, Labels & Comments)

Backend FastAPI theo kiến trúc phân tầng Layered Architecture (`endpoints` -> `services` -> `repositories` -> `schemas` / `models`).

## Tiến độ

- [x] **Day 1:** Core Setup & Layered Architecture
- [x] **Day 2:** Database (SQLAlchemy 2.x Async & Alembic Migrations)
- [x] **Day 3:** Authentication (JWT), User Profile & RBAC Core
- [x] **Day 4:** Workspace & Project Management (Workspace RBAC: `OWNER`, `EDITOR`, `VIEWER`)
- [x] **Day 5:** Task Management (Project Tasks, Filtering, Labels, Task-Label Association, Comments & Archive/Unarchive Guard)

## Hướng dẫn khởi chạy & Kiểm thử

1. Tạo file `.env` từ `.env.example` và sinh `SECRET_KEY`:
   ```bash
   cp .env.example .env
   openssl rand -hex 32
   ```

2. Cài đặt thư viện:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Chạy kiểm thử tự động & Linter:
   ```bash
   ruff check .
   ruff format --check .
   pytest -v
   ```

4. Khởi động server:
   ```bash
   uvicorn app.main:app --reload
   ```
