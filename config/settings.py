import os
from pathlib import Path

# -----------------------------------------------------------------------------
# DIRECTORY PATHS
# -----------------------------------------------------------------------------
# Define project-wide paths to ensure consistency.
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = OUTPUT_DIR / "reports"
SRC_DIR = PROJECT_ROOT / "src"

# Create necessary directories on startup if they don't exist.
OUTPUT_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# --------------------- --------------------------------------------------------
# MARKET CONFIGURATIONS
# -----------------------------------------------------------------------------
# This dictionary holds the specific configurations for each market.
# - 'base_url': The starting URL for the scraper.
# - 'processor': The name of the data processor to use.
# - 'default_total_limit': A default safety limit for the number of products.
# - 'default_per_page_limit': The default number of items to request per page.
# -----------------------------------------------------------------------------
MARKET_CONFIGS = {
    "vero": {
        "base_url": "https://pricelist.vero.com.mk/",
        "processor": "Vero",
        "default_total_limit": 2,
        "default_per_page_limit": 1,
    },
    "zito": {
        "base_url": "https://zito.proverkanaceni.mk/index.php",
        "processor": "Standard",
        "default_total_limit": 2,
        "default_per_page_limit": 1,
    },
    "tinex": {
        "base_url": "https://ceni.tinex.mk:442/index.php",
        "processor": "Standard",
        "default_total_limit": 2,
        "default_per_page_limit": 1,
    },
    "stokomak": {
        "base_url": "https://stokomak.proverkanaceni.mk/",
        "processor": "Standard",
        "default_total_limit": 2,
        "default_per_page_limit": 1,
    },
} 