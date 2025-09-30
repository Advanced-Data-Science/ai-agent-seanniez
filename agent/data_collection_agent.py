import requests
import json
import time
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging

class DataCollectionAgent:
    def __init__(self, config_file):
        # Load configuration
        self.config = self.load_config(config_file)
        load_dotenv()
        fred_key = os.getenv("FRED_API_KEY") # fetch the API key from .env instead of the dummy key in the config file
        if fred_key:
            self.config["FRED_API_KEY"] = fred_key # overwrite the dummy key in memory

        alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if alpha_key:
            self.config["ALPHA_VANTAGE_API_KEY"] = alpha_key

        # information from https://docs.python.org/3/library/logging.html
        # and https://stackoverflow.com/questions/28330317/print-timestamp-for-logging-in-python
        logging.basicConfig(
            filename="logs/collection.log",
            level=logging.INFO,
            format='%(asctime)s %(levelname)-8s %(message)s'
        )

        # Initialize data storage and stats
        self.data_store = {}
        self.collection_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }
        self.delay_multiplier = 1.0

    # configuration management
    # information for working with json files found here https://www.geeksforgeeks.org/python/read-write-and-parse-json-using-python/
    def load_config(self, config_file):
        if not os.path.exists(config_file): # handle case where config file is not found
            raise FileNotFoundError(f"Config file {config_file} not found")
        with open(config_file, "r") as f:
            return json.load(f) # convert to a dictionary

    # intelligent collection strategy
    def collect_data(self):
        api_map = self.config.get("SERIES_API_MAPPING", {}) # to determine which symbols come from which API

        fred_url = "https://api.stlouisfed.org/fred/series/observations"
        fred_api_key = self.config.get("FRED_API_KEY") # fetch FRED API key from memory

        alpha_url = "https://www.alphavantage.co/query"
        alpha_api_key = self.config.get("ALPHA_VANTAGE_API_KEY") # fetch alpha API key from memory

        start_date = self.config.get("START_DATE")
        end_date = self.config.get("END_DATE")
        frequency = self.config.get("FRED_FREQUENCY", "d") # daily frequency

        raw_data = {} # empty dictionary to store the raw data

        for series, api_name in api_map.items():
            if api_name == "FRED":
                params = {
                    "series_id": series,
                    "api_key": fred_api_key,
                    "file_type": "json",
                    "observation_start": start_date,
                    "observation_end": end_date
                }
                raw_data[series] = self.make_fred_request(fred_url, params) # pull data for FRED symbols

            elif api_name == "ALPHA":
                params = {
                    "function": "TIME_SERIES_DAILY",
                    "symbol": series,
                    "apikey": alpha_api_key,
                    "outputsize": "compact"
                }
                raw_data[series] = self.make_alpha_request(alpha_url, params) # pull data for Alpha Vantage symbols

            self.respectful_delay()  # rate limiting

        processed = self.process_data(raw_data)
        self.store_data(processed, raw_data=raw_data)
        self.adjust_strategy()

    # data quality assessment
    def assess_data_quality(self):
        """Evaluate the quality of collected data"""
        if not self.data_store:
            return 0

        quality_metrics = {
            'completeness': self.check_completeness(),
            # 'accuracy': self.check_accuracy(),
            # 'consistency': self.check_consistency(),
            # 'timeliness': self.check_timeliness()
        }

        # Calculate overall quality score
        return sum(quality_metrics.values()) / len(quality_metrics)

    # adaptive strategy
    def adjust_strategy(self):
        """Modify collection approach based on performance"""
        success_rate = self.get_success_rate()

        if success_rate < 0.5:
            # Increase delays, try alternative APIs
            self.delay_multiplier *= 2
            # self.try_fallback_api()
        elif success_rate > 0.9:
            # Can be more aggressive
            self.delay_multiplier *= 0.8

    # respectful collection
    def respectful_delay(self):
        """Implement respectful rate limiting"""
        base_delay = self.config.get('base_delay', 1.0)
        delay = base_delay * self.delay_multiplier

        # Add random jitter to avoid thundering herd
        jitter = random.uniform(0.5, 1.5)
        time.sleep(delay * jitter)

    def make_fred_request(self, url, params):
        # helpful information for using the requests library from https://www.geeksforgeeks.org/python/response-json-python-requests/
        # and here https://www.w3schools.com/python/ref_requests_get.asp
        self.collection_stats["total_requests"] += 1 # increment total_requests accumulator

        try:
            response = requests.get(url, params=params) # API response in accordance to parameters
            response.raise_for_status() # raise exception for bad status codes
            self.collection_stats["successful_requests"] += 1 # increment successful requests
            return response.json() # parse the response as a json.
        except Exception as e:
            self.collection_stats["failed_requests"] += 1 # increment failed_requests if exception occurs
            print(f"Request failed for params={params}: {e}")
            return None

    def make_alpha_request(self, url, params):
        self.collection_stats["total_requests"] += 1
        try:
            response = requests.get(url, params=params) # API response in accordance to parameters
            response.raise_for_status() # raise exception for bad status codes
            self.collection_stats["successful_requests"] += 1 # increment successful requests
            return response.json() # parse the response as a json.
        except Exception as e:
            self.collection_stats["failed_requests"] += 1 # increment failed_requests if exception occurs
            print(f"Request failed for params={params}: {e}")
            return None

    # standardize numbers and missing entries and store as a dictionary
    def process_data(self, raw_data):
        processed = {} # empty dictionary
        last_month = datetime.today() - timedelta(days=30) # get previous 30 days for alpha vantage

        for series, data in raw_data.items():
            processed[series] = [] # list to hold the data for each series

            # FRED
            if "observations" in data:
                for observation in data["observations"]:
                    try:
                        value = float(observation["value"])
                    except:
                        value = None
                    processed[series].append({"date": observation["date"], "value": value})

            # Alpha Vantage
            elif "Time Series (Daily)" in data:
                for date_str, values in data["Time Series (Daily)"].items():
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if date >= last_month: # most recent data
                        try:
                            close_price = float(values["4. close"])
                        except:
                            close_price = None
                        processed[series].append({"date": date_str, "value": close_price})

        return processed

    def store_data(self, processed, raw_data):
        # store raw data

        for series, data in raw_data.items():
            path = f"../data/raw/{series}_raw.json" # store raw data
            with open(path, "w") as f:
                json.dump(data, f, indent=2)

        # store processed data
        for series, observations in processed.items():
            path = f"../data/processed/{series}_processed.json" # store in the processed data folder
            with open(path, "w") as f:
                json.dump(observations, f, indent=2)

        # store processed data in memory for further processing
        for series, observations in processed.items():
            if series not in self.data_store:
                self.data_store[series] = [] # store in the original data structure declared at the top of the class
            self.data_store[series].extend(observations) # use .extend() rather than .append() since we are dealing with lists of items


    def get_success_rate(self):
        total = self.collection_stats["total_requests"]
        return self.collection_stats["successful_requests"] / total # ratio of successful requests to total requests

    def check_completeness(self):
        completeness_scores = {} # dictionary to store completeness scores

        for series, observations in self.data_store.items():
            if not observations: # if no observations are found for a particular series
                completeness_scores[series] = 0 # return 0 for completeness
                continue

            total = len(observations) # total requests
            non_missing = sum(1 for obs in observations if obs["value"] is not None) # actual observations
            completeness_scores[series] = non_missing / total # ratio of observations to total

        # average across series to give us a single score
        if completeness_scores:
            avg_completeness = sum(completeness_scores.values()) / len(completeness_scores) # take the average across the series'
        else:
            avg_completeness = 0

        return avg_completeness


    # reports and metadata
    def generate_metadata(self):
        metadata = {
            "collection_date": datetime.now().isoformat(), # get the date of collection
            "total_records": sum(len(v) for v in self.data_store.values()), # count the total number of records
            "success_rate": self.get_success_rate(), # call the success_rate method
            "series_collected": list(self.data_store.keys()) # get a list of the series' that were queried for
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"../reports/metadata_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(metadata, f, indent=2)

    def generate_quality_report(self):
        report_data = {
            "total_records": sum(len(v) for v in self.data_store.values()),
            "collection_success_rate": self.get_success_rate(),
            "quality_score": self.assess_data_quality(),
            "metrics": {
                "completeness": self.check_completeness(),
            }
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # attach the time the report was generated
        filename = f"../reports/quality_assessment_{timestamp}.json"
        with open("../reports/quality_assessment.json", "w") as f:
            json.dump(filename, f, indent=2)

    def generate_collection_summary(self):
        summary_data = {
            "total_data_points": sum(len(v) for v in self.data_store.values()), # sum of the collected data points
            "successes": self.collection_stats["successful_requests"], # return accumulated number of successful requests
            "failures": self.collection_stats["failed_requests"], # return accumulated number of failed requests
            "success rate": self.get_success_rate()
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"../reports/collection_summary_{timestamp}.json"
        with open("../reports/collection_summary.json", "w") as f:
            json.dump(filename, f, indent=2)


if __name__ == "__main__":
    # initialize agent with the config file
    agent = DataCollectionAgent("config.json")

    # start data collection
    print("Collecting data...")
    agent.collect_data()

    # generate reports
    print("Generating reports...")
    agent.generate_metadata()
    agent.generate_quality_report()
    agent.generate_collection_summary()
    print("Reports created")

    print("Data collection complete")
    print(f"Records collected: {sum(len(v) for v in agent.data_store.values())}")
    print(f"Collection success rate: {agent.get_success_rate():.2%}")
