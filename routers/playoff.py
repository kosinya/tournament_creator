from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from database import get_connection
from services import playoff

router = APIRouter()


@router.get("/get_grid", tags=["playoff"])
async def get_grid(db: Session = Depends(get_connection), playoff_id: str = None):
    return playoff.get_the_grid(db, int(playoff_id))


@router.get("/get_playoffs", tags=["playoff"])
async def get_playoffs(db: Session = Depends(get_connection), l_id: str = None):
    return playoff.get_all_playoffs(db, int(l_id))


@router.post("/next_stage", tags=["playoff"])
async def next_stage(db: Session = Depends(get_connection), p_id: str = None):
    return playoff.next_stage(db, int(p_id))
