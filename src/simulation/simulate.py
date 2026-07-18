import random
from src.models.predict import predict
from src.setup1.db import get_connection
import time

team_id_list =[]
def get_match_winner(home_team_id, away_team_id):
    result = predict(home_team_id, away_team_id, neutral=True)
    home_win = result['home_win']
    draw = result['draw']
    away_win = result['away_win']
    elo_win_home = result['elo_win_probability']
    elo_win_away = 1 -elo_win_home

    adjusted_home = home_win + draw * elo_win_home
    adjusted_away = away_win + draw * elo_win_away
    winner = random.choices([home_team_id, away_team_id],weights=[adjusted_home, adjusted_away],k=1)[0]

    return {
        "winner": winner,
        "home_probability": adjusted_home,
        "away_probability": adjusted_away
    }

def simulate_round(teams):
    winners = []
    for i in range(0, len(teams), 2):
        result = get_match_winner(teams[i],teams[i+1])
        winners.append(result["winner"])
    return winners


def simulate_tournament(teams_32):
    round_of_16 = simulate_round(teams_32)
    quarterfinals = simulate_round(round_of_16)
    semifinals = simulate_round(quarterfinals)
    finalists = simulate_round(semifinals)
    champion = get_match_winner(finalists[0], finalists[1])['winner']
    return champion

def run_simulations(teams_32, n=10000):
    results= []
    for i in range(n):
        results.append(simulate_tournament(teams_32))
    count = {}
    for winner in results:
        count[winner] = count.get(winner, 0) + 1
    return {team_id: count / n for team_id, count in count.items()}

def seed_teams():
    con = get_connection()
    cursor = con.cursor()
    query = """
    WITH team_matches AS (
        SELECT mf.home_team_id AS team_id, mf.home_elo AS elo , mf.home_rank AS rank,
        mf.home_xg AS xG, mf.home_form AS form ,m.date 
        FROM match_features AS mf
        INNER JOIN matches AS m
        ON mf.match_id = m.id
        UNION ALL
        SELECT mf.away_team_id AS team_id, mf.away_elo AS elo, mf.away_rank AS rank, mf.away_xg AS xG, mf.away_form AS form, m.date 
        FROM match_features AS mf
        INNER JOIN matches AS m
        ON mf.match_id = m.id
    ),
    recent AS (
        SELECT team_id, elo, rank, xG, form,
               ROW_NUMBER() OVER (PARTITION BY team_id ORDER BY date DESC) as rn
        FROM team_matches
    )
    SELECT team_id, elo
    FROM recent
    WHERE rn = 1
    ORDER BY elo DESC
    LIMIT 32;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    con.close()
    teams_arrange = []

    for i in range(len(rows)//2):
        teams_arrange.append(rows[i][0])
        teams_arrange.append(rows[(len(rows)-1-i)][0])

    return teams_arrange

teams_32 = seed_teams()
results = run_simulations(teams_32, n=5000)
print(results)