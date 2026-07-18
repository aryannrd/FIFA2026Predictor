from datetime import datetime, timedelta
from src.api.config import LAST_UPDATE_FILE
from src.setup1.db import get_team_ids, get_connection
from src.setup1.setup import setup
from src.setup1.setup import flatten
from src.setup1.setup import competition_weights
state = {}

def initialize():
    con = get_connection()
    cursor = con.cursor()
    state['team_id_map'] = get_team_ids(cursor)
    flat_comp_weights = flatten(competition_weights)
    state['flat_comp_weights'] = flat_comp_weights
    cursor.close()
    con.close()
    if needs_update():
        print("Data is older than 30 days. Running update pipeline...")
        setup()
        save_update_time()


def needs_update() -> bool:
    if not LAST_UPDATE_FILE.exists():
        return True
    with LAST_UPDATE_FILE.open("r") as f:
        last_update = datetime.fromisoformat(f.read().strip())
    return datetime.now() - last_update > timedelta(days=30)


def save_update_time():
    LAST_UPDATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LAST_UPDATE_FILE.open("w") as f:
        f.write(datetime.now().isoformat())