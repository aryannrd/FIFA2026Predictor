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