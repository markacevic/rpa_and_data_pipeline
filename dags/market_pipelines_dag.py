# -*- coding: utf-8 -*-
"""
Airflow DAG to dynamically orchestrate the Supermarket Data Pipeline for all
configured markets.

This DAG provides a comprehensive data pipeline that:
- Scrapes product data from multiple supermarket websites
- Validates and processes the raw data according to defined schemas
- Generates analytics reports and summary statistics
- Supports dynamic configuration for different markets
- Handles error recovery and retry logic
- Provides manual trigger capabilities with customizable parameters

The pipeline supports multiple markets that can be configured through the MARKET_CONFIGS in settings.py.

Each market can be configured with specific scraping limits, browser settings,
and processing parameters through the MARKET_CONFIGS in settings.py.
"""
import logging
import os
import sys
from datetime import datetime, timedelta

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

# Add the project root to the Python path to allow importing project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import MARKET_CONFIGS
from src.processors import get_data_processor
from src.scrapers.factory import get_market_scraper
from src.validators.data_validator import DataValidator
from src.reporting.analytics import generate_summary_analytics

# --- Task Functions (remain the same, but are now more generic) ---

def scrape_data_task(market_name: str, browser: str, headless: bool, **kwargs):
    """Scrapes data for a given market using the configured scraper.
    
    This task dynamically creates a scraper instance based on the market name
    and configuration, then executes the scraping process. The raw data file
    path is stored in XCom for downstream tasks.
    
    Args:
        market_name: The name of the market to scrape (e.g., 'vero', 'stokomak').
        browser: The browser to use for scraping ('chrome' or 'firefox').
        headless: Whether to run the browser in headless mode.
        **kwargs: Additional keyword arguments including Airflow context.
        
    Raises:
        ValueError: If scraping fails or no output files are produced.
    """
    # Read params from the DAG run configuration for manual runs
    params = kwargs.get('params', {})
    # Prioritize manual 'params', but fall back to the default op_kwargs value.
    total_limit = params.get('total_limit', kwargs.get('total_limit'))
    per_page_limit = params.get('per_page_limit', kwargs.get('per_page_limit'))

    logging.info(
        f"Starting scrape task for market: {market_name} "
        f"(total_limit: {total_limit}, per_page_limit: {per_page_limit})"
    )
    config = MARKET_CONFIGS[market_name]
    
    with get_market_scraper(
        market_name=market_name,
        base_url=config['base_url'],
        browser=browser,
        headless=headless,
        total_limit=total_limit,
        per_page_limit=per_page_limit
    ) as scraper:
        output_files = scraper.scrape()

    if not output_files:
        raise ValueError(f"Scraping failed, no output files produced for {market_name}.")

    # For simplicity, we assume one primary output file from the scrape task.
    # If a scraper can produce multiple files, this logic may need adjustment.
    kwargs['ti'].xcom_push(key=f'{market_name}_raw_data_path', value=output_files[0])


def process_data_task(market_name: str, **kwargs):
    """Processes raw scraped data for a given market using the configured data processor.
    
    This task retrieves the raw data file path from XCom, processes the data using
    the market-specific processor, and saves the processed data to a CSV file.
    The processed data file path is stored in XCom for downstream tasks.
    
    Args:
        market_name: The name of the market to process data for (e.g., 'vero', 'stokomak').
        **kwargs: Additional keyword arguments including Airflow context.
        
    Raises:
        ValueError: If the raw data file is not found or invalid.
        ValueError: If processing results in an empty DataFrame.
    """
    ti = kwargs['ti']
    raw_data_path = ti.xcom_pull(key=f'{market_name}_raw_data_path', task_ids=f'scrape_{market_name}_data')
    logging.info(f"Processing data for {market_name} from: {raw_data_path}")

    if not raw_data_path or not os.path.exists(raw_data_path):
        raise ValueError(f"Raw data file for {market_name} not found or path is invalid.")

    processor = get_data_processor(market_name)
    processed_df = processor.process_market_data(raw_data_path)

    if processed_df.empty:
        raise ValueError(f"Processing for {market_name} resulted in an empty DataFrame.")

    processed_data_path = f"outputs/{market_name}_processed_data.csv"
    processed_df.to_csv(processed_data_path, index=False, encoding='utf-8')

    ti.xcom_push(key=f'{market_name}_processed_data_path', value=processed_data_path)


