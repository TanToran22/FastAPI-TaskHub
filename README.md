# TaskHub API (Day 3: Authentication, User Profile & RBAC Core)

Backend FastAPI theo kiến trúc phân tầng Layered Architecture.

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
   pytest -v
   ```

4. Khởi động server:
   ```bash
   uvicorn app.main:app --reload
   ```
