from src.setup1.db import get_connection, get_ranking_map
from src.stat_calc.poisson import overall_goals, poisson_attack_strength, poisson_defense_strength, calculate_xg
from src.stat_calc.elo import calculate_individual_elo
from src.setup1.marketvalue import market_value, mapping_values


def populate_match_features():
    data_list=[]
    con = get_connection()
    cursor= con.cursor()

    avg_goals = overall_goals()
    attack_strength = poisson_attack_strength(avg_goals)
    defense_strength = poisson_defense_strength(avg_goals)
    match_elo_snapshots, elo_ratings = calculate_individual_elo()
    ranking_map = get_ranking_map(cursor)

    search_query = "SELECT id, home_team_id, away_team_id, home_score, away_score, neutral FROM matches; "
    cursor.execute(search_query)
    rows = cursor.fetchall()
    for row in rows:
        data=[]
        data.append(row[0]) # match_id

        elo = match_elo_snapshots[row[0]]
        data.append(elo[0])
        data.append(elo[1]) #getting home_elo and away_elo

        data.append(ranking_map.get(row[1],200))
        data.append(ranking_map.get(row[2],200))#getting home and away ranks

        home_xg, away_xg = calculate_xg(attack_strength,defense_strength,row[1], row[2], row[5], avg_goals)
        data.append(home_xg)
        data.append(away_xg) #adding xG's
        data.append(row[5]) #neutral

        if row[3] > row[4]: #result being appended
            data.append(2)
        elif row[3] < row[4]:
            data.append(0)
        else:
            data.append(1)

        data_list.append(tuple(data,))


    for i, row in enumerate(data_list):
        if len(row) != 9:
            print(f"Row {i} has {len(row)} elements: {row}")
            break

    insert_query = """ INSERT INTO match_features(match_id, home_elo, away_elo, home_rank, away_rank, home_xg, away_xg, neutral, result)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (match_id) DO NOTHING;
    """

    cursor.executemany(insert_query,data_list)
    con.commit()
    update_match_features(defense_strength)
    cursor.close()
    con.close()
    return

def update_match_features(def_score):
    values_df= mapping_values()
    values_df['market_value_eur'] = values_df['market_value_eur'].fillna(0).astype(int)
    market_val_score = dict(zip(values_df['team_id'].astype(int), values_df['market_value_eur']))
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("SELECT match_id, home_team_id, away_team_id FROM match_features")
    rows = cursor.fetchall()

    update_query = """UPDATE match_features SET home_defense_score = %s, away_defense_score = %s, 
                      home_market_value  = %s,away_market_value  = %s WHERE match_id = %s """
    update_list = []
    for row in rows:
        match_id = row[0]
        home_team_id = row[1]
        away_team_id = row[2]
        home_def = def_score.get(home_team_id, 1.0)
        away_def = def_score.get(away_team_id, 1.0)
        home_mv = market_val_score.get(home_team_id, 0)
        away_mv = market_val_score.get(away_team_id, 0)
        update_list.append((home_def, away_def, home_mv, away_mv, match_id))

    cursor.executemany(update_query, update_list)
    con.commit()
    cursor.close()
    con.close()
    return





