import json
import random
from fastapi import HTTPException
import itertools

from database import Session
from models.league import League
from models.player import Player
from models.group import Group
from dto import league as league_dto
from dto import group as group_dto
from dto import match as match_dto
from dto import playoff as playoff_dto
from . import group as group_service
from . import match as match_service
from . import playoff as playoff_service

LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
           'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']


# Получить список всех лиг турнира
def get_all_leagues(db: Session, t_id: int):
    return db.query(League).filter_by(tournament_id=t_id).all()


# Получить лигу по id
def get_league_by_id(db: Session, league_id: int):
    return db.query(League).filter_by(league_id=league_id).first()


# Создать лигу
def create_league(db: Session, t_id: int, data: league_dto.LeagueCreate):
    new_league = League(
        name=data.name,
        n_groups=data.n_groups,
        tournament_id=t_id
    )
    try:
        db.add(new_league)
        db.commit()
        db.refresh(new_league)
    except Exception as e:
        db.rollback()
        print(e)

    return new_league


# Удалить лигу по id
def delete_league(db: Session, league_id: int):
    lg = db.query(League).filter_by(league_id=league_id).first()
    db.delete(lg)
    db.commit()
    return lg


# Обновить лигу по id
def update_league(db: Session, league_id: int, draw_completed: bool):
    league = db.query(League).filter_by(league_id=league_id).first()
    league.draw_completed = draw_completed

    try:
        db.add(league)
        db.commit()
        db.refresh(league)
    except Exception as e:
        db.rollback()
        print(e)

    return league


# Добавить в лигу игроков
def add_players(db: Session, league_id: int, player_ids: str):
    new_player_ids = [int(item) for item in player_ids.split(',')]
    ids = [i[0] for i in db.query(Player.player_id).all()]

    league = db.query(League).filter_by(league_id=league_id).first()

    for p in new_player_ids:
        if p not in ids:
            raise HTTPException(status_code=404, detail=f'Player with id = {p} not found')

    if league.players == "":
        league.players = ','.join([str(i) for i in new_player_ids])
    else:
        league.players = league.players + ',' + ','.join([str(i) for i in new_player_ids])

    try:
        db.add(league)
        db.commit()
        db.refresh(league)
    except Exception as e:
        print(e)
        db.rollback()

    return league


# Удалить игрока из лиги
def delete_player(db: Session, league_id: int, player_id: int):
    league = db.query(League).filter_by(league_id=league_id).first()
    league_players = league.players.split(',')
    print(league_players)

    ids = [i[0] for i in db.query(Player.player_id).all()]
    if player_id not in ids:
        raise HTTPException(status_code=404, detail=f'Player with id = {player_id} not found')

    if str(player_id) not in league_players:
        raise HTTPException(status_code=404, detail=f'Player with id = {player_id} not found '
                                                    f'in the list of current league players ')

    league_players.remove(str(player_id))
    league.players = ','.join(league_players)
    print(league_players)

    try:
        db.add(league)
        db.commit()
        db.refresh(league)
    except Exception as e:
        print(e)
        db.rollback()

    return league


# Провести жеребьевку
def draw(db: Session, league_id: int):
    league = db.query(League).filter_by(league_id=league_id).first()
    if league.players != "":
        ids = [int(i) for i in league.players.split(',')]
    else:
        raise HTTPException(status_code=400, detail=f'The list of players is empty')

    if len(ids) % league.n_groups > 0:
        raise HTTPException(status_code=400, detail=f'The number of players must be a multiple of 4')

    players = db.query(Player).filter(Player.player_id.in_(ids)).order_by(Player.rating.desc()).all()

    n_iter = len(ids) // league.n_groups
    for i in range(n_iter):
        choices = LETTERS[0:league.n_groups]
        for j in range(league.n_groups):
            group_name = random.choice(choices)
            choices.remove(group_name)

            player = players[0]
            players.remove(player)

            data = group_dto.GroupCreate(
                player_id=player.player_id,
                group_name=group_name,
                score=0
            )

            group_service.add_player_to_group(db, data, league_id)

    groups = db.query(Group).filter_by(league_id=league_id).all()
    create_group_matches(db, league.league_id, league.n_groups, groups)
    update_league(db, league.league_id, True)
    return "success"


