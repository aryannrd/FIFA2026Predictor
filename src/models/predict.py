import joblib
import numpy as np
import pandas as pd
from src.models.explainers import explain_prediction
from src.stat_calc.poisson import overall_goals, calculate_xg, poisson_attack_strength, poisson_defense_strength, \
    predict_match
from src.stat_calc.elo import calculate_individual_elo
from src.setup1.db import get_connection, get_team_ids, get_ranking_map, get_current_form, get_current_draw_rates
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# load everything once at startup
avg_goals = overall_goals()
attack_strength = poisson_attack_strength(avg_goals)
defense_strength = poisson_defense_strength(avg_goals)
_, elo_ratings = calculate_individual_elo()
con = get_connection()
cursor = con.cursor()
form_map = get_current_form(cursor)
draw_rates = get_current_draw_rates(cursor)
ranking_map = get_ranking_map(cursor)
scaler = joblib.load(os.path.join(BASE_DIR, 'scaler.pkl'))
model_lr = joblib.load(os.path.join(BASE_DIR, 'logistic_regression.pkl'))
model_xg = joblib.load(os.path.join(BASE_DIR, 'xgboost.pkl'))



def predict(home_team, away_team, neutral,tournament_weight=1.0):
    # Raw lookups
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

    # xG from Poisson
    home_xg, away_xg = calculate_xg(attack_strength, defense_strength,
                                    home_team, away_team, neutral, avg_goals)

    # Engineered features
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
    neutral = int(neutral)
    combined_strength = home_elo + away_elo
    if neutral:
        adjusted_elo_difference = elo_difference
    else:
        adjusted_elo_difference = elo_difference + 60

    features_array = np.array([[
        home_elo,
        away_elo,
        elo_difference,
        home_rank,
        away_rank,
        rank_difference,
        home_xg,
        away_xg,
        home_draw_rate,
        away_draw_rate,
        home_form,
        away_form,
        tournament_weight,
        home_attack_vs_away_defense,
        away_attack_vs_home_defense,
        elo_closeness,
        elo_win_probability,
        xg_difference,
        defense_difference,
        form_difference,
        combined_defense_strength,
        overall_strength_gap,
        team_balance,
        combined_strength,
        adjusted_elo_difference
    ]])

    probs = model_xg.predict_proba(features_array)[0]
    x, home_win_poisson, draw_poisson, away_win_poisson = predict_match(home_xg, away_xg)
    xgb_prob = np.array([
        probs[0],  # away
        probs[1],  # draw
        probs[2]  # home
    ])

    features_scaled = scaler.transform(features_array)
    probs = model_lr.predict_proba(features_scaled)[0]
    lr_prob = np.array([
        probs[0],  # away
        probs[1],  # draw
        probs[2]  # home
    ])

    poisson_prob = np.array([
        away_win_poisson,
        draw_poisson,
        home_win_poisson
    ])
    final_prob = (
            0.65 * xgb_prob +
            0.1 * poisson_prob +
            0.25 * lr_prob
    )
    return final_prob




