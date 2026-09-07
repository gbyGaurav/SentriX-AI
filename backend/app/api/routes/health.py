from fastapi import APIRouter, Depends
from app.schemas.analysis import HealthResponse
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time

router = APIRouter()
startup_time = time.time()

@router.get('/api/health', response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        pass
        
    return HealthResponse(
        status="ok",
        version="1.0.0",
        uptime_seconds=time.time() - startup_time,
        models_loaded={"url-heuristic": True, "text-pattern": True},
        database_connected=db_connected
    )
