import os
from src.models.predict import predict
from src.setup1.setup import setup
from datetime import date, datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPDATE_FILE = os.path.join(BASE_DIR, "last_setup.txt")

def should_run_setup():
    today = date.today()
    if not os.path.exists(UPDATE_FILE):
        return True
    with open(UPDATE_FILE, "r") as f:
        last_setup = date.fromisoformat(f.read())
    return (today - last_setup) > timedelta(days=30)

def update_setup_date():
    with open(UPDATE_FILE, "w") as f:
        f.write(str(date.today()))

def main():
    if should_run_setup():
        try:
            setup()
            update_setup_date()
            print("Updated data and model!")
        except Exception as e:
            print("Setup failed:", e)

    while True:
        print("Starting Prediction Pipeline")
        team1 = input("Enter team 1 id: ")
        if team1.lower() == "q":
            break
        try:
            team1 = int(team1)
        except ValueError:
            print("Invalid")
            continue
        team2 = input("Enter team 2 id: ")
        try:
            team2 = int(team2)
        except ValueError:
            print("Invalid")
            continue

        try:
            print(predict(int(team1), int(team2), True, 1.0))
        except Exception as e:
            print("Prediction failed:", e)


if __name__ == "__main__":
    main()