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

def train_model():
    features = ['home_elo', 'away_elo', 'elo_difference', 'home_rank', 'away_rank', 'rank_difference', 'home_xg', 'away_xg', 'neutral',
        'home_form', 'away_form', 'tournament_weight','home_value_log','away_value_log','home_attack_vs_away_defense','away_attack_vs_home_defense','elo_closeness', 'elo_win_probability','xg_difference','defense_difference','form_difference', 'combined_defense_strength','overall_strength_gap','team_balance']
    target = 'result'

    con = get_connection()
    query = """SELECT home_elo, away_elo, elo_difference, home_rank, away_rank, rank_difference, home_xg, away_xg, neutral,home_defense_score, away_defense_score,
        home_form, away_form, result, tournament_weight,home_market_value, away_market_value FROM match_features"""
    df = pd.read_sql(query, con) #getting also sql data into a dataset

    home_defense_median = df['home_defense_score'].median()
    away_defense_median = df['away_defense_score'].median()
    df['home_defense_score'] = df['home_defense_score'].replace(0, home_defense_median)
    df['away_defense_score'] = df['away_defense_score'].replace(0,away_defense_median)

    df['home_rank'] = df['home_rank'].fillna(200)
    df['away_rank'] = df['away_rank'].fillna(200)
    df['rank_difference'] = df['home_rank'] - df['away_rank']
    df['neutral'] = df['neutral'].astype(int)

    df['home_market_value'] = df['home_market_value'].replace(0, np.nan)
    df['away_market_value'] = df['away_market_value'].replace(0, np.nan)
    median_value = df['home_market_value'].median()
    df['home_market_value'] = df['home_market_value'].fillna(median_value)
    df['away_market_value'] = df['away_market_value'].fillna(median_value)
    df['home_value_log'] = np.log1p(df['home_market_value'])
    df['away_value_log'] = np.log1p(df['away_market_value'])
    df = df.drop(columns=['home_market_value', 'away_market_value'])

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
    con.close()

    X = df[features]
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.25, random_state=42, stratify=y) #training on 80% dataset, testing on 20%
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
        random_state=42,
        n_estimators=100,
        max_depth=4,  # Shallow trees prevent overfitting the noise
        learning_rate=0.05,  # Slower learning rate prevents aggressive jumps
        subsample=0.8,  # Force it to look at different subsets of matches
        colsample_bytree=0.8
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


train_model()
