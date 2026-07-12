from src.setup1.db import get_connection

def calculate_individual_elo():
    con = get_connection()
    cursor = con.cursor()
    fetch_query = "SELECT id, home_team_id, away_team_id, home_score, away_score, tournament_weight, date FROM matches ORDER BY date ASC"
    cursor.execute(fetch_query)
    rows = cursor.fetchall()  # getting all matches to calculate elo

    default = 1500
    elo_ratings = {}
    match_elo_snapshots = {}
    actual_result = 0.0
    for row in rows:
        home_elo = elo_ratings.get(row[1], default)
        away_elo = elo_ratings.get(row[2], default)
        if row[3] > row[4]:  # home team wins
            actual_result = 1.0
        elif row[3] < row[4]:  # away team wins
            actual_result = 0.0
        else:  # draw
            actual_result = 0.5

        expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))  # formula for expected is this
        expected_away = 1 - expected_home
        k_factor = float(30 * row[5])  # considering tournamernt weight
        new_home_elo = home_elo + k_factor * (actual_result - expected_home)
        new_away_elo = away_elo + k_factor * ((1 - actual_result) - expected_away)
        match_elo_snapshots[row[0]] = (home_elo, away_elo)
        elo_ratings[row[1]] = new_home_elo
        elo_ratings[row[2]] = new_away_elo  # updating both elo's
    return match_elo_snapshots, elo_ratings

