import requests
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("FDA_API_KEY")
if not api_key:
    raise ValueError("API key not found")

url = "https://api-datadashboard.fda.gov/v1/inspections_classifications"  # actual endpoint from docs

headers = {
    "Authorization-User": "sniez@uvm.edu",
    "Authorization-Key": api_key
}

# Minimal payload
payload = {
    "filters": {},
    "sort": "",
    "sortorder": "",
    "columns": []
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    print("API key works! Response:")
    print(response.json())
else:
    print(f"Request failed with status {response.status_code}")
    print(response.text)
