import os
from dotenv import load_dotenv
import requests

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

if not API_KEY:
    raise ValueError("FRED_API_KEY not found in environment. Create a .env file with your key!")

# Example FRED series IDs
SERIES = ["GDP", "CPIAUCSL"]

for series_id in SERIES:
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json"
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        # Print the first observation as proof
        first_obs = data["observations"][0]
        print(f"{series_id} first observation:")
        print(first_obs)
    else:
        print(f"Failed to fetch {series_id}: {response.status_code} - {response.text}")
