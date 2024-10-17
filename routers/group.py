from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from database import get_connection
from services import group

router = APIRouter()


@router.get('', tags=['group'])
async def get_groups(db: Session = Depends(get_connection), l_id: str = None):
    data = group.get_all_groups(db, int(l_id))
    return JSONResponse(content=data, status_code=200)


@router.post('', tags=['group'])
async def conflict_resolution(db: Session = Depends(get_connection), group_id: str = None,
                              place: int = None, l_id: str = None):
    return group.conflicts_resolution(db, group_id, place, l_id)
