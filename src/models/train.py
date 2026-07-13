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
from sklearn.metrics import confusion_matrix

import joblib

def train_model():
    features = ['home_elo', 'away_elo', 'elo_difference', 'home_rank', 'away_rank', 'rank_difference', 'home_xg', 'away_xg', 'neutral','home_defense_score', 'away_defense_score',
        'home_form', 'away_form', 'is_heavy_favorite', 'is_heavy_underdog','tournament_weight']
    target = 'result'

    con = get_connection()
    query = """SELECT home_elo, away_elo, elo_difference, home_rank, away_rank, rank_difference, home_xg, away_xg, neutral,home_defense_score, away_defense_score,
        home_form, away_form, result, tournament_weight FROM match_features"""
    df = pd.read_sql(query, con) #getting also sql data into a dataset
    df['home_rank'] = df['home_rank'].fillna(200)
    df['away_rank'] = df['away_rank'].fillna(200)
    df['rank_difference'] = df['home_rank'] - df['away_rank']
    df['neutral'] = df['neutral'].astype(int)
    df['is_heavy_favorite'] = (df['elo_difference'] > 150).astype(int)
    df['is_heavy_underdog'] = (df['elo_difference'] < -150).astype(int)
    con.close()

    X = df[features]
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.25, random_state=42) #training on 80% dataset, testing on 20%

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
    """joblib.dump(model, 'models/logistic_regression.pkl')
    joblib.dump(model_xg, 'models/xgboost.pkl')
    joblib.dump(scaler, 'models/scaler.pkl')"""


train_model()
