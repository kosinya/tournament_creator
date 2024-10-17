from sqlalchemy.orm import Session
from sqlalchemy import text
from starlette.responses import JSONResponse

from models.player import Player
from dto import player


# Получить список всех игроков
def get_players(db: Session):
    query = text("""SELECT p.*, d.name
                    FROM players p
                    LEFT JOIN departments d ON p.department_id = d.id;""")
    results = db.execute(query).fetchall()
    data = []
    if results:
        for r in results:
            data.append({
                "player_id": r[0],
                "surname": r[1],
                "name": r[2],
                "patronymic": r[3],
                "sex": r[4],
                "department_id": r[5],
                "rating": r[6],
                "department_name": r[7],
            })
    return JSONResponse(content=data, status_code=200)


# Получить игрока по id
def get_player(db: Session, player_id: int):
    return db.query(Player).filter_by(player_id=player_id).first()


# Обновить игрока по id
def update_player(db: Session, player_id: int, data: player.Player):
    p = db.query(Player).filter_by(id=player_id).first()
    p.name = data.name
    p.surname = data.surname
    p.patronymic = data.patronymic
    p.sex = data.sex
    p.department_id = data.department_id
    p.rating = data.rating

    try:
        db.add(p)
        db.commit()
        db.refresh(p)
    except Exception as e:
        db.rollback()
        print(e)

    return p


# Удалить игрока по id
def delete_player(db: Session, player_id: int):
    p = db.query(Player).filter_by(player_id=player_id).delete()
    db.commit()
    return p


# Добавить игрока
def create_new_player(db: Session, data: player.PlayerCreate):
    new_p = Player(
        surname=data.surname,
        name=data.name,
        patronymic=data.patronymic,
        sex=data.sex,
        department_id=data.department_id,
        rating=data.rating)

    try:
        db.add(new_p)
        db.commit()
        db.refresh(new_p)
    except Exception as e:
        db.rollback()
        print(e)

    return new_p
