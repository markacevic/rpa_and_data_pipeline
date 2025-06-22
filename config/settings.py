import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = OUTPUT_DIR / "reports"

# Create necessary directories
OUTPUT_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Scraping settings
SCRAPING_DELAY = 2  # seconds between requests
MAX_RETRIES = 3 # number of retries for failed requests
TIMEOUT = 30 # timeout for requests

# Data processing settings
BATCH_SIZE = 1000
DATE_FORMAT = "%Y-%m-%d"

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File paths
RAW_DATA_PATH = OUTPUT_DIR / "raw_data.json"
PROCESSED_DATA_PATH = OUTPUT_DIR / "processed_data.csv"

# API settings (if needed)
API_TIMEOUT = 30
API_RETRY_COUNT = 3

# Database settings (if needed)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "scraping_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Market-specific configurations
MARKET_CONFIGS = {
    "vero": {
        "base_url": "https://pricelist.vero.com.mk/",
        "processor": "Vero",
        "default_total_limit": 150,
        "default_per_page_limit": 1,
    },
    "zito": {
        "base_url": "https://zito.proverkanaceni.mk/index.php",
        "processor": "Standard",
        "default_total_limit": 150,
        "default_per_page_limit": 1,
    },
    "tinex": {
        "base_url": "https://ceni.tinex.mk:442/index.php",
        "processor": "Standard",
        "default_total_limit": 150,
        "default_per_page_limit": 1,
    },
    "stokomak": {
        "base_url": "https://stokomak.proverkanaceni.mk/",
        "processor": "Standard",
        "default_total_limit": 150,
        "default_per_page_limit": 1,
    },
} 