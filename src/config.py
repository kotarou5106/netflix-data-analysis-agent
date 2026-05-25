from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORTS_DIR = PROJECT_ROOT / "reports"
NETFLIX_CSV_PATH = DATA_DIR / "netflix_user_behavior_dataset.csv"
