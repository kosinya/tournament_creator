import json
import random
from fastapi import HTTPException
import itertools

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch

from sqlalchemy import text

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

pdfmetrics.registerFont(TTFont('DejaVu', r'C:\Users\admin\Documents\GitHub\tournament_creator\services\DejaVuSans.ttf'))

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
        raise HTTPException(status_code=400, detail=f'Список игроков пуст!')

    if len(ids) % league.n_groups > 0:
        for i in range(league.n_groups - len(ids) % league.n_groups):
            ids.append(0)

    players = db.query(Player).filter(Player.player_id.in_(ids)).order_by(Player.rating.desc()).all()
    if len(players) % league.n_groups > 0:
        for i in range(league.n_groups - len(players) % league.n_groups):
            players.append(Player(player_id=0, rating=0))

    n_iter = len(ids) // league.n_groups
    for i in range(n_iter):
        choices = LETTERS[0:league.n_groups]
        for j in range(league.n_groups):
            player = players[0]
            players.remove(player)

            group_name = random.choice(choices)
            choices.remove(group_name)

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
            if p1.player_id == 0 or p2.player_id == 0:
                continue
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

    for i in parse_by_place:
        if len(i) % league.n_groups != 0:
            for j in range(league.n_groups - len(i) % league.n_groups):
                i.append(0)

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

        n_matches = {'Финал': 1, '3 место': 1, '1/2': 2, '1/4': 4, '1/8': 8}
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


def get_pdf_result(db: Session, league_id: int):
    playoffs = playoff_service.get_all_playoffs(db, league_id)

    query = text(f"""SELECT m.*, p1.surname AS 'player1_surname', p1.name AS 'player1_name',
                         p2.surname AS 'player2_surname', p2.name AS 'player2_name'
                         FROM matches m
                         JOIN players p1 ON m.player1_id = p1.player_id
                         JOIN players p2 ON m.player2_id = p2.player_id
                         WHERE m.league_id = {league_id} AND m.playoff_id = {playoffs[0].playoff_id} AND m.type IN ('Финал', '3 место');
        """)

    results = db.execute(query).fetchall()
    winners = {}
    for r in results:
        if r.type == "Финал":
            if r.player1_id == r.winner_id:
                winners['first'] = r.player1_surname + r.player1_name
                winners['second'] = r.player2_surname + r.player2_name
            else:
                winners['first'] = r.player2_surname + r.player2_name
                winners['second'] = r.player1_surname + r.player1_name
        else:
            if r.player1_id == r.winner_id:
                winners['third'] = r.player1_surname + r.player1_name
            else:
                winners['third'] = r.player2_surname + r.player2_name

    winner = "Иван Иванов"
    second_place = "Петр Петров"
    third_place = "Сергей Сергеев"
    bronze_color = colors.Color(0.8, 0.5, 0.2)

    c = canvas.Canvas(f"league{league_id}_results.pdf", pagesize=letter)
    width, height = letter

    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, fill=1)

    # Заголовок
    c.setFont("DejaVu", 24)
    c.setFillColor(colors.black)
    c.drawCentredString(width / 2, height - 100, "Результаты соревнования")

    # Отступы
    margin = 100
    line_height = 30

    # 1 место
    c.setFont("DejaVu", 20)
    c.drawString(margin, height - 150, f"1. Победитель: {winner}")

    # 2 место
    c.setFont("DejaVu", 20)
    c.drawString(margin, height - 180, f"2. Призер 2 места: {second_place}")

    # 3 место
    c.setFont("DejaVu", 20)
    c.drawString(margin, height - 210, f"3. Призер 3 места: {third_place}")

    # Подпись
    c.setFont("DejaVu", 16)
    c.drawCentredString(width / 2, height - 300, "Спасибо за участие!")

    # Сохранение PDF
    c.save()


    return 0
