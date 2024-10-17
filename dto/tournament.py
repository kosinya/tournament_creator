from pydantic import BaseModel
from datetime import datetime


class TournamentBase(BaseModel):
    name: str
    date: datetime = datetime.now()
    is_completed: bool = False


class TournamentCreate(TournamentBase):
    pass


class Tournament(TournamentBase):
    tournament_id: int

    class Config:
        from_attributes = True
