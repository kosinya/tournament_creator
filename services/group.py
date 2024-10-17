import itertools

from fastapi import HTTPException
from sqlalchemy import text
from starlette.responses import JSONResponse

from models.group import Group
from models.match import Match
from services import match
from dto import group
from database import Session


def add_player_to_group(db: Session, data: group.GroupCreate, league_id: int):
    new = Group(
        player_id=data.player_id,
        score=data.score,
        group_name=data.group_name,
        league_id=league_id
    )

    try:
        db.add(new)
        db.commit()
        db.refresh(new)
    except Exception as e:
        print(e)
        db.rollback()

    return new


def get_all_groups(db: Session, l_id: int):
    query = text(f"""SELECT g.*, p.surname, p.name, p.patronymic
                     FROM groups g
                     JOIN players p ON g.player_id = p.player_id
                     WHERE g.league_id = {l_id}
                     ORDER BY g.group_name ASC;""")
    results = db.execute(query).fetchall()

    data = []
    if results:
        for r in results:
            data.append({
                "id": r[0],
                "player_id": r[1],
                "score": r[2],
                "place": r[3],
                "group_name": r[4],
                "league_id": r[5],
                "surname": r[6],
                "name": r[7],
                "patronymic": r[8]
            })
    return data


def updating_the_results(db: Session, league_id: int, group_name: str):
    g = db.query(Group).filter_by(league_id=league_id, group_name=group_name).all()
    ranked = rank_players(g, 1)

    db.add_all(ranked)
    db.commit()
    return ranked


def rank_players(players, r):
    players.sort(key=lambda x: x.score, reverse=True)

    current_rank = r
    previous_score = players[0].score

    for i, player in enumerate(players):
        if player.score != previous_score:
            current_rank = current_rank + 1
        previous_score = player.score
        player.place = current_rank

    return players


def conflict_search(groups):
    ranked_players = {}
    for player in groups:
        if player['place'] not in ranked_players:
            ranked_players[player['place']] = []
        ranked_players[player['place']].append(player)

    for key, value in ranked_players.items():
        coincidences = {}
        for player in value:
            if player['group_name'] not in coincidences:
                coincidences[player['group_name']] = []
            coincidences[player['group_name']].append(player)

        for v in coincidences.values():
            if len(v) > 1:
                return True

    return False


def conflicts_resolution(db: Session, group_id, place, l_id):
    n = match.get_count_unplayed_group_matches(db, l_id)
    if n != 0:
        raise HTTPException(status_code=400, detail=f"{n} матча/матчей в групповом этапе еще не сыграно")

    gr = db.query(Group).filter_by(id=group_id).first()
    gr.place = place
    db.add(gr)
    db.commit()
    return JSONResponse(status_code=200, content="Успех!")

