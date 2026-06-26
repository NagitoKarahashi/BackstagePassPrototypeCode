from fastapi import APIRouter, HTTPException
from app.services.events_service import get_events_df, reload_events_df
from app.services.retrieval_service import retriever

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "events_rows": int(len(get_events_df())), "rag_enabled": bool(retriever.enabled)}

@router.post("/admin/reload_events")
def reload_events():
    try:
        df = reload_events_df()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload events: {e}")
    return {"status": "ok", "rows": int(len(df))}
