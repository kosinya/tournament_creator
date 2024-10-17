from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database import Base
from models.player import Player
from models.group import Group
from models.league import League
from models.playoff import Playoff


class Match(Base):
    __tablename__ = 'matches'

    match_id = Column(Integer, primary_key=True)
    player1_id = Column(Integer, ForeignKey(Player.player_id))
    player2_id = Column(Integer, ForeignKey(Player.player_id))
    type = Column(String, nullable=False)
    score = Column(String())
    invoice_by_batch = Column(String())
    group_name = Column(String)
    playoff_id = Column(Integer, ForeignKey(Playoff.playoff_id))
    league_id = Column(Integer, ForeignKey(League.league_id, ondelete='CASCADE'))
    winner_id = Column(Integer, ForeignKey(Player.player_id))
