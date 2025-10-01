import requests
import json
import logging

# Exercise 2.3
def get_public_holidays(country_code="US", year=2024):
    """
    Get public holidays for a specific country and year
    Uses Nager.Date API (free, no key required)
    """
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for bad status codes

        holidays = response.json()
        return holidays

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


# Test with different countries
countries = ['RU', 'ES', 'GB']
summary = {} # empty dictionary for json summary

for country in countries:
    holidays = get_public_holidays(country)
    if holidays:
        summary[country] = len(holidays)
        for holiday in holidays:
            print(f'{holiday['date']}: {holiday['localName']}')
    else:
        summary[country] = 0

with open("country_holiday_summary.json", "w") as f:
    json.dump(summary, f, indent=2)