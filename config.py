from pathlib import Path

# ==========================================
# JANW ENTERPRISE - SYSTEM CONFIGURATION
# ==========================================

# Folder containing this project
BASE_DIR = Path(__file__).resolve().parent

# Project folders
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = BASE_DIR / "documents"

QUOTATIONS_DIR = DOCUMENTS_DIR / "quotations"
INVOICES_DIR = DOCUMENTS_DIR / "invoices"

# Important files
DATABASE_FILE = DATA_DIR / "janw.db"
LETTERHEAD_FILE = ASSETS_DIR / "letterhead.png"


# ==========================================
# COMPANY INFORMATION
# ==========================================

COMPANY_NAME = "JANW ENTERPRISE (PTY) LTD"

SLOGAN = "EMPOWERING WOMEN IN CONSTRUCTION"

ADDRESS = "55 Gannabos Street, Windsorton, 8510"

PHONE = "072 673 3646"

EMAIL = "jandwenterprise1968@gmail.com"


# ==========================================
# DOCUMENT SETTINGS
# ==========================================

CURRENCY = "R"

QUOTE_PREFIX = "QT"

INVOICE_PREFIX = "INV"

DEFAULT_QUOTE_VALID_DAYS = 30


# ==========================================
# CREATE REQUIRED FOLDERS
# ==========================================

def create_folders():
    """Create system folders if they do not already exist."""

    folders = [
        ASSETS_DIR,
        DATA_DIR,
        DOCUMENTS_DIR,
        QUOTATIONS_DIR,
        INVOICES_DIR,
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)


# Automatically make sure folders exist
create_folders()