import requests
import json
import logging


# Exercise 2.2
# Make your first API call to get a random cat fact

logging.basicConfig(
    level=logging.INFO,
    format="{asctime} - {levelname} - {message}",
    style="{",
    filename='cat_facts.log',
    filemode="w"
)

def get_cat_fact():
    url = "https://catfact.ninja/fact"

    try:

        # Send GET request to the API
        response = requests.get(url)

        # Check if request was successful
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            logging.info(f"Response successful: {data['fact']}")
            return data['fact']
        else:
            print(f"Error: {response.status_code}")
            logging.error(f"Error: {response.status_code}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        logging.exception(f"An error occurred: {e}")
        return None


# Test your function
cat_facts = [] # empty list to store cat facts
for i in range(5):
    cat_fact = get_cat_fact()
    print(f"Cat fact: {cat_fact}")

# dump cat facts to a json file
with open("cat_facts.json", "w") as f:
    json.dump(cat_facts, f, indent=2)
logging.info("Successfully saved cat facts to file")



