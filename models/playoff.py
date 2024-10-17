from sqlalchemy import Column, Integer, String, ForeignKey

from database import Base
from models.league import League


class Playoff(Base):
    __tablename__ = 'playoffs'

    playoff_id = Column(Integer, primary_key=True)
    name = Column(String)
    start_stage = Column(String)
    current_stage = Column(String)
    league_id = Column(Integer, ForeignKey(League.league_id, ondelete='CASCADE'))
