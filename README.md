# TechGear - Hybrid Catalog and Order System

Workshop 2 (Python). Hybrid system made of a REST API and a web interface.

## Structure

- `techgear_api/` - FastAPI backend (MongoDB Atlas + Pydantic models)
- `techgear_web/` - Django frontend (consumes the API over HTTP)

## Requirements

- Python 3.12+
- A MongoDB Atlas cluster

## API setup

```bash
cd techgear_api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your MongoDB Atlas URI
fastapi dev app/main.py
```

Health check: http://127.0.0.1:8000/health
Docs: http://127.0.0.1:8000/docs

## Web setup

```bash
cd techgear_web
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 8001
```

## Environment variables

| File | Variable | Description |
|---|---|---|
| `techgear_api/.env` | `MONGODB_URI` | MongoDB Atlas connection string |
| `techgear_api/.env` | `MONGODB_DB_NAME` | Database name |
| `techgear_web/.env` | `TECHGEAR_API_URL` | Base URL of the API |
