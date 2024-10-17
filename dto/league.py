from pydantic import BaseModel


class LeagueBase(BaseModel):
    name: str
    n_groups: int = 4


class LeagueCreate(LeagueBase):
    pass


class League(LeagueBase):
    league_id: int

    class Config:
        from_attributes = True
