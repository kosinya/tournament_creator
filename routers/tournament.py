from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_connection
from services import tournament as service
from dto import tournament as dto


router = APIRouter()


@router.get("/all", tags=['tournament'])
async def get_tournaments(db: Session = Depends(get_connection)):
    return service.get_tournaments(db)


@router.delete('/{t_id}', tags=['tournament'])
async def delete_tournament(db: Session = Depends(get_connection), t_id: str = None, ):
    return service.delete_tournament(db, int(t_id))


@router.put('/{t_id}', tags=['tournament'])
async def update_tournament(db: Session = Depends(get_connection), t_id: str = None, data: dto.Tournament = None):
    return service.update_tournament(db, int(t_id), data)


@router.post('/', tags=['tournament'])
async def create_tournament(db: Session = Depends(get_connection), data: dto.TournamentCreate = None):
    return service.create_tournament(db, data)
