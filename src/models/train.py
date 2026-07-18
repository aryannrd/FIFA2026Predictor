import numpy as np
import pandas as pd
from src.setup1.db import get_connection
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score
import joblib
from sklearn.metrics import log_loss
from sklearn.calibration import CalibratedClassifierCV
from src.stat_calc.form import draw_last_20
import pandas as pd

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def train_model():
    features = ['home_elo', 'away_elo', 'elo_difference', 'home_rank', 'away_rank', 'rank_difference', 'home_xg', 'away_xg', 'home_draw_rate_last20','away_draw_rate_last20',
        'home_form', 'away_form', 'tournament_weight','home_attack_vs_away_defense','away_attack_vs_home_defense','elo_closeness', 'elo_win_probability','xg_difference','defense_difference','form_difference', 'combined_defense_strength','overall_strength_gap','team_balance', 'combined_strength', 'adjusted_elo_difference']
    target = 'result'

    con = get_connection()
    query = """SELECT 
    mf.match_id,
    m.date,
    mf.home_elo,
    mf.away_elo,
    mf.elo_difference,
    mf.home_rank,
    mf.away_rank,
    mf.rank_difference,
    mf.home_xg,
    mf.away_xg,
    mf.neutral,
    mf.home_defense_score,
    mf.away_defense_score,
    mf.home_form,
    mf.away_form,
    mf.result,
    mf.tournament_weight
FROM match_features mf
JOIN matches m
ON mf.match_id = m.id"""
    df = pd.read_sql(query, con) #getting also sql data into a dataset
    home_defense_median = df['home_defense_score'].median()
    away_defense_median = df['away_defense_score'].median()
    df['home_defense_score'] = df['home_defense_score'].replace(0, home_defense_median)
    df['away_defense_score'] = df['away_defense_score'].replace(0,away_defense_median)

    df['home_rank'] = df['home_rank'].fillna(200)
    df['away_rank'] = df['away_rank'].fillna(200)
    df['rank_difference'] = df['home_rank'] - df['away_rank']
    df['neutral'] = df['neutral'].astype(int)

    df['home_attack_vs_away_defense'] = df['home_xg']/df['away_defense_score']
    df['away_attack_vs_home_defense'] = df['away_xg'] / df['home_defense_score']

    df['elo_closeness'] = abs(df['elo_difference'])
    df['combined_defense_strength'] = (df['home_defense_score'] +df['away_defense_score'])
    df["elo_win_probability"] = (1 /(1 + 10 ** ((df["away_elo"] - df["home_elo"]) / 400)))
    df["xg_difference"] = (df["home_xg"] -df["away_xg"])
    df["defense_difference"] = (df["away_defense_score"] -df["home_defense_score"])
    df["form_difference"] = (df["home_form"] -df["away_form"])
    df['overall_strength_gap'] = (abs(df['elo_difference']) +abs(df['rank_difference']))
    df['team_balance'] = (abs(df['xg_difference']) +abs(df['defense_difference']))
    df['combined_strength'] = df['home_elo'] + df['away_elo']
    con.close()
    draw_rates = draw_last_20()
    df["home_draw_rate_last20"] = df["match_id"].apply(
        lambda x: draw_rates[x]["home_draw_rate_last20"]
    )

    df["away_draw_rate_last20"] = df["match_id"].apply(
        lambda x: draw_rates[x]["away_draw_rate_last20"]
    )
    df["adjusted_elo_difference"] = (
            df["elo_difference"]
            - (~df["neutral"]) * 60
    )
    df['tournament_weight'] = df['tournament_weight'].fillna(0.5)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=features)
    X = df[features]
    y = df[target]

    train_df = df[df['date'] < '2023-01-01']
    test_df = df[df['date'] >= '2023-01-01']

    X_train = train_df[features]
    y_train = train_df[target]

    X_test = test_df[features]
    y_test = test_df[target]
    #X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.3, random_state=42, stratify=y) #training on 80% dataset, testing on 20%
    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    model = LogisticRegression(max_iter=1000,class_weight='balanced') #training a logisticRegression models
    model.fit(X_train_scaled,y_train)
    accuracy = accuracy_score(y_test, model.predict(X_test_scaled))
    print(f"Logistic Regression: {accuracy}")

    model_rf = RandomForestClassifier(random_state=42, class_weight='balanced')
    model_rf.fit(X_train, y_train)
    accuracy_rf = accuracy_score(y_test, model_rf.predict(X_test))
    print(f"Random Forest: {accuracy_rf}")

    sample_weights = compute_sample_weight('balanced', y_train)
    model_xg = XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        random_state=42,
        n_estimators=300,
        max_depth=3,
        learning_rate=0.05,
    )
    model_xg.fit(X_train, y_train, sample_weight=sample_weights)
    accuracy_xg = accuracy_score(y_test, model_xg.predict(X_test))
    print(f"XGBoost: {accuracy_xg}")

    print("\nLogistic Regression")
    print(classification_report(
        y_test,
        model.predict(X_test_scaled)
    ))

    print("\nRandom Forest")
    print(classification_report(
        y_test,
        model_rf.predict(X_test)
    ))

    print("\nXGBoost")
    print(classification_report(
        y_test,
        model_xg.predict(X_test)
    ))
    importance = pd.DataFrame({
        "feature": X.columns,
        "importance": model_rf.feature_importances_
    })

    print(
        importance.sort_values(
            "importance",
            ascending=False
        )
    )
    print("XGBoost Classes:", model_xg.classes_)
    y_prob_xg = model_xg.predict_proba(X_test)
    print("XGBoost Log Loss:", log_loss(y_test, y_prob_xg))
    joblib.dump(model, os.path.join(BASE_DIR, 'logistic_regression.pkl'))
    joblib.dump(model_xg, os.path.join(BASE_DIR, 'xgboost.pkl'))
    joblib.dump(scaler, os.path.join(BASE_DIR, 'scaler.pkl'))
    joblib.dump(model_rf, os.path.join(BASE_DIR, 'random_forest.pkl'))
    return