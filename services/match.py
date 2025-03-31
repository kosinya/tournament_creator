from fastapi.exceptions import HTTPException
from sqlalchemy import text
from starlette.responses import JSONResponse

from services import group as GroupService
from database import Session
from models.match import Match
from models.group import Group
from models.player import Player
from dto import match


def create_match(db: Session, data: match.MatchCreate):
    new_match = Match(
        player1_id=data.player1_id,
        player2_id=data.player2_id,
        type=data.type,
        score=data.score,
        invoice_by_batch=data.invoice_by_batch,
        group_name=data.group_name,
        playoff_id=data.playoff_id,
        league_id=data.league_id
    )

    try:
        db.add(new_match)
        db.commit()
        db.refresh(new_match)
    except Exception as e:
        print(e)
        db.rollback()

    return new_match


def get_group_matches(db: Session, league_id: int):
    query = text(f"""SELECT m.*, p1.surname AS 'player1_surname', p1.name AS 'player1_name',
                     p2.surname AS 'player2_surname', p2.name AS 'player2_name'
                     FROM matches m
                     JOIN players p1 ON m.player1_id = p1.player_id
                     JOIN players p2 ON m.player2_id = p2.player_id
                     WHERE m.league_id = {league_id};
    """)
    results = db.execute(query).fetchall()
    data = []
    if results:
        for result in results:
            data.append({
                "match_id": result[0],
                "player1_id": result[1],
                "player2_id": result[2],
                "type": result[3],
                "score": result[4],
                "invoice_by_batch": result[5],
                "group_name": result[6],
                "playoff_id": result[7],
                "league_id": result[8],
                "winner_id": result[9],
                "player1_surname": result[10],
                "player1_name": result[11],
                "player2_surname": result[12],
                "player2_name": result[13]
            })
    return JSONResponse(content=data, status_code=200)


def get_matches_by_playoff(db: Session, playoff_id: int):
    query = text(f"""SELECT m.*, p1.surname AS 'player1_surname', p1.name AS 'player1_name',
                         p2.surname AS 'player2_surname', p2.name AS 'player2_name'
                         FROM matches m
                         LEFT JOIN players p1 ON m.player1_id = p1.player_id
                         LEFT JOIN players p2 ON m.player2_id = p2.player_id
                         WHERE m.playoff_id = {playoff_id};
        """)
    results = db.execute(query).fetchall()
    data = []
    if results:
        for result in results:
            if result[3] == '3 место':
                break
            data.append({
                "match_id": result[0],
                "player1_id": result[1],
                "player2_id": result[2],
                "type": result[3],
                "score": result[4],
                "invoice_by_batch": result[5],
                "playoff_id": result[7],
                "league_id": result[8],
                "winner_id": result[9],
                "player1_surname": result[10],
                "player1_name": result[11],
                "player2_surname": result[12],
                "player2_name": result[13]
            })
    return data


def get_count_unplayed_group_matches(db: Session, league_id: int):
    return db.query(Match).filter_by(league_id=league_id, winner_id=None).count()


def update_match_result(db: Session, match_id: int, winner_id: int, score: str, by_batch: str):
    m = db.query(Match).filter_by(match_id=match_id).first()
    old_winner = m.winner_id
    m.winner_id = winner_id
    m.score = score
    m.invoice_by_batch = by_batch
    try:
        db.add(m)
        db.commit()
        db.refresh(m)
    except Exception as e:
        print(e)
        db.rollback()

    if m.type == "Групповой":
        p2 = None
        p = db.query(Group).filter_by(league_id=m.league_id, player_id=winner_id).first()
        if old_winner != winner_id:
            p.score += 2
            if old_winner is not None:
                p2 = db.query(Group).filter_by(league_id=m.league_id, player_id=old_winner).first()
                p2.score -= 2
        try:
            db.add(p)
            if p2 is not None:
                db.add(p2)
            db.commit()
            if p2 is not None:
                db.refresh(p2)
            db.refresh(p)
        except Exception as e:
            print(e)
            db.rollback()

        GroupService.updating_the_results(db, m.league_id, m.group_name)

    return m