def validate_data_task(market_name: str, **kwargs):
    """Validates processed data for a given market using the data validator.
    
    This task retrieves the processed data file path from XCom, validates the data
    using the DataValidator, and saves the validated data to a CSV file. If no data
    remains after validation, it pushes None to XCom to indicate that downstream
    tasks should be skipped.
    
    Args:
        market_name: The name of the market to validate data for (e.g., 'vero', 'stokomak').
        **kwargs: Additional keyword arguments including Airflow context.
        
    Raises:
        ValueError: If the processed data file is not found.
    """
    ti = kwargs['ti']
    processed_data_path = ti.xcom_pull(key=f'{market_name}_processed_data_path', task_ids=f'process_{market_name}_data')
    logging.info(f"Validating data for {market_name} from: {processed_data_path}")

    if not processed_data_path or not os.path.exists(processed_data_path):
        raise ValueError(f"Processed data file for {market_name} not found.")

    df = pd.read_csv(processed_data_path)
    validator = DataValidator()
    validated_df = validator.validate(df, market_name)

    if validated_df.empty:
        logging.warning(f"No data remained for {market_name} after validation.")
        # Push None to indicate no further steps should run for this market
        ti.xcom_push(key=f'{market_name}_validated_data_path', value=None)
        return

    validated_data_path = f"outputs/{market_name}_validated_data.csv"
    validated_df.to_csv(validated_data_path, index=False, encoding='utf-8')
    ti.xcom_push(key=f'{market_name}_validated_data_path', value=validated_data_path)


def generate_analytics_report_task(market_name: str, **kwargs):
    """Generates analytics report for validated data of a given market.
    
    This task retrieves the validated data file path from XCom, reads the data,
    and generates a summary analytics report in JSON format. If no validated data
    is available, the task logs a warning and exits gracefully.
    
    Args:
        market_name: The name of the market to generate analytics for (e.g., 'vero', 'stokomak').
        **kwargs: Additional keyword arguments including Airflow context.
    """
    ti = kwargs['ti']
    validated_data_path = ti.xcom_pull(key=f'{market_name}_validated_data_path', task_ids=f'validate_{market_name}_data')

    if not validated_data_path:
        logging.warning(f"No validated data path found for {market_name}. Skipping analytics.")
        return

    df = pd.read_csv(validated_data_path)
    report_path = f"outputs/reports/{market_name}_summary_analytics_report.json"
    generate_summary_analytics(df, report_path)


# --- DAG Generation Loop ---

def create_dag(market_name: str, market_config: dict):
    """Creates an Airflow DAG for a specific market's data pipeline.
    
    This function dynamically creates a complete DAG with four sequential tasks:
    scraping, processing, validation, and analytics generation. The DAG is configured
    with appropriate scheduling, retry logic, and task dependencies.
    
    Args:
        market_name: The name of the market to create a DAG for (e.g., 'vero', 'stokomak').
        market_config: Dictionary containing market-specific configuration including
                      base_url, default_total_limit, and default_per_page_limit.
    
    Returns:
        DAG: A configured Airflow DAG instance for the specified market.
    """
    
    dag_id = f'supermarket_data_pipeline_{market_name}'
    
    default_args = {
        'owner': 'airflow',
        'depends_on_past': False,
        'start_date': datetime(2025, 6, 22),
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=2),
    }

    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        description=f'A data pipeline for the {market_name.title()} supermarket.',
        schedule_interval=timedelta(days=1),
        catchup=False,
        tags=['data-pipeline', 'scraping', market_name]
    )

    with dag:
        scrape_task = PythonOperator(
            task_id=f'scrape_{market_name}_data',
            python_callable=scrape_data_task,
            op_kwargs={
                'market_name': market_name,
                'browser': 'chrome',
                'headless': True,
                'total_limit': market_config['default_total_limit'],
                'per_page_limit': market_config['default_per_page_limit']
            },
        )

        process_task = PythonOperator(
            task_id=f'process_{market_name}_data',
            python_callable=process_data_task,
            op_kwargs={'market_name': market_name},
        )

        validate_task = PythonOperator(
            task_id=f'validate_{market_name}_data',
            python_callable=validate_data_task,
            op_kwargs={'market_name': market_name},
        )

        analytics_task = PythonOperator(
            task_id=f'generate_{market_name}_analytics_report',
            python_callable=generate_analytics_report_task,
            op_kwargs={'market_name': market_name},
        )

        scrape_task >> process_task >> validate_task >> analytics_task
        
    return dag

# This is the standard Airflow pattern for dynamically generating DAGs.
# Airflow will scan this file and discover each DAG created in this loop.
for market, config in MARKET_CONFIGS.items():
    dag = create_dag(market, config)
    globals()[dag.dag_id] = dag 