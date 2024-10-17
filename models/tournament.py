from sqlalchemy.orm import relationship

from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Date


class Tournament(Base):
    __tablename__ = 'tournaments'

    tournament_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    date = Column(Date, nullable=False)
    is_completed = Column(Boolean, default=False)

    leagues = relationship("League", cascade="all,delete")
