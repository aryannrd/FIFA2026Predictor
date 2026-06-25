#
from datetime import date
today = date.today()
import requests
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


def create_ranking():
    r = get_rankings()
    rankings_dict={}
    for i in r.json()['Results']:
        rankings_dict[i['TeamName'][0]['Description']]={'ConfederationName': i['ConfederationName'], 'Rank': i['Rank'], 'PrevRank': i['PrevRank'], 'TotalPoints': i['TotalPoints'], 'PrevPoints': i['PrevPoints'], 'Date': today}
    return rankings_dict

def sql_ranking():
    rankings = create_ranking()
    #adding content from rankings to the rankings table in the postgres DB
