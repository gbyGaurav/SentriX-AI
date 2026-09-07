from fastapi import APIRouter, Depends, Query
from app.schemas.analysis import HistoryResponse, HistoryItem, InputType
from app.db.database import get_db
from app.db.models import Analysis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

router = APIRouter()

@router.get('/api/history', response_model=HistoryResponse)
async def get_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * page_size
    stmt = select(Analysis).order_by(Analysis.created_at.desc()).offset(offset).limit(page_size)
    count_stmt = select(func.count()).select_from(Analysis)
    
    total = await db.scalar(count_stmt)
    result = await db.execute(stmt)
    analyses = result.scalars().all()
    
    items = [
        HistoryItem(
            analysis_id=a.id,
            input_type=InputType(a.input_type),
            risk_score=a.risk_score,
            risk_level=a.risk_level,
            fraud_types=a.fraud_types,
            processing_time_ms=a.processing_time_ms,
            created_at=a.created_at.isoformat() + 'Z',
            ai_media=(a.extracted_content or {}).get("ai_media")
        ) for a in analyses
    ]
    
    return HistoryResponse(items=items, total=total or 0, page=page, page_size=page_size)
