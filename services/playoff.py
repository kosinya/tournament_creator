from http.client import HTTPResponse

from starlette.responses import JSONResponse

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
    n = 0
    for match in match_by_current_stage:
        if match.winner_id is None:
            raise HTTPException(status_code=400, detail='Еще не все матчи текущей стадии сыграны!')

    next_stages = {'1/8': '1/4', '1/4': '1/2', '1/2': 'Финал'}

    match_by_next_stage = [m for m in matches if m.type == next_stages[plf.current_stage]]
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