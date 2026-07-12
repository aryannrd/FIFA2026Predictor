from src.setup1.db import get_connection, get_ranking_map
from src.stat_calc.poisson import overall_goals, poisson_attack_strength, poisson_defense_strength, calculate_xg
from src.stat_calc.elo import calculate_individual_elo

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

        data.append(ranking_map.get(row[1]))
        data.append(ranking_map.get(row[2]))#getting home and away ranks

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
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """

    cursor.executemany(insert_query,data_list)
    con.commit()
    cursor.close()
    con.close()

populate_match_features()





