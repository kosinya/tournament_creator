from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_connection
from dto import player as dto
from services import player


router = APIRouter()


# Получить список всех игроков
@router.get('/all', tags=['player'])
async def get_players(db: Session = Depends(get_connection)):
    return player.get_players(db)


# Получить игрока по id
@router.get('/{p_id}', tags=['player'])
async def get_player(p_id: str = None, db: Session = Depends(get_connection)):
    return player.get_player(db, int(p_id))


# Удалить игрока по id
@router.delete('/{p_id}', tags=['player'])
async def delete_player(p_id: str = None, db: Session = Depends(get_connection)):
    return player.delete_player(db, int(p_id))


# Обновить игрока по id
@router.put('/{id}', tags=['player'])
async def update_player(p_id: str = None, db: Session = Depends(get_connection), data: dto.Player = None):
    return player.update_player(db, int(p_id), data)


# Добавить игрока
@router.post('/', tags=['player'])
async def create_player(db: Session = Depends(get_connection), data: dto.PlayerCreate = None):
    return player.create_new_player(db, data)
