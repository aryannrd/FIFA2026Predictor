#form = SUM(result × tournament_weight) / SUM(tournament_weight)
from src.setup1.db import get_connection
def calculate_form():
    con = get_connection()
    cursor = con.cursor()
    form_query = ("""WITH team_timelines AS (
    SELECT id, date, home_team_id AS team_id,
         CASE 
               WHEN result = 2 THEN 1
               WHEN result = 0 THEN 0 
               ELSE 0.5                   
           END as result, tournament_weight
    FROM matches
    UNION ALL
    SELECT id,date, away_team_id AS team_id,CASE 
               WHEN result = 2 THEN 0
               WHEN result = 0 THEN 1 
               ELSE 0.5 
               END AS result, tournament_weight
    FROM matches)
    
    SELECT id, date, team_id, SUM(result * tournament_weight) OVER (
        PARTITION BY team_id
        ORDER BY date ASC
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        )
    /
    NULLIF(SUM(tournament_weight) OVER(
    PARTITION BY team_id
    ORDER BY date ASC
    ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ),0) AS form_score        
    FROM team_timelines;""") #first part of query creates a temporary object with all the data we require, generalizing home and away id to team_d
    #second part of query uses the form formula over 5 rows of data, partitioning by team id, allowing us to track a particular team and ordering by date
    cursor.execute(form_query)
    rows = cursor.fetchall()
    new_rows={}
    for row in rows:
        match_id = row[0]
        team_id = row[2]
        form_score = row[3]
        if match_id not in new_rows:
            new_rows[match_id] = {}
        new_rows[match_id][team_id] = float(form_score) if form_score is not None else 0.5 #if its first game, defaulting to 0.5
    cursor.close()
    con.close()
    return new_rows


def populate_form():
    con = get_connection()
    cursor = con.cursor()
    form = calculate_form()
    cursor.execute("SELECT match_id, home_team_id, away_team_id FROM match_features")
    rows = cursor.fetchall()

    update_query = "UPDATE match_features SET home_form=%s, away_form=%s WHERE match_id=%s"
    update_list = []
    for row in rows:
        match_id = row[0]
        home_team_id = row[1]
        away_team_id = row[2]
        match_teams_form = form.get(match_id, {})
        home_form = match_teams_form.get(home_team_id, 0.5)
        away_form = match_teams_form.get(away_team_id, 0.5)
        update_list.append((home_form, away_form, match_id,))

    cursor.executemany(update_query, update_list)
    con.commit()
    cursor.close()
    con.close()
    return

populate_form()
