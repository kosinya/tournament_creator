from pydantic import BaseModel


class GroupBase(BaseModel):
    player_id: int
    score: int
    group_name: str


class GroupCreate(GroupBase):
    pass


class Group(GroupBase):

    class Config:
        from_attributes = True
    