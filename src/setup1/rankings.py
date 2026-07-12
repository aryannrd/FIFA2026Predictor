from datetime import date
today = date.today()
import requests
from db import get_connection, get_team_ids

def get_rankings():
    url = "https://api.fifa.com/api/v3/fifarankings/rankings/live?gender=1&sportType=0&language=en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://inside.fifa.com/",
        "Origin": "https://inside.fifa.com",
    }
    r = requests.get(url, headers=headers)
    return r

def create_rankings():
    r = get_rankings()
    rankings_dict={}
    for i in r.json()['Results']:
        rankings_dict[i['TeamName'][0]['Description']]={'ConfederationName': i['ConfederationName'], 'Rank': i['Rank'], 'PrevRank': i['PrevRank'], 'TotalPoints': i['TotalPoints'], 'PrevPoints': i['PrevPoints'], 'Date': today}
    return rankings_dict

def sql_ranking():
    rankings_dict = create_rankings()
    #adding content from rankings to the rankings table in the postgres DB
    fifa_clarifying_map = {
        'USA': 'United States',
        'Türkiye': 'Turkey',
        'IR Iran' : 'Iran',
        'Congo DR': 'DR Congo',
        'Czechia': 'Czech Republic',
        'Côte d\'Ivoire': 'Ivory Coast',
        'Korea Republic': 'South Korea',
        'Cabo Verde': 'Cape Verde',
        'Kyrgyz Republic': 'Kyrgyzstan',
        'The Gambia': 'Gambia',
        'DPR Korea': 'North Korea',
        'St. Kitts and Nevis': 'Saint Kitts and Nevis',
        'St. Lucia': 'Saint Lucia',
        'St. Vincent / Grenadines': 'Saint Vincent and the Grenadines',
        'US Virgin Islands': 'United States Virgin Islands',
        'China PR': 'China'
    }

    corrected_rankings = {}
    for name, data in rankings_dict.items():
        corrected_name = fifa_clarifying_map.get(name, name)
        corrected_rankings[corrected_name] = data
    con=get_connection()
    cursor= con.cursor()
    team_id_map=get_team_ids(cursor)
    insert_query= 'INSERT INTO rankings(team_id, ranking_date,rank,points,prev_rank,prev_points) VALUES (%s, %s,%s,%s,%s,%s)'
    update_query='UPDATE teams SET region=%s where id= %s'
    ranking_list=[]
    region_list=[]
    for name, data in corrected_rankings.items():
        team_id = team_id_map.get(name)
        if team_id is None:
            continue
        ranking_list.append([
            team_id,
            data['Date'],
            data['Rank'],
            data['TotalPoints'],
            data['PrevRank'],
            data['PrevPoints']
        ])
        region_list.append([data['ConfederationName'],team_id])
    cursor.executemany(insert_query,ranking_list)
    con.commit()
    cursor.executemany(update_query,region_list)
    con.commit()
    print(f"Inserted rankings")
    cursor.close()
    con.close()




