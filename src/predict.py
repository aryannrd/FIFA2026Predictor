from src.poisson import overall_goals, calculate_xg, predict_match, poisson_attack_strength, poisson_defense_strength

avg_goals = overall_goals()
attack_strength = poisson_attack_strength(avg_goals)
defense_strength = poisson_defense_strength(avg_goals)
def predict(home_team, away_team, neutral):
    home_lambda, away_lambda = calculate_xg(attack_strength,defense_strength, home_team, away_team, neutral, avg_goals)
    scoreline_probabilities, home_win, draw, away_win = predict_match(home_lambda,away_lambda)
    return {"home_win": home_win, "draw" : draw, "away_win": away_win}, scoreline_probabilities

