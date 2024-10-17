from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey

from models.department import Department


class Player(Base):
    __tablename__ = 'players'

    player_id = Column(Integer, primary_key=True, index=True)
    surname = Column(String(30), nullable=False)
    name = Column(String(30), nullable=False)
    patronymic = Column(String(30))
    sex = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey(Department.id))
    rating = Column(Integer, nullable=False)
