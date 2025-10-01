import requests
import os
from dotenv import load_dotenv

load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
ALPHA_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# test FRED API

fred_request = requests.get(
    "https://api.stlouisfed.org/fred/series/observations",
    params={
        "series_id":"GDP",
        "api_key":FRED_API_KEY,
        "file_type": "json",
        "observation_start":"2020-01-01",
        "observation_end":"2024-12-25"
    }
)

print(f"FRED key test: {fred_request.status_code == 200}") # if status code is 200, then they key is valid

alpha_request = requests.get(
    "https://www.alphavantage.co/query",
    params = {
        "function":"TIME_SERIES_DAILY",
        "symbol":"MSFT",
        "apikey":ALPHA_API_KEY,
        "outputsize":"compact"
    }
)

print(f"Alpha Vantage key test: {alpha_request.status_code == 200}")
