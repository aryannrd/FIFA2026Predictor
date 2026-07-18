from src.setup1.db import get_connection

def get_all_teams():
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("SELECT id, name FROM teams;")
    rows = cursor.fetchall()
    teams_list =[]
    for i in rows:
        temp_dict = {"id": i[0], "name": i[1]}
        teams_list.append(temp_dict)
    cursor.close()
    con.close()
    return teams_list

def get_team_info(cursor, team_id):
    query = """
    WITH team_matches AS (
        SELECT mf.home_team_id AS team_id, mf.home_elo AS elo , mf.home_rank AS rank,
        mf.home_xg AS xG, mf.home_form AS form ,m.date 
        FROM match_features AS mf
        INNER JOIN matches AS m
        ON mf.match_id = m.id
        UNION ALL
        SELECT mf.away_team_id AS team_id, mf.away_elo AS elo, mf.away_rank AS rank, mf.away_xg AS xG, mf.away_form AS form, m.date 
        FROM match_features AS mf
        INNER JOIN matches AS m
        ON mf.match_id = m.id
    ),
    recent AS (
        SELECT team_id, elo, rank, xG, form,
               ROW_NUMBER() OVER (PARTITION BY team_id ORDER BY date DESC) as rn
        FROM team_matches
    )
    SELECT team_id, elo, rank, xG, form
    FROM recent
    WHERE rn <= 1 AND team_id = %s;
    """
    cursor.execute(query,(team_id,))
    row = cursor.fetchone()
    return row