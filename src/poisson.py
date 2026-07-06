from setup1.db import get_connection
import psycopg2

def poisson_calc():
    con = get_connection()
    cursor = con.cursor()
    overall_query = """SELECT SUM(goals_scored * tournament_weight) / SUM(tournament_weight)
    FROM (
            SELECT home_score as goals_scored, tournament_weight FROM matches
            UNION ALL
            SELECT away_score as goals_scored, tournament_weight FROM matches
         ) as all_matches"""
    cursor.execute(overall_query)
    overall_avg_goals= cursor.fetchone()[0]


    team_query = """SELECT team_id, SUM(goals_scored * tournament_weight) / NULLIF(SUM(tournament_weight),0) / %s 
        FROM 
        (SELECT home_team_id as team_id, home_score as goals_scored, tournament_weight FROM matches     
         UNION ALL     
         SELECT away_team_id as team_id, away_score as goals_scored, tournament_weight FROM matches 
        ) as all_matches GROUP BY team_id;
    """
    cursor.execute(team_query,(overall_avg_goals,))
    attack_strength = cursor.fetchall()

poisson_calc()
