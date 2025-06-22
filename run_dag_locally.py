import logging
import sys
from pathlib import Path
import argparse

# Add the project root to the Python path to allow importing project modules
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from dags.market_pipelines_dag import (
    scrape_data_task,
    process_data_task,
    validate_data_task,
    generate_analytics_report_task,
)

class MockTaskInstance:
    """A mock of the Airflow TaskInstance object to simulate XComs."""
    def __init__(self):
        self.xcoms = {}
        logging.info("Created MockTaskInstance for local run.")

    def xcom_push(self, key, value):
        logging.info(f"[XCOM PUSH] key='{key}', value='{value}'")
        self.xcoms[key] = value

    def xcom_pull(self, key, task_ids):
        logging.info(f"[XCOM PULL] key='{key}', task_ids='{task_ids}'")
        # In our new DAG, the key already contains the market name.
        return self.xcoms.get(key)

def run_pipeline_locally(market_name: str, browser: str = 'chrome', headless: bool = False, total_limit: int = None, per_page_limit: int = None):
    """
    Runs the main steps of a specific market's Airflow DAG locally.
    This is useful for debugging the core logic of the tasks.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    mock_ti = MockTaskInstance()
    
    # Define kwargs to pass to tasks, simulating the Airflow context
    kwargs = {'ti': mock_ti}

    try:
        # --- 1. Scrape Data ---
        logging.info(f"--- Starting local scrape task for '{market_name}' (browser visible: {not headless}) ---")
        scrape_data_task(
            market_name=market_name,
            browser=browser,
            headless=headless,
            total_limit=total_limit,
            per_page_limit=per_page_limit,
            **kwargs
        )
        
        # --- 2. Process Data ---
        logging.info(f"--- Starting local process task for '{market_name}' ---")
        process_data_task(market_name=market_name, **kwargs)
            
        # --- 3. Validate Data ---
        logging.info(f"--- Starting local validate task for '{market_name}' ---")
        validate_data_task(market_name=market_name, **kwargs)
        
        # --- 4. Generate Analytics ---
        logging.info(f"--- Starting local analytics task for '{market_name}' ---")
        generate_analytics_report_task(market_name=market_name, **kwargs)

        logging.info(f"--- Local pipeline run for '{market_name}' finished successfully! ---")

    except Exception as e:
        logging.error(f"An error occurred during the local run for '{market_name}': {e}", exc_info=True)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a market data pipeline locally.")
    parser.add_argument(
        "market_name",
        type=str,
        help="The name of the market to run (e.g., 'vero', 'zito')."
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the browser in headless mode (no UI)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of items to scrape (for testing)."
    )
    parser.add_argument(
        "--per-page",
        type=int,
        default=None,
        help="Limit the number of items per page (for testing)."
    )
    args = parser.parse_args()

    # Ensure output directories exist before running
    Path("outputs/reports").mkdir(parents=True, exist_ok=True)
    
    run_pipeline_locally(
        market_name=args.market_name, 
        headless=args.headless, 
        total_limit=args.limit,
        per_page_limit=args.per_page
    ) 