# Создание групповых матчей
def create_group_matches(db: Session, league_id: int, n_groups: int, groups: list):

    for i in range(n_groups):
        group = [g for g in groups if g.group_name == LETTERS[i]]
        for p1, p2 in itertools.combinations(group, 2):
            match = match_dto.MatchCreate(
                player1_id=p1.player_id,
                player2_id=p2.player_id,
                type="Групповой",
                score="0-0",
                invoice_by_batch="0-0 0-0 0-0",
                group_name=LETTERS[i],
                league_id=league_id,
            )

            match_service.create_match(db, match)


def complete_the_group_stage(db: Session, league_id: int):
    league = db.query(League).filter_by(league_id=league_id).first()
    if league.group_stage_completed :
        raise HTTPException(status_code=400, detail="Групповой этап уже завершен!")
    league.group_stage_completed = True
    n = match_service.get_count_unplayed_group_matches(db, league_id)

    if n != 0:
        raise HTTPException(status_code=400, detail=f"{n} матча/матчей в групповом этапе еще не сыграно")

    groups = group_service.get_all_groups(db, league_id)
    if group_service.conflict_search(groups):
        raise HTTPException(status_code=400, detail="Разрешите конфликтные ситуации")

    if len(groups) == 0:
        raise HTTPException(status_code=400, detail="Жеребьевка еще не проведена")

    parse_by_place = [[], [], []]
    for g in groups:
        if g["place"] == 1:
            parse_by_place[0].append(g["player_id"])
        elif g["place"] == 2:
            parse_by_place[1].append(g["player_id"])
        elif g["place"] == 3:
            parse_by_place[2].append(g["player_id"])

    # Создание плей-офф
    playoff_types = ["Золотой", "Серебрянный", "Бронзовый"]
    for i, t in enumerate(playoff_types):
        if len(parse_by_place[i]) > 0:
            new_playoff = playoff_dto.PlayoffCreate(
                name=t,
                start_stage=playoff_stage(parse_by_place[i]),
                current_stage=playoff_stage(parse_by_place[i]),
                league_id=league_id
            )
            playoff_service.create_playoff(db, new_playoff)

    playoffs = playoff_service.get_all_playoffs(db, league_id)

    for i in range(len(playoffs)):
        num_players = len(parse_by_place[i])

        for j in range(0, num_players, 4):
            new_match = match_dto.MatchCreate(
                player1_id=parse_by_place[i][j],
                player2_id=parse_by_place[i][j+2],
                type=playoffs[i].current_stage,
                score="0-0",
                invoice_by_batch="0-0 0-0 0-0",
                playoff_id=playoffs[i].playoff_id,
                league_id=league_id,
            )
            match_service.create_match(db, new_match)
            new_match.player1_id = parse_by_place[i][j+1]
            new_match.player2_id = parse_by_place[i][j+3]
            match_service.create_match(db, new_match)

        n_matches = {'Финал': 1, '1/2': 2, '1/4': 4, '1/8': 8}
        for key, val in n_matches.items():
            if key == playoffs[i].current_stage:
                break
            for k in range(val):
                new_match = match_dto.MatchCreate(
                    player1_id=-1,
                    player2_id=-1,
                    type=key,
                    score="0-0",
                    invoice_by_batch="0-0 0-0 0-0",
                    playoff_id=playoffs[i].playoff_id,
                    league_id=league_id,
                )
                match_service.create_match(db, new_match)
    db.commit()

    return "success"


def playoff_stage(player_list):
    num_teams = len(player_list)

    if num_teams == 2:
        return "Финал"
    elif num_teams == 4:
        return "1/2"
    elif num_teams == 8:
        return "1/4"
    elif num_teams == 16:
        return "1/6"
    else:
        return "Unknown stage"
