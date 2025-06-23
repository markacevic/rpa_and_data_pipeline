import os
import json
import logging
from datetime import datetime
from typing import Any, Dict
import random
import time
from selenium.webdriver.remote.webdriver import WebDriver

def setup_logging(log_level: str = "INFO") -> None:
    """Configures the root logger for the application.

    Args:
        log_level (str, optional): The minimum logging level to capture. 
            Defaults to "INFO".
    """
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_output_dir(dir_path: str) -> None:
    """Creates a directory if it does not already exist.

    Args:
        dir_path (str): The path of the directory to create.
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def save_json(data: Dict[str, Any], filepath: str) -> None:
    """Saves a dictionary to a file in JSON format.

    Args:
        data (Dict[str, Any]): The dictionary data to save.
        filepath (str): The path to the output JSON file.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filepath: str) -> Dict[str, Any]:
    """Loads data from a JSON file into a dictionary.

    Args:
        filepath (str): The path to the JSON file to load.

    Returns:
        Dict[str, Any]: The data loaded from the JSON file.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_timestamp() -> str:
    """Generates a timestamp string in a specific format.

    Returns:
        str: A timestamp string formatted as "YYYYMMDD_HHMMSS".
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def format_filename(base_name: str, extension: str) -> str:
    """Formats a filename by appending a timestamp.

    Args:
        base_name (str): The base name for the file.
        extension (str): The file extension.

    Returns:
        str: A formatted filename in the format 'base_name_YYYYMMDD_HHMMSS.extension'.
    """
    timestamp = get_timestamp()
    return f"{base_name}_{timestamp}.{extension}"

def random_delay(min_sec: float = 1.5, max_sec: float = 4.0) -> None:
    """Pauses execution for a random amount of time.

    This function is used to simulate human-like delays between web requests
    to avoid triggering anti-scraping mechanisms.

    Args:
        min_sec (float, optional): The minimum delay in seconds. Defaults to 1.5.
        max_sec (float, optional): The maximum delay in seconds. Defaults to 4.0.
    """
    delay = random.uniform(min_sec, max_sec)
    logging.info(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def handle_selenium_error(driver: WebDriver, logger: logging.Logger, e: Exception, context: str) -> None:
    """Handles errors during Selenium operations.

    This function logs the given exception and attempts to save a screenshot
    of the current browser state for debugging purposes.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        logger (logging.Logger): The logger instance to use for logging the error.
        e (Exception): The exception that was caught.
        context (str): A string describing the context in which the error occurred.
    """
    logger.error(f"An error occurred during {context}: {e}", exc_info=True)
    try:
        screenshots_dir = "error_screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        safe_context = context.replace('/', '_').replace(':', '')
        screenshot_file = os.path.join(screenshots_dir, f"{safe_context}_{timestamp}.png")
        driver.save_screenshot(screenshot_file)
        logger.info(f"Saved screenshot for debugging to: {screenshot_file}")
    except Exception as screenshot_error:
        logger.error(f"Could not save screenshot: {screenshot_error}") 