from pydantic import BaseModel
from typing import Literal


class PlayerBase(BaseModel):
    surname: str
    name: str
    patronymic: str = ""
    sex: Literal['Муж.', 'Жен.'] = 'Муж.'
    department_id: int
    rating: int = 0


class PlayerCreate(PlayerBase):
    pass


class Player(PlayerBase):
    player_id: int

    class Config:
        from_attributes = True
