from http.client import HTTPResponse

from starlette.responses import JSONResponse
from sqlalchemy import text

from database import Session
from models.playoff import Playoff
from models.match import Match
from services import match as match_service
from dto import playoff

from fastapi import HTTPException


def create_playoff(db: Session, data: playoff.PlayoffCreate):
    new_playoff = Playoff(
        name=data.name,
        start_stage=data.start_stage,
        current_stage=data.current_stage,
        league_id=data.league_id
    )

    try:
        db.add(new_playoff)
        db.commit()
        db.refresh(new_playoff)
    except Exception as e:
        print(e)
        db.rollback()

    return new_playoff


def get_all_playoffs(db: Session, league_id: int):
    return db.query(Playoff).filter_by(league_id=league_id).all()


def get_the_grid(db, playoff_id: int):
    matches = match_service.get_matches_by_playoff(db, playoff_id)
    return build_tree(matches)


def build_tree(matches):
    tree = {}

    final_match = max(matches, key=lambda x: x["type"])
    if final_match:
        tree = build_match_tree(final_match, matches, set(), "0")
    return tree


def build_match_tree(match, matches, processed_matches, key):
    match_dict = match
    match_dict["key"] = key
    match_dict["children"] = []

    types = ['Финал', '1/2', '1/4', '1/8']
    current_stage_index = types.index(match_dict["type"])
    dependent_matches = []

    if current_stage_index < len(types):
        processed_matches.add(match["match_id"])
        if match_dict["player1_id"] != -1:
            dependent_matches = [m for m in matches
                                 if types.index(m["type"]) == current_stage_index+1
                                 and m["match_id"] not in processed_matches
                                 and (m["winner_id"] == match_dict["player1_id"] or
                                      m["winner_id"] == match_dict["player2_id"])]
        else:
            dependent_matches = [m for m in matches
                                 if types.index(m["type"]) == current_stage_index + 1
                                 and m["match_id"] not in processed_matches]
    for i, dependent_match in enumerate(dependent_matches[:2]):
        match_dict["children"].append(build_match_tree(dependent_match, matches, processed_matches, key+"_"+str(i)))

    return match_dict


def next_stage(db:Session, playoff_id: int):
    plf = db.query(Playoff).filter_by(playoff_id=playoff_id).first()

    if plf.current_stage == 'Финал':
        raise HTTPException(status_code=400, detail="Финальная стадия уже завершена")
    matches = db.query(Match).filter_by(playoff_id=plf.playoff_id).all()

    match_by_current_stage = [m for m in matches if m.type == plf.current_stage]

    for match in match_by_current_stage:
        if match.winner_id is None:
            raise HTTPException(status_code=400, detail='Еще не все матчи текущей стадии сыграны!')

    next_stages = {'1/8': '1/4', '1/4': '1/2', '1/2': 'Финал'}

    match_by_next_stage = [m for m in matches if m.type == next_stages[plf.current_stage]]

    # Матч за 3 место
    if plf.current_stage == "1/2":
        third_place_match = matches[0]
        for match in matches:
            if match.type == "3 место":
                third_place_match = match
                break
        if match_by_current_stage[0].winner_id != match_by_current_stage[0].player1_id:
            third_place_match.player1_id = match_by_current_stage[0].player1_id
        else:
            third_place_match.player1_id = match_by_current_stage[0].player2_id

        if match_by_current_stage[1].winner_id != match_by_current_stage[1].player1_id:
            third_place_match.player2_id = match_by_current_stage[1].player1_id
        else:
            third_place_match.player2_id = match_by_current_stage[1].player2_id

        db.add(third_place_match)

    it = 0
    for i in range(0, len(match_by_current_stage), 2):
        match_by_next_stage[it].player1_id = match_by_current_stage[i].winner_id
        match_by_next_stage[it].player2_id = match_by_current_stage[i+1].winner_id
        it += 1

    for match in match_by_next_stage:
        db.add(match)

    plf.current_stage = next_stages[plf.current_stage]
    db.commit()

    return JSONResponse(status_code=200, content="Успех!")


def get_third_match(db:Session, playoff_id: int):
    query = text(f"""SELECT m.*, p1.surname AS 'player1_surname', p1.name AS 'player1_name',
                             p2.surname AS 'player2_surname', p2.name AS 'player2_name'
                             FROM matches m
                             LEFT JOIN players p1 ON m.player1_id = p1.player_id
                             LEFT JOIN players p2 ON m.player2_id = p2.player_id
                             WHERE m.playoff_id = {playoff_id} AND m.type = '3 место';
            """)
    results = db.execute(query).fetchall()
    if not results:
        return HTTPException(status_code=404, detail="Match not found!")
    result = results[0]
    match = {
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
    }
    return match
