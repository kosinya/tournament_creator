from sqlalchemy.orm import Session

from dto import tournament
from models.tournament import Tournament


# Получить список всех турниров
def get_tournaments(db: Session):
    return db.query(Tournament).all()


# Создать турнир
def create_tournament(db: Session, data: tournament.TournamentCreate):
    new_tournament = Tournament(
        name=data.name,
        date=data.date,
        is_completed=data.is_completed)

    try:
        db.add(new_tournament)
        db.commit()
        db.refresh(new_tournament)
    except Exception as e:
        print(e)
        db.rollback()

    return new_tournament


# Удалить турнир
def delete_tournament(db: Session, tournament_id: int):
    tm = db.query(Tournament).filter_by(tournament_id=tournament_id).first()
    db.delete(tm)
    db.commit()
    return tm


# Обновление турнира
def update_tournament(db: Session, tournament_id: int, data: tournament.Tournament):
    tm = db.query(Tournament).filter_by(tournament_id=tournament_id).first()
    tm.name = data.name
    tm.date = data.date
    tm.is_completed = data.is_completed

    try:
        db.add(tm)
        db.commit()
        db.refresh(tm)
    except Exception as e:
        print(e)

    return tm
