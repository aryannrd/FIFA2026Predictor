import psycopg2
def get_connection():
    con = psycopg2.connect(dbname="fifa", user="postgres", password="yourpassword", host='localhost', port="5432")
    return con

def get_team_ids(cursor):
    query = "SELECT id, name FROM teams;"
    cursor.execute(query)
    rows = cursor.fetchall()
    team_dict = {}
    for i in rows:
        team_dict[i[1]] = i[0]
    return team_dict

def get_ranking_map(cursor):
    ranking_query = "SELECT team_id, rank FROM rankings;"
    cursor.execute(ranking_query)
    rows = cursor.fetchall()
    ranking_dict={}
    for i in rows:
        ranking_dict[i[0]] = i[1]
    return ranking_dict


def get_current_form(cursor):
    info_query = """
    WITH recent_matches AS (
        SELECT team_id, result_scaled, tournament_weight,
               ROW_NUMBER() OVER (PARTITION BY team_id ORDER BY date DESC) as rn
        FROM (
            SELECT home_team_id as team_id,
                   CASE WHEN result = 2 THEN 1.0 
                        WHEN result = 0 THEN 0.0 
                        ELSE 0.5 END as result_scaled,
                   tournament_weight, date FROM matches
            UNION ALL
            SELECT away_team_id as team_id,
                   CASE WHEN result = 2 THEN 0.0 
                        WHEN result = 0 THEN 1.0 
                        ELSE 0.5 END as result_scaled,
                   tournament_weight, date FROM matches
        ) as all_matches
    )
    SELECT team_id, 
           SUM(result_scaled * tournament_weight) / NULLIF(SUM(tournament_weight), 0) as current_form
    FROM recent_matches
    WHERE rn <= 10
    GROUP BY team_id
    """
    cursor.execute(info_query)
    rows = cursor.fetchall()
    form_dict = {}
    for row in rows:
        if row[1] is not None:
            form_dict[row[0]] = float(row[1])
    return form_dict

def get_current_draw_rates(cursor):
    query = """
    WITH team_matches AS (
        SELECT home_team_id as team_id,
               (home_score = away_score)::int AS is_draw,
               date FROM matches
        UNION ALL
        SELECT away_team_id as team_id,
               (home_score = away_score)::int AS is_draw,
               date FROM matches
    ),
    recent AS (
        SELECT team_id, is_draw,
               ROW_NUMBER() OVER (PARTITION BY team_id ORDER BY date DESC) as rn
        FROM team_matches
    )
    SELECT team_id, AVG(is_draw::float) as draw_rate
    FROM recent
    WHERE rn <= 20
    GROUP BY team_id
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    return {row[0]: float(row[1]) if row[1] is not None else 0.24
            for row in rows}