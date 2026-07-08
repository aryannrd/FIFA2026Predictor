import kagglehub
import os
import pandas as pd
from db import get_connection, get_team_ids
from rankings import sql_ranking


def flatten(tournaments: dict):
    updated_tournament_dict = {}
    for i in tournaments.values():
        for j in i["competitions"]:
            updated_tournament_dict[j] = i["weight"]
    return updated_tournament_dict

def setup():

    path = kagglehub.dataset_download("martj42/international-football-results-from-1872-to-2017")

    print("Path to dataset files:", path)
    csv_path = os.path.join(path, 'results.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print("Success!")
        print(df.head())
    else:
        print("Error!")

    df = df.dropna(subset=['home_score', 'away_score'])
    df['date'] = pd.to_datetime(df['date'])
    df= df[df['date'] > '2000-01-01']

    competition_weights = {
        "Tier 1": {
            "weight": 1.00,
            "competitions": [
                "FIFA World Cup"
            ]
        },
        "Tier 2": {
            "weight": 0.90,
            "competitions": [
                "FIFA World Cup qualification"
            ]
        },
        "Tier 3": {
            "weight": 0.75,
            "competitions": [
                "UEFA Euro",
                "Copa América",
                "African Cup of Nations",
                "AFC Asian Cup",
                "Gold Cup",
                "Oceania Nations Cup"
            ]
        },

        "Tier 4": {
            "weight": 0.60,
            "competitions": [
                "CONMEBOL–UEFA Cup of Champions",
                "UEFA Euro qualification",
                "Copa América qualification",
                "African Cup of Nations qualification",
                "AFC Asian Cup qualification",
                "Gold Cup qualification",
                "Oceania Nations Cup qualification",
                "UEFA Nations League",
                "CONCACAF Nations League",
                "Confederations Cup"
            ]
        },

        "Tier 5": {
            "weight": 0.45,
            "competitions": [
                "AFF Championship",
                "AFC Challenge Cup",
                "ASEAN Championship",
                "EAFF Championship",
                "WAFF Championship",
                "Gulf Cup",
                "CAFA Nations Cup",
                "CECAFA Cup",
                "COSAFA Cup",
                "CFU Caribbean Cup",
                "SAFF Cup",
                "Pacific Games",
                "Melanesia Cup",
                "Nations Cup",
                "UNCAF Cup",
                "Baltic Cup",
                "CONCACAF Nations League qualification",
            ]
        },
        "Tier 6": {
            "weight": 0.30,
            "competitions": [
                "AFF Championship qualification",
                "EAFF Championship qualification",
                "AFC Challenge Cup qualification",
                "ASEAN Championship qualification",
                "COSAFA Cup qualification",
                "Friendly",
                "FIFA Series",
                "Kirin Cup",
                "Kirin Challenge Cup",
                "King's Cup",
                "King Hassan II Tournament",
                "Jordan International Tournament",
                "Cyprus International Tournament",
                'CFU Caribbean Cup qualification',
                "OSN Cup",
                "VFF Cup",
                "Three Nations Cup",
                "Tri Nation Tournament",
                "Tri-Nations Cup",
                "Tri-Nations Series",
                "Prime Minister's Cup",
                "United Arab Emirates Friendship Tournament",
                "Unity Cup",
                "USA Cup",
                "World Unity Cup"
            ]
        },

        "Tier 7": {
            "weight": 0.10,
            "competitions": [
                "ABCS Tournament",
                "Al Ain International Cup",
                "Amílcar Cabral Cup",
                "Arab Cup",
                "Arab Cup qualification",
                "Afro-Asian Games",
                "Atlantic Heritage Cup",
                "Benedikt Fontana Cup",
                "Canadian Shield",
                "CONCACAF Series",
                "Copa Confraternidad",
                "Copa Paz del Chaco",
                "Copa del Pacífico",
                "Corsica Cup",
                "Coupe de l'Outre-Mer",
                "Cup of Ancient Civilizations",
                "Diamond Jubilee International Football Tournament",
                "Dragon Cup",
                "East Asian Games",
                "Hungary Heritage Cup",
                "Indian Ocean Island Games",
                "Inter Games",
                "Island Games",
                "Malta International Tournament",
                "MSG Prime Minister's Cup",
                "Mahinda Rajapaksa Cup",
                "Mapinduzi Cup",
                "Marianas Cup",
                "Mauritius Four Nations Cup",
                "Merdeka Tournament",
                "Millennium Cup",
                "Morocco, Capital of African Football",
                "Mukuru 4 Nations",
                "Muratti Vase",
                "Navruz Cup",
                "Nehru Cup",
                "Niamh Challenge Cup",
                "Nile Basin Tournament",
                "Outrigger Challenge Cup",
                "Palestine International Championship",
                "Philippine Peace Cup",
                "SKN Football Festival",
                "Soccer Ashes",
                "South Asian Super Cup",
                "South Pacific Games",
                "Superclásico de las Américas",
                "TIFOCO Tournament",
                "The Other Final",
                "Tynwald Hill Tournament",
                "Windward Islands Tournament"
            ]
        },

        "Excluded": {
            "weight": 0.0,
            "competitions": [
                "CONIFA Africa Football Cup",
                "CONIFA Asia Cup",
                "CONIFA European Football Cup",
                "CONIFA South America Football Cup",
                "CONIFA World Football Cup",
                "CONIFA World Football Cup qualification",
                "CONIFA World Cup qualification",
                "ConIFA Challenger Cup",
                "ELF Cup",
                "FIFI Wild Cup",
                "Viva World Cup",
                "Pacific Mini Games",
                "Nordic Championship",
                "Lunar New Year Cup",
                "AFC Solidarity Cup",
                "AFC",
                'International Tournament of Peoples, Cultures and Tribes',
                "Intercontinental Cup"
            ]
        }
    }

    """def get_tournament_weight(tournament_name):
        x= competition_weights.values()
        for i in x:
            for j in i.get("competitions"):
                if j==tournament_name:
                    return i.get("weight")
        return 0 """


    flat_comp_weights = flatten(competition_weights)

    def get_tournament_weight(tournament_name):
        return flat_comp_weights.get(tournament_name)

    df['comp_weights'] = df['tournament'].map(get_tournament_weight)

    x = pd.concat([df['home_team'], df['away_team']])
    u_teams = x.unique()

    try:
        con=get_connection()
        cursor = con.cursor()
        print("Connected to DB")
        team_list = [[str(team,)] for  team in u_teams]
        insert_query = "INSERT INTO teams (name) VALUES(%s) ON CONFLICT (name) DO NOTHING"
        cursor.executemany(insert_query, team_list)
        con.commit()
        print("Inserted all teams")
        team_id_map = get_team_ids(cursor)
        df['home_team_id'] = df['home_team'].map(team_id_map)
        df['away_team_id'] = df['away_team'].map(team_id_map)
        insert_query = "INSERT into matches(home_team_id, away_team_id, date, home_score, away_score, tournament, tournament_weight, neutral) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        df = df[['home_team_id', 'away_team_id', 'date', 'home_score', 'away_score', 'tournament', 'comp_weights', 'neutral']]
        match_list=[]
        for i in df.values:
            match_list.append([i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7],])
        cursor.executemany(insert_query,match_list)
        print("Inserted all teams into matches")
        con.commit()
        cursor.close()
        con.close()
    except Exception as e:
        print(f"Error: {e}")
        return
    sql_ranking()




setup()




