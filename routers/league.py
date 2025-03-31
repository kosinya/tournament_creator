from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from services import league
from dto import league as dto
from database import get_connection


router = APIRouter()


@router.get("/all", tags=['league'])
async def get_all_leagues(db: Session = Depends(get_connection), t_id: str = None):
    return league.get_all_leagues(db, int(t_id))


@router.post("/", tags=['league'])
async def create_league(db: Session = Depends(get_connection), t_id: str = None, data: dto.LeagueCreate = None):
    return league.create_league(db, int(t_id), data)


@router.delete("/{l_id}", tags=['league'])
async def delete_league(db: Session = Depends(get_connection), l_id: str = None):
    return league.delete_league(db, int(l_id))


@router.put("/{l_id}/players", tags=['league'])
async def add_players(db: Session = Depends(get_connection), l_id: str = None, player_ids: str = None):
    return league.add_players(db, int(l_id), player_ids)


@router.put('/{l_id}/', tags=['league'])
async def delete_player(db: Session = Depends(get_connection), l_id: str = None, player_id: str = None):
    return league.delete_player(db, int(l_id), int(player_id))


@router.post('/{l_id}/draw', tags=['league'])
async def draw(db: Session = Depends(get_connection), l_id: str = None):
    return league.draw(db, int(l_id))


@router.post('/{l_id}/create_playoff', tags=['league'])
async def create_playoff(db: Session = Depends(get_connection), l_id: str = None):
    return league.complete_the_group_stage(db, int(l_id))


@router.get('/get_results', tags=['league'])
async def get_results(db: Session = Depends(get_connection), l_id: str = None):
    return league.get_pdf_result(db, int(l_id))
