# EIC backend service

This service provides an API endpoint for mzML upload and EIC extraction using MassCube.

## Start service

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## API

- `GET /api/health`
- `POST /api/eic` (multipart form)

Frontend default backend URL:

- `http://127.0.0.1:8000`
