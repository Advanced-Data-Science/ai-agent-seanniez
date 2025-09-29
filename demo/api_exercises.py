import requests
import json
import logging
from time import sleep

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="cat_facts.log",
    filemode="w"
)


def get_cat_fact():
    url = "https://catfact.ninja/fact"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raises HTTPError for bad responses

        data = response.json()
        fact = data.get("fact")

        if not fact:
            logging.warning("No fact found in API response.")
            return None
        return fact

    except requests.exceptions.Timeout:
        logging.error("Request timed out.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON response.")

    return None


def get_multiple_cat_facts(n=5, max_retries=3):
    facts = []
    attempts = 0

    while len(facts) < n and attempts < n * max_retries:
        fact = get_cat_fact()
        if fact and fact not in facts:  # avoid duplicates
            facts.append(fact)
            logging.info(f"Retrieved fact: {fact}")
        else:
            logging.warning("Duplicate or invalid fact received.")
        attempts += 1
        sleep(1)  # be kind to the API
    return facts


def save_to_json(data, filename="cat_facts.json"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Saved {len(data)} facts to {filename}")
    except Exception as e:
        logging.error(f"Failed to save data to {filename}: {e}")


if __name__ == "__main__":
    cat_facts = get_multiple_cat_facts(5)
    if cat_facts:
        save_to_json(cat_facts)
        print("Cat facts successfully retrieved and saved!")
    else:
        print("Failed to retrieve cat facts. Check logs for details.")
