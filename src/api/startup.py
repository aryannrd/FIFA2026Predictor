from datetime import datetime, timedelta
from src.api.config import LAST_UPDATE_FILE
from src.setup1.db import get_team_ids, get_connection, get_ranking_map, get_current_form, get_current_draw_rates
from src.setup1.setup import flatten, competition_weights
import joblib
import numpy as np
import os

from src.stat_calc.poisson import overall_goals

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
state = {}
og = overall_goals()

def initialize():
    from src.setup1.setup import setup  # import inside function to avoid module-level execution
    from src.stat_calc.poisson import overall_goals, poisson_attack_strength, poisson_defense_strength
    from src.stat_calc.elo import calculate_individual_elo
    if needs_update():
        setup()
        save_update_time()
    con = get_connection()
    cursor = con.cursor()
    state['team_id_map'] = get_team_ids(cursor)
    state['flat_comp_weights'] = flatten(competition_weights)
    state['attack_strength'] = poisson_attack_strength(og)
    state['defense_strength'] = poisson_defense_strength(og)
    _, state['elo_ratings'] = calculate_individual_elo()
    state['ranking_map'] = get_ranking_map(cursor)
    state['form_map'] = get_current_form(cursor)
    state['draw_rate_map'] = get_current_draw_rates(cursor)
    state['xgb_model'] = joblib.load(os.path.join(BASE_DIR, '../models/xgboost.pkl'))
    state['lr_model'] = joblib.load(os.path.join(BASE_DIR, '../models/logistic_regression.pkl'))
    state['scaler'] = joblib.load(os.path.join(BASE_DIR, '../models/scaler.pkl'))
    cursor.close()
    con.close()

def needs_update() -> bool:
    if not LAST_UPDATE_FILE.exists():
        return True
    with LAST_UPDATE_FILE.open("r") as f:
        last_update = datetime.fromisoformat(f.read().strip())
    return datetime.now() - last_update > timedelta(days=30)


def save_update_time():
    LAST_UPDATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LAST_UPDATE_FILE.open("w") as f:
        f.write(datetime.now().isoformat())


initialize()