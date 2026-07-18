from src.api.startup import state
import numpy as np
from src.stat_calc.poisson import calculate_xg, predict_match, overall_goals

avg_goals = overall_goals()


def predict(home_team, away_team, neutral, tournament_weight=1.0):
    # Get everything from state
    attack_strength = state['attack_strength']
    defense_strength = state['defense_strength']
    elo_ratings = state['elo_ratings']
    ranking_map = state['ranking_map']
    form_map = state['form_map']
    draw_rates = state['draw_rate_map']
    model_xg = state['xgb_model']
    model_lr = state['lr_model']
    scaler = state['scaler']

    home_elo = elo_ratings.get(home_team, 1500)
    away_elo = elo_ratings.get(away_team, 1500)
    home_rank = ranking_map.get(home_team, 200)
    away_rank = ranking_map.get(away_team, 200)
    home_defense_score = defense_strength.get(home_team, 1.0)
    away_defense_score = defense_strength.get(away_team, 1.0)
    home_form = form_map.get(home_team, 0.5)
    away_form = form_map.get(away_team, 0.5)
    home_draw_rate = draw_rates.get(home_team, 0.24)
    away_draw_rate = draw_rates.get(away_team, 0.24)

    home_xg, away_xg = calculate_xg(attack_strength, defense_strength,home_team, away_team, neutral, avg_goals)
    elo_difference = home_elo - away_elo
    rank_difference = home_rank - away_rank
    xg_difference = home_xg - away_xg
    defense_difference = away_defense_score - home_defense_score
    form_difference = home_form - away_form
    elo_closeness = abs(elo_difference)
    elo_win_probability = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
    combined_defense_strength = home_defense_score + away_defense_score
    overall_strength_gap = abs(elo_difference) + abs(rank_difference)
    team_balance = abs(xg_difference) + abs(defense_difference)
    home_attack_vs_away_defense = home_xg / away_defense_score
    away_attack_vs_home_defense = away_xg / home_defense_score
    neutral_int = int(neutral)
    combined_strength = home_elo + away_elo
    adjusted_elo_difference = elo_difference if neutral else elo_difference + 60

    features_array = np.array([[
        home_elo, away_elo, elo_difference, home_rank, away_rank,
        rank_difference, home_xg, away_xg, home_draw_rate, away_draw_rate,
        home_form, away_form, tournament_weight, home_attack_vs_away_defense,
        away_attack_vs_home_defense, elo_closeness, elo_win_probability,
        xg_difference, defense_difference, form_difference,
        combined_defense_strength, overall_strength_gap, team_balance,
        combined_strength, adjusted_elo_difference
    ]])

    xgb_probs = model_xg.predict_proba(features_array)[0]
    features_scaled = scaler.transform(features_array)
    lr_probs = model_lr.predict_proba(features_scaled)[0]
    _, home_win_poisson, draw_poisson, away_win_poisson = predict_match(home_xg, away_xg)

    poisson_prob = np.array([away_win_poisson, draw_poisson, home_win_poisson])
    final_prob = 0.65 * xgb_probs + 0.25 * lr_probs + 0.10 * poisson_prob

    return {
        "home_win": float(final_prob[2]),
        "draw": float(final_prob[1]),
        "away_win": float(final_prob[0]),
        "elo_win_probability": float(elo_win_probability)
    }