import scipy.stats

from src.setup1.db import get_connection
import numpy as np

max_goals = 10

def overall_goals():
    con = get_connection()
    cursor = con.cursor()
    overall_goal_query = """SELECT SUM(goals_scored * tournament_weight) / SUM(tournament_weight)
                          FROM (SELECT home_score as goals_scored, tournament_weight \
                                FROM matches \
                                UNION ALL \
                                SELECT away_score as goals_scored, tournament_weight \
                                FROM matches) as all_matches"""   #calculating the average goals across all tournaments normalized by weight
    cursor.execute(overall_goal_query)
    overall_avg_goals = float(cursor.fetchone()[0])
    print(overall_avg_goals)
    if overall_avg_goals is None:
        raise ValueError("No match data found.")
    return overall_avg_goals



def poisson_attack_strength(overall_avg_goals):
    con = get_connection()
    cursor = con.cursor()

    team_attack_query = """SELECT team_id, SUM(goals_scored * tournament_weight) / NULLIF(SUM(tournament_weight),0) / %s 
        AS attack_strength FROM 
        (SELECT home_team_id as team_id, home_score as goals_scored, tournament_weight FROM matches     
         UNION ALL     
         SELECT away_team_id as team_id, away_score as goals_scored, tournament_weight FROM matches 
        ) as all_matches GROUP BY team_id;
    """ # calculating the number of goals score by each team normalized by tournament and diving by overall average goals to see if they score more or less than the average
    cursor.execute(team_attack_query,(overall_avg_goals,))
    attack_strength = cursor.fetchall()
    new_attack_strength={}
    for i in attack_strength:
        if i[1] is not None:
            new_attack_strength[i[0]] = float(i[1])
    cursor.close()
    con.close()
    return new_attack_strength

def poisson_defense_strength(overall_avg_goals):
    con = get_connection()
    cursor = con.cursor()
    team_defense_query = """SELECT team_id, SUM(goals_conceded * tournament_weight) / NULLIF(SUM(tournament_weight),0) / %s 
        AS defense_strength FROM 
        (SELECT home_team_id as team_id, away_score as goals_conceded, tournament_weight FROM matches     
         UNION ALL     
         SELECT away_team_id as team_id, home_score as goals_conceded, tournament_weight FROM matches 
        ) as all_matches GROUP BY team_id;
    """ # calculating the number of goals conceded by each team normalized by tournament and diving by overall average goals to see if they concede more or less than the average. Lower defense score is better
    cursor.execute(team_defense_query,(overall_avg_goals,))
    defense_strength = cursor.fetchall()
    new_defense_strength={}
    for i in defense_strength:
        if i[1] is not None:
            new_defense_strength[i[0]] = float(i[1]) #basically turning the list into a dict for easier lookup.
    cursor.close()
    con.close()
    return new_defense_strength

def calculate_xg(attack_strength, defense_strength, home_team, away_team, neutral,overall_avg_goals):
    home_team_attack = attack_strength.get(home_team, 1.0)
    home_team_defense = defense_strength.get(home_team, 1.0)
    away_team_attack = attack_strength.get(away_team, 1.0)
    away_team_defense = defense_strength.get(away_team, 1.0) # get attack and defense strengths for both teams

    home_lambda_score=(home_team_attack*away_team_defense*overall_avg_goals) # formula for lambda is first_attack_strength times second_defense_strength°overall_avg goals
    away_lambda_score=(away_team_attack*home_team_defense*overall_avg_goals)

    if not neutral:
        home_lambda_score*=1.15 # if its a home game, accounting for advantage

    return home_lambda_score, away_lambda_score
    
def predict_match(home_lambda, away_lambda):
    home_pmf_list = []
    away_pmf_list=[]
    home_win = 0
    draw = 0
    away_win = 0
    for i in range(max_goals+1):
        home_pmf_list.append(scipy.stats.poisson.pmf(i,home_lambda))
        away_pmf_list.append(scipy.stats.poisson.pmf(i,away_lambda)) # calculate the probability of home and away team scoring each number of goals untill 10 goals. so the probability each team scores 0,1,2,... so on

    scoreline_probabilities = np.zeros((max_goals + 1, max_goals + 1)) # creating an array to store our probabilities
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            scoreline_probabilities[i][j] = home_pmf_list[i]*away_pmf_list[j] # formual for a scoreline probability is the probability of the team scoring i goals multipled by the other team scoreing j goals
            if i > j:
                home_win += scoreline_probabilities[i][j] #each time the number of goals of home is greater, we add the probability of that outcome to our home_win probability, same for away. if the score is equal we add it to draw probabilities.
            elif i == j:
                draw += scoreline_probabilities[i][j]
            else:
                away_win += scoreline_probabilities[i][j]
    return scoreline_probabilities, home_win, draw, away_win