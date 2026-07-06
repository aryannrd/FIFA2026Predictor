import psycopg2
def get_connection():
    con = psycopg2.connect(dbname="fifa", user="postgres", password="yourpassword", host='localhost', port="5432")
    print("Connected to DB")
    return con

def get_team_ids(cursor):
    query = "SELECT id, name FROM teams;"
    cursor.execute(query)
    rows = cursor.fetchall()
    team_dict = {}
    for i in rows:
        team_dict[i[1]] = i[0]
    return team_dict

