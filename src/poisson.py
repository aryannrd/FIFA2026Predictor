from setup1.db import get_connection

def overall_goals():
    con = get_connection()
    cursor = con.cursor()
    overall_goal_query = """SELECT SUM(goals_scored * tournament_weight) / SUM(tournament_weight)
                          FROM (SELECT home_score as goals_scored, tournament_weight \
                                FROM matches \
                                UNION ALL \
                                SELECT away_score as goals_scored, tournament_weight \
                                FROM matches) as all_matches"""
    cursor.execute(overall_goal_query)
    overall_avg_goals = cursor.fetchone()[0]
    if overall_avg_goals is None:
        raise ValueError("No match data found.")
    return overall_avg_goals

overall_avg_goals = overall_goals()

def poisson_attack_strength():
    con = get_connection()
    cursor = con.cursor()

    team_attack_query = """SELECT team_id, SUM(goals_scored * tournament_weight) / NULLIF(SUM(tournament_weight),0) / %s 
        AS attack_strength FROM 
        (SELECT home_team_id as team_id, home_score as goals_scored, tournament_weight FROM matches     
         UNION ALL     
         SELECT away_team_id as team_id, away_score as goals_scored, tournament_weight FROM matches 
        ) as all_matches GROUP BY team_id;
    """
    cursor.execute(team_attack_query,(overall_avg_goals,))
    attack_strength = cursor.fetchall()
    new_attack_strength={}
    for i in attack_strength:
        new_attack_strength[i[0]] = i[1]
    cursor.close()
    con.close()
    return new_attack_strength

def poisson_defense_strength():
    con = get_connection()
    cursor = con.cursor()
    team_defense_query = """SELECT team_id, SUM(goals_conceded * tournament_weight) / NULLIF(SUM(tournament_weight),0) / %s 
        AS defense_strength FROM 
        (SELECT home_team_id as team_id, away_score as goals_conceded, tournament_weight FROM matches     
         UNION ALL     
         SELECT away_team_id as team_id, home_score as goals_conceded, tournament_weight FROM matches 
        ) as all_matches GROUP BY team_id;
    """
    cursor.execute(team_defense_query,(overall_avg_goals,))
    defense_strength = cursor.fetchall()
    new_defense_strength={}
    for i in defense_strength:
        new_defense_strength[i[0]] = i[1]
    cursor.close()
    con.close()
    return new_defense_strength

def calculate_xG(attack_strength, defense_strength, home_team, away_team, neutral):
    home_team_attack = attack_strength[home_team]
    home_team_defense = defense_strength[home_team]
    away_team_attack = attack_strength[away_team]
    away_team_defense = defense_strength[away_team]

    home_lambda_score=(home_team_attack*away_team_defense*overall_avg_goals)
    away_lambda_score=(away_team_attack*home_team_defense*overall_avg_goals)

    if not neutral:
        home_lambda_score*=1.0

    return home_lambda_score, away_lambda_score

