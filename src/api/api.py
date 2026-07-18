from fastapi import FastAPI, HTTPException
from src.api.api_helper import get_all_teams, get_team_info
from src.setup1.db import get_connection, get_team_ids
from src.api.startup import initialize,state
from pydantic import BaseModel
from src.models.predict import predict


class PredictRequest(BaseModel):
    team1: str
    team2: str
    neutral: bool
    tournament: str = "FIFA World Cup"
app = FastAPI()
@app.on_event("startup")
def startup():
    initialize()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/teams")
def get_teams():
    teams_list = get_all_teams()
    return teams_list

@app.get("/teams/{team_id}")
def get_team(team_id: int):
    con= get_connection()
    cursor = con.cursor()
    team_info = get_team_info(cursor,team_id)
    if team_info is None:
        cursor.close()
        con.close()
        raise HTTPException(status_code=404, detail="Team not found")
    cursor.close()
    con.close()
    teams_list = get_all_teams()
    for i in teams_list:
        if i["id"] == team_id:
            team_name = i["name"]
            break

    team_dict = {"id": team_info[0], "name": team_name,"elo": team_info[1], "rank": team_info[2], "xG": team_info[3], "form": team_info[4]}

    return team_dict

@app.post("/predict")
def predict_match(request: PredictRequest):
    teams_info = state['team_id_map']
    flat_comp_weights = state['flat_comp_weights']
    id1 = teams_info.get(request.team1)
    id2 = teams_info.get(request.team2)
    if id1 is None or id2 is None:
        raise HTTPException(status_code=404, detail="Team not found")
    tournament_weight = flat_comp_weights.get(request.tournament, 0.6)
    final_prob = predict(id1, id2, request.neutral, tournament_weight)
    return final_prob