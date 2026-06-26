# Backstage Pass backend restructure pack

## What this zip is
This package is designed to fit your current `ai-service/` backend.
Do **not** create another `backend/` folder above it.

Use it like this:

```
ai-service/
├── app/
├── data/
├── vectordb/
├── tests/
└── requirements.txt
```

## Safe migration plan
1. Back up your current `app/main.py` as `app/main_old.py`.
2. Copy the new subfolders from this zip into your existing `ai-service/app/`.
3. Keep your current `data/` and `vectordb/` where they are.
4. Keep `ingest.py` and `rag_core.py` for now.
5. Start the app with:

```use powershell not bash
uvicorn app.main:app --reload
```

## Old-to-new mapping
- old `main.py` intent + language utils -> `app/services/intent_service.py`
- old `main.py` event recommendation -> `app/services/recommendation_service.py`
- old `main.py` hybrid search -> `app/services/retrieval_service.py`
- old `main.py` /ask orchestration -> `app/services/ask_service.py`
- old `main.py` /wallet -> `app/api/wallet.py`
- old `main.py` /health + reload -> `app/api/health.py`
- old `main.py` fraud rules -> `app/services/fraud_service.py` + `app/api/fraud.py`

## Important
This pack intentionally avoids moving your `data/` and `vectordb/` folders, so your current paths remain valid.

