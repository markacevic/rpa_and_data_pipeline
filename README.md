# Web Scraping and Data Processing Pipeline

This project implements a robust web scraping and data processing pipeline using Python. It follows a modular architecture for easy maintenance and extensibility.

## Project Structure

```
project_root/
├── src/                    # Source code
│   ├── scrapers/          # Web scraping modules
│   ├── processors/        # Data processing modules
│   ├── validators/        # Data validation modules
│   └── utils/             # Utility functions
├── dags/                  # Airflow DAGs
├── config/                # Configuration files
├── tests/                 # Test files
└── outputs/              # Output data and reports
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Configure settings in `config/settings.py`
2. Run the pipeline:
```bash
python -m src.main
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

## License

MIT 