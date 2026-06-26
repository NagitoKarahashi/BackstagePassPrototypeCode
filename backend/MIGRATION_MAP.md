# Migration map

## Keep as-is for now
- `data/`
- `vectordb/`
- `app/ingest.py`
- `app/rag_core.py`

## Move logic from current main.py
- `AskRequest` -> `app/schemas/ask.py`
- `OrderInfo` -> `app/schemas/fraud.py`
- fraud rules -> `app/services/fraud_service.py`
- language + intent -> `app/services/intent_service.py`
- event recommendation -> `app/services/recommendation_service.py`
- hybrid search -> `app/services/retrieval_service.py`
- /ask main flow -> `app/services/ask_service.py`
- /health -> `app/api/health.py`
- /wallet -> `app/api/wallet.py`
- /fraud/check_order -> `app/api/fraud.py`

## Start command
```bash
uvicorn app.main:app --reload
```
