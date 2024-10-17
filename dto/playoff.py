from pydantic import BaseModel
from typing import Literal


class PlayoffBase(BaseModel):
    name: Literal['Золотой', 'Серебрянный', 'Бронзовый'] = 'Золотой'
    start_stage: Literal['1/4', '1/2', 'Финал'] = '1/4'
    current_stage: Literal['1/4', '1/2', 'Финал'] = '1/4'
    league_id: int


class PlayoffCreate(PlayoffBase):
    ...


class PlayoffUpdate(PlayoffBase):
    id: int

    class Config:
        from_attributes = True
