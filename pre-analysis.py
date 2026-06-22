import kagglehub
import os
import pandas as pd

path = kagglehub.dataset_download("martj42/international-football-results-from-1872-to-2017")

print("Path to dataset files:", path)
csv_path = os.path.join(path, 'results.csv')
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    print("\nSuccess! Here is the data:")
    print(df.head())
else:
    print(f"\nError: Could not find results.csv in the downloaded files.")

df = df.dropna(subset=['home_score', 'away_score'])
df['date'] = pd.to_datetime(df['date'])
x = df[df['date'] >  '2000-01-01']

df.info()
for t in sorted(x['tournament'].unique()):
    print(t)


competition_weights = {
    "Tier 1": {
        "weight": 1.00,
        "competitions": [
            "FIFA World Cup"
        ]
    },
    "Tier 2": {
        "weight": 0.90,
        "competitions": [
            "FIFA World Cup qualification"
        ]
    },
    "Tier 3": {
        "weight": 0.75,
        "competitions": [
            "UEFA Euro",
            "Copa América",
            "African Cup of Nations",
            "AFC Asian Cup",
            "Gold Cup",
            "Oceania Nations Cup"
        ]
    },

    "Tier 4": {
        "weight": 0.60,
        "competitions": [
            "CONMEBOL–UEFA Cup of Champions",
            "UEFA Euro qualification",
            "Copa América qualification",
            "African Cup of Nations qualification",
            "AFC Asian Cup qualification",
            "Gold Cup qualification",
            "Oceania Nations Cup qualification",
            "UEFA Nations League",
            "CONCACAF Nations League",
            "Confederations Cup"
        ]
    },

    "Tier 5": {
        "weight": 0.45,
        "competitions": [
            "AFF Championship",
            "AFC Challenge Cup",
            "ASEAN Championship",
            "EAFF Championship",
            "WAFF Championship",
            "Gulf Cup",
            "CAFA Nations Cup",
            "CECAFA Cup",
            "COSAFA Cup",
            "CFU Caribbean Cup",
            "SAFF Cup",
            "Pacific Games",
            "Melanesia Cup",
            "Nations Cup",
            "UNCAF Cup",
            "Baltic Cup",
            "CONCACAF Nations League qualification",
        ]
    },
    "Tier 6": {
        "weight": 0.30,
        "competitions": [
            "AFF Championship qualification",
            "EAFF Championship qualification",
            "AFC Challenge Cup qualification",
            "ASEAN Championship qualification",
            "COSAFA Cup qualification",
            "Friendly",
            "FIFA Series",
            "Kirin Cup",
            "Kirin Challenge Cup",
            "King's Cup",
            "King Hassan II Tournament",
            "Jordan International Tournament",
            "Cyprus International Tournament",
            'CFU Caribbean Cup qualification',
            "Malta International Tournament",
            "OSN Cup",
            "VFF Cup",
            "Three Nations Cup",
            "Tri Nation Tournament",
            "Tri-Nations Cup",
            "Tri-Nations Series",
            "Prime Minister's Cup",
            "United Arab Emirates Friendship Tournament",
            "Unity Cup",
            "USA Cup",
            "World Unity Cup"
        ]
    },

    "Tier 7": {
        "weight": 0.10,
        "competitions": [
            "ABCS Tournament",
            "Al Ain International Cup",
            "Amílcar Cabral Cup",
            "Arab Cup",
            "Arab Cup qualification",
            "Afro-Asian Games",
            "Atlantic Heritage Cup",
            "Benedikt Fontana Cup",
            "Canadian Shield",
            "CONCACAF Series",
            "Copa Confraternidad",
            "Copa Paz del Chaco",
            "Copa del Pacífico",
            "Corsica Cup",
            "Coupe de l'Outre-Mer",
            "Cup of Ancient Civilizations",
            "Diamond Jubilee International Football Tournament",
            "Dragon Cup",
            "East Asian Games",
            "Hungary Heritage Cup",
            "Indian Ocean Island Games",
            "Inter Games",
            "Island Games",
            "Malta International Tournament",
            "MSG Prime Minister's Cup",
            "Mahinda Rajapaksa Cup",
            "Mapinduzi Cup",
            "Marianas Cup",
            "Mauritius Four Nations Cup",
            "Merdeka Tournament",
            "Millennium Cup",
            "Morocco, Capital of African Football",
            "Mukuru 4 Nations",
            "Muratti Vase",
            "Navruz Cup",
            "Nehru Cup",
            "Niamh Challenge Cup",
            "Nile Basin Tournament",
            "Outrigger Challenge Cup",
            "Palestine International Championship",
            "Philippine Peace Cup",
            "SKN Football Festival",
            "Soccer Ashes",
            "South Asian Super Cup",
            "South Pacific Games",
            "Superclásico de las Américas",
            "TIFOCO Tournament",
            "The Other Final",
            "Tynwald Hill Tournament",
            "Windward Islands Tournament"
        ]
    },

    "Excluded": {
        "weight": 0.0,
        "competitions": [
            "CONIFA Africa Football Cup",
            "CONIFA Asia Cup",
            "CONIFA European Football Cup",
            "CONIFA South America Football Cup",
            "CONIFA World Football Cup",
            "CONIFA World Football Cup qualification",
            "CONIFA World Cup qualification",
            "ConIFA Challenger Cup",
            "ELF Cup",
            "FIFI Wild Cup",
            "Viva World Cup",
            "Pacific Mini Games",
            "Nordic Championship",
            "Lunar New Year Cup",
            "AFC Solidarity Cup",
            "AFC",
            'International Tournament of Peoples, Cultures and Tribes',
            "Intercontinental Cup"
        ]
    }
}

