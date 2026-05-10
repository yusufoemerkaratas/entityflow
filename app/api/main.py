from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api.routes.documents import router as documents_router
from app.api.routes.entities import router as entities_router
from app.api.routes.extractions import router as extractions_router
from app.api.vision import router as vision_router

from app.db.database import get_db

app = FastAPI(title="EntityFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(entities_router)
app.include_router(extractions_router)
app.include_router(vision_router)


@app.get("/")
def read_root():
    return {"message": "EntityFlow API is running"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    
