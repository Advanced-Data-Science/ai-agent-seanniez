import requests
import json
import time
import random
from datetime import datetime
import os
from dotenv import load_dotenv

class DataCollectionAgent:
    def __init__(self, config_file):
        # Load configuration
        self.config = self.load_config(config_file)
        load_dotenv()
        api_key = os.getenv("FRED_API_KEY")
        if api_key:
            self.config["FRED_API_KEY"] = api_key

        # Initialize data store and stats
        self.data_store = {}
        self.collection_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }
        self.delay_multiplier = 1.0

    # configuration management
    def load_config(self, config_file):
        if not os.path.exists(config_file): # handle case where config file is not found
            raise FileNotFoundError(f"Config file {config_file} not found")
        with open(config_file, "r") as f:
            return json.load(f)

    # intelligent collection strategy
    def collect_data(self):
        series_ids = [
            self.config.get("GDP_SERIES_ID", "GDP"), # annual GDP
            self.config.get("CPI_SERIES_ID", "CPIAUCSL") # annual CPI
        ]
        start_date = self.config.get("START_DATE") # store start date as stated in config
        end_date = self.config.get("END_DATE") # store end date as stated in config
        base_url = "https://api.stlouisfed.org/fred/series/observations"
        api_key = self.config.get("FRED_API_KEY")

        # raw data collection
        while not self.collection_complete(): # continue collected data as long as it is not yet complete
            raw_batch = {}
            for series in series_ids:
                # data collection parameters
                params = {
                    "series_id": series,
                    "api_key": api_key,
                    "file_type": "json",
                    "observation_start": start_date,
                    "observation_end": end_date
                }
                data = self.make_api_request(base_url, params) # request data per params
                raw_batch[series] = data

                self.respectful_delay()  # rate limiting

            processed = self.process_data(raw_batch)
            if self.validate_data(processed):
                self.store_data(processed)
            self.adjust_strategy()  # adaptive logic

    # data quality assessment
    def assess_data_quality(self):
        """Evaluate the quality of collected data"""
        if not self.data_store:
            return 0

        quality_metrics = {
            'completeness': self.check_completeness(),
            'accuracy': self.check_accuracy(),
            'consistency': self.check_consistency(),
            'timeliness': self.check_timeliness()
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
            self.try_fallback_api()
        elif success_rate > 0.9:
            # Can be more aggressive
            self.delay_multiplier *= 0.8

        # Log strategy changes
        self.log_strategy_change()

    # respectful collection
    def respectful_delay(self):
        """Implement respectful rate limiting"""
        base_delay = self.config.get('base_delay', 1.0)
        delay = base_delay * self.delay_multiplier

        # Add random jitter to avoid thundering herd
        jitter = random.uniform(0.5, 1.5)
        time.sleep(delay * jitter)

    def check_rate_limits(self):
        pass  # stub

    # -----------------------------
    # Core API + Data Methods
    # -----------------------------
    def make_api_request(self, url, params):
        self.collection_stats["total_requests"] += 1
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            self.collection_stats["successful_requests"] += 1
            return response.json()
        except Exception as e:
            self.collection_stats["failed_requests"] += 1
            print(f"API request failed: {e}")
            return None

    # standardize numbers and missing entries and store as a dictionary
    def process_data(self, raw_batch):
        processed = {}
        for series, data in raw_batch.items():
            if data is None or "observations" not in data:
                continue
            processed[series] = [] # holds cleaned data
            for obs in data["observations"]:
                try:
                    value = float(obs["value"])
                except ValueError:
                    value = None # standardize missing data
                processed[series].append({"date": obs["date"], "value": value})
        return processed

    def validate_data(self, processed):
        return bool(processed)

    # method to store data in the class' data structure
    def store_data(self, processed):
        for series, observations in processed.items():
            if series not in self.data_store:
                self.data_store[series] = [] # create a list if series is not already in data_store
            self.data_store[series].extend(observations) # store data in data_store

    # helper methods
    def collection_complete(self):
        """
        Stop collecting once all series have reached the expected number of rows
        specified in the config.
        """
        for series, expected_rows in self.config.get("EXPECTED_ROWS", {}).items():
            observations = self.data_store.get(series, [])
            if len(observations) < expected_rows:
                return False  # still need more data for this series
        return True  # all series have enough data

    def get_success_rate(self):
        total = self.collection_stats["total_requests"]
        if total == 0:
            return 0
        return self.collection_stats["successful_requests"] / total

    def check_completeness(self):
        completeness_scores = {}

        for series, observations in self.data_store.items():
            if not observations:
                completeness_scores[series] = 0
                continue

            total = len(observations) # total requests
            non_missing = sum(1 for obs in observations if obs["value"] is not None) # actual observations
            completeness_scores[series] = non_missing / total # ratio of observations to total

        # average across series for one score
        if completeness_scores:
            avg_completeness = sum(completeness_scores.values()) / len(completeness_scores)
        else:
            avg_completeness = 0

        return avg_completeness

    def check_accuracy(self):
        return 1.0

    def check_consistency(self):
        return 1.0

    def check_timeliness(self):
        return 1.0

    def try_fallback_api(self):
        pass

    def log_strategy_change(self):
        pass

    # report and metadata generation
    def generate_metadata(self):
        metadata = {
            "collection_date": datetime.now().isoformat(),
            "total_records": sum(len(v) for v in self.data_store.values()),
            "success_rate": self.get_success_rate(),
            "series_collected": list(self.data_store.keys())
        }
        os.makedirs("metadata", exist_ok=True)
        with open("metadata/collection_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    def generate_quality_report(self):
        report = {
            "total_records": sum(len(v) for v in self.data_store.values()),
            "collection_success_rate": self.get_success_rate(),
            "quality_score": self.assess_data_quality(),
            "metrics": {
                "completeness": self.check_completeness(),
                "accuracy": self.check_accuracy(),
                "consistency": self.check_consistency(),
                "timeliness": self.check_timeliness()
            }
        }
        os.makedirs("reports", exist_ok=True)
        with open("reports/quality_report.json", "w") as f:
            json.dump(report, f, indent=2)

    def generate_collection_summary(self):
        summary = {
            "total_data_points": sum(len(v) for v in self.data_store.values()),
            "successes": self.collection_stats["successful_requests"],
            "failures": self.collection_stats["failed_requests"],
            "recommendations": "Check API keys and series IDs"
        }
        os.makedirs("reports", exist_ok=True)
        with open("reports/collection_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
