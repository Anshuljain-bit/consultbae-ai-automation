import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://consultbae:consultbae@127.0.0.1:3306/consultbae_assignment",
)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
if not UPLOAD_DIR.is_absolute():
    UPLOAD_DIR = BASE_DIR / UPLOAD_DIR

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

DEFAULT_SOURCE1 = BASE_DIR / "data" / "raw" / "source1_naukri_applicants.csv"
DEFAULT_SOURCE2 = BASE_DIR / "data" / "raw" / "source2_gig_workers.csv"
DEFAULT_SOURCE3 = BASE_DIR / "data" / "raw" / "source3_cbnexus_contacts.csv"
