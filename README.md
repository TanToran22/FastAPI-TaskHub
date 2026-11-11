# TaskHub API - Day 1 Core Setup

Du an Backend FastAPI theo kien truc phan tang Layered Architecture.

## 1. Huong dan Clone va Thiet lap Import

Vi cac import trong ma nguon su dung package `app`, khi clone repo ve ban co 2 cach chay:

### Cach 1 (Khuyen nghi): Clone truc tiep vao thu muc ten la `app`
```bash
git clone <URL_REPO> app
cd app
```

### Cach 2: Thiet lap PYTHONPATH neu clone voi ten thu muc khac
- **Linux / macOS**: `export PYTHONPATH=.`
- **Windows (CMD)**: `set PYTHONPATH=.`
- **Windows (PowerShell)**: `$env:PYTHONPATH="."`

## 2. Cai dat moi truong

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx
```

## 3. Khoi chay Server

```bash
uvicorn main:app --reload
```

## 4. Chay kiem thu (Test)

```bash
pytest -v
```
