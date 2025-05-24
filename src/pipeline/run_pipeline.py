#!/usr/bin/env python3

from src.data_analysis import preprocess
from src.data_analysis.fetcher import fetch_hackernews_data


def main():
    print("Starting HackerNews data pipeline...")

    try:  # Fetch data from HackerNews
        print("Fetching data from HackerNews...")
        items = fetch_hackernews_data(max_stories=8, max_comments=2)

        if not items:
            print("Error: No data fetched")
            return False

        print(f"Fetched {len(items)} items")

        # Preprocess and save
        print("Processing data...")
        output_file = preprocess.save_preprocessed_data(
            items, "src/data/hackernews_optimized.txt"
        )

        print(f"Data saved to: {output_file}")
        print("Update your .env file with:")
        print(f"DATA_PATH={output_file}")

        return True

    except Exception as e:
        print(f"Pipeline error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("Pipeline completed")
    else:
        print("Pipeline failed")
