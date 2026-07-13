import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from src.setup1.db import get_connection
def parse_market_value(value):
    if value is None:
        return None
    value = value.replace("€", "").strip()
    if "bn" in value:
        return int(float(value.replace("bn", "")) * 1_000_000_000)

    elif "m" in value:
        return int(float(value.replace("m", "")) * 1_000_000)
    return None

def market_value():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    all_teams = []
    for page in range(1, 10):
        url = f"https://www.transfermarkt.com/marktwertetop/wertvollstenationalmannschaften?page={page}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="items")
        if not table:
            print("No table found on page", page)
            break
        rows = table.find_all("tr", class_=["odd", "even"])
        if len(rows) == 0:
            print("No teams on page", page)
            break
        for row in rows:
            cols = row.find_all("td")
            if len(cols) > 0:
                country = cols[1].get_text(" ", strip=True)
                value = None
                for col in cols:
                    text = col.get_text(" ", strip=True)
                    if "€" in text:
                        value = text
                        break
                all_teams.append({
                    "country": country,
                    "market_value": value
                })
        print(f"Finished page {page}")
        time.sleep(3)

    df = pd.DataFrame(all_teams)
    df = df.dropna(subset=["market_value"])
    df["market_value_eur"] = df["market_value"].apply(parse_market_value)
    return df


def mapping_values():
    values = market_value()
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("SELECT id, name FROM teams")
    data = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    teams_df = pd.DataFrame(data, columns=columns)

    team_mapping = dict(zip(teams_df['name'], teams_df['id']))
    values['team_id'] = values['country'].map(team_mapping)
    values = values.dropna(subset=['team_id'])
    values['team_id'] = values['team_id'].astype(int)
    cursor.close()
    con.close()
    return values

