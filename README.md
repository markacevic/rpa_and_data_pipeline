# Web Scraping and Data Processing Pipeline

This project implements a robust web scraping and data processing pipeline using Python. It follows a modular architecture for easy maintenance and extensibility.

## Project Structure

```
rpa/
├── .gitignore
├── config/                # Configuration files (e.g., settings.py)
├── dags/                  # Airflow DAGs for orchestration
├── Dockerfile             # Dockerfile for building the application image
├── docker-compose.yml     # Docker Compose for running the full stack (Airflow, etc.)
├── error_screenshots/     # Screenshots saved on scraping errors
├── logs/                  # Log files from application runs
├── main.py                # Main entry point for the application
├── outputs/               # Generated output files (raw data, processed data, reports)
├── README.md              # This file
├── requirements.txt       # Python package dependencies
├── run_dag_locally.py     # Script to run a DAG task without Airflow
├── src/                   # Main source code
│   ├── __init__.py
│   ├── processors/        # Data processing and transformation modules
│   ├── reporting/         # Analytics and reporting modules
│   ├── scrapers/          # Web scraping modules for each market
│   ├── utils/             # Helper functions and utilities
│   └── validators/        # Data validation and quality checks
└── tests/                 # Test suite
    ├── __init__.py
    ├── test_processor.py
    ├── test_scraper.py
    └── test_validator.py
```

## Setup & Running

There are two primary ways to run this project: using Docker (recommended for the full pipeline with Airflow) or running scripts locally with a Python environment.

### 1. Running with Docker (Recommended)

This method uses Docker Compose to build the necessary Docker images and run the Airflow services, which will then execute your DAGs.

**Prerequisites:**
- [Docker](https://docs.docker.com/get-docker/) installed and running.
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop).

**Instructions:**

1.  **Build and Start the Services:**
    From the project root directory, run the following command. This will build the Docker image for your project and start all services (Airflow webserver, scheduler, etc.) in the background.

    ```bash
    docker-compose up -d
    ```

2.  **Access Airflow UI:**
    Once the containers are running, open your web browser and navigate to `http://localhost:8080`. You should see the Airflow UI. The default credentials are `airflow` / `airflow`.

3.  **Run the DAG:**
    In the Airflow UI, you will find the `market_data_pipeline` DAG. You can enable it and trigger a new run manually.

4.  **Stop the Services:**
    To stop all running services, use the following command:
    ```bash
    docker-compose down
    ```

### 2. Local Python Setup

This method is suitable for running individual scripts or tests without the full Airflow orchestration layer.

**Instructions:**

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage (Local)

To run a specific scraper or processor locally without Airflow, you can invoke them via `run_dag_locally.py` or `main.py`.

1.  Configure settings in `config/settings.py`.
2.  Run the main script, which will execute the full scrape, process, and validate pipeline for a single market:
    ```bash
    python main.py <market_name> [options]
    ```

**Example:**
To run the scraper for "Vero" with a visible browser UI and a total limit of 100 products:
```bash
python main.py vero --no-headless --total-limit 100
```

**Options:**
*   `<market_name>`: (Required) The market to scrape (e.g., `vero`, `tinex`).
*   `--browser <name>`: Specify the browser to use (`chrome`, `edge`, `firefox`). Defaults to `chrome`.
*   `--total-limit <number>`: The maximum total number of products to scrape.
*   `--page-limit <number>`: The maximum number of products to scrape per page.
*   `--no-headless`: Use this flag to run the browser with a visible UI for debugging.

### 3. Simulating a DAG Run Locally

For debugging purposes, you can run the entire pipeline for a single market from your command line using the `run_dag_locally.py` script. This simulates the sequence of tasks (scrape, process, validate, report) without needing the full Airflow environment. This is the best way to test the full logic of a single pipeline.

**Usage:**

```bash
python run_dag_locally.py <market_name> [options]
```

**Example:**

To run the full pipeline for the "Vero" market with a visible browser UI and a limit of 50 products:

```bash
python run_dag_locally.py vero --limit 50
```

**Options:**

*   `<market_name>`: (Required) The name of the market to run (e.g., `vero`, `zito`).
*   `--headless`: Run the browser in headless mode (no UI).
*   `--limit <number>`: Stop scraping after a total of `<number>` products.
*   `--per-page <number>`: Set the number of items to show per page on sites that support it.

## Testing

Run the full test suite using pytest. The `-m` flag is recommended to ensure Python pathing works correctly.
```bash
python -m pytest tests/
```

## Architecture Overview and Design Decisions

This project is built with a modular and scalable architecture to facilitate easy maintenance and the addition of new data sources.

*   **Decoupled Components**: The application is divided into four main layers:
    1.  **Scrapers**: Responsible for fetching raw data from market websites.
    2.  **Processors**: Responsible for cleaning, standardizing, and transforming the raw data into a structured format.
    3.  **Validators**: Responsible for enforcing data quality and schema integrity.
    4.  **Reporting**: Responsible for generating analytics and summaries from the final, validated data.
    This separation of concerns makes the codebase easier to manage and test.

*   **Factory Pattern**: The `src.scrapers.factory` and `src.processors.factory` modules use a factory design pattern. This allows the main application to request a `scraper` or `processor` by name (e.g., "vero") without being tightly coupled to the specific implementation classes. This makes adding a new market as simple as creating a new class and registering it in the factory map.

*   **Centralized Configuration**: Market-specific configurations, such as base URLs, are stored in `config/settings.py`. This keeps the scraping logic generic and avoids hardcoding values, making the system easier to configure and maintain.

*   **Orchestration with Airflow**: The entire pipeline is designed to be orchestrated by Apache Airflow, as defined in `dags/market_pipelines_dag.py`. This allows for robust scheduling, monitoring, retries, and parallel execution of data pipelines for different markets.

*   **Containerization with Docker**: The project is fully containerized using `Dockerfile` and `docker-compose.yml`. This ensures a consistent and reproducible environment for all developers and for deployment, eliminating "it works on my machine" issues. Docker Compose orchestrates all the necessary Airflow services.

*   **Local Debugging Utilities**: Scripts like `main.py` and `run_dag_locally.py` are provided to allow developers to run and debug the entire pipeline for a single market outside of the full Docker/Airflow stack. This significantly improves the development and testing workflow.
