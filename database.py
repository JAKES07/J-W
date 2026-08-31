import sqlite3
from config import DATABASE_FILE


# ============================================================
# JANW ENTERPRISE - DATABASE
# ============================================================


def get_connection():
    """Open a connection to the JANW database."""

    connection = sqlite3.connect(DATABASE_FILE)

    connection.row_factory = sqlite3.Row

    # Enforce relationships between tables
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# CHECK WHETHER A COLUMN EXISTS
# ============================================================

def column_exists(cursor, table_name, column_name):
    """
    Check whether a column already exists in a SQLite table.
    """

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    for column in columns:

        # column[1] contains the column name
        if column[1] == column_name:
            return True

    return False


# ============================================================
# DATABASE UPGRADES
# ============================================================

def upgrade_database(cursor):
    """
    Upgrade an existing JANW database without deleting
    existing quotations, invoices, customers or items.
    """

    # --------------------------------------------------------
    # QUOTATION ITEM UNIT
    # --------------------------------------------------------

    if not column_exists(
        cursor,
        "quotation_items",
        "unit"
    ):

        cursor.execute("""
            ALTER TABLE quotation_items
            ADD COLUMN unit TEXT DEFAULT ''
        """)

        print(
            "Database upgraded: "
            "quotation item units added."
        )

    # --------------------------------------------------------
    # INVOICE ITEM UNIT
    # --------------------------------------------------------

    if not column_exists(
        cursor,
        "invoice_items",
        "unit"
    ):

        cursor.execute("""
            ALTER TABLE invoice_items
            ADD COLUMN unit TEXT DEFAULT ''
        """)

        print(
            "Database upgraded: "
            "invoice item units added."
        )


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():
    """Create and upgrade all required database tables."""

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ====================================================
        # CUSTOMERS
        # ====================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                customer_number TEXT UNIQUE,

                name TEXT NOT NULL,
                company TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # QUOTATIONS
        # ====================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                quote_number TEXT UNIQUE NOT NULL,

                customer_id INTEGER,

                quote_date TEXT NOT NULL,
                valid_until TEXT,

                prepared_by TEXT,

                subtotal REAL DEFAULT 0,

                tax_rate REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,

                other_amount REAL DEFAULT 0,

                total REAL DEFAULT 0,

                status TEXT DEFAULT 'DRAFT',

                notes TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (customer_id)
                    REFERENCES customers(id)
            )
        """)

        # ====================================================
        # QUOTATION ITEMS
        # ====================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotation_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                quotation_id INTEGER NOT NULL,

                description TEXT NOT NULL,

                quantity REAL DEFAULT 1,

                unit TEXT DEFAULT '',

                unit_price REAL DEFAULT 0,

                taxable INTEGER DEFAULT 0,

                amount REAL DEFAULT 0,

                FOREIGN KEY (quotation_id)
                    REFERENCES quotations(id)
                    ON DELETE CASCADE
            )
        """)

        # ====================================================
        # INVOICES
        # ====================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                invoice_number TEXT UNIQUE NOT NULL,

                customer_id INTEGER,

                invoice_date TEXT NOT NULL,

                due_date TEXT,

                prepared_by TEXT,

                subtotal REAL DEFAULT 0,

                tax_rate REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,

                other_amount REAL DEFAULT 0,

                total REAL DEFAULT 0,

                status TEXT DEFAULT 'UNPAID',

                notes TEXT,

                source_quote_id INTEGER,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (customer_id)
                    REFERENCES customers(id),

                FOREIGN KEY (source_quote_id)
                    REFERENCES quotations(id)
            )
        """)

        # ====================================================
        # INVOICE ITEMS
        # ====================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                invoice_id INTEGER NOT NULL,

                description TEXT NOT NULL,

                quantity REAL DEFAULT 1,

                unit TEXT DEFAULT '',

                unit_price REAL DEFAULT 0,

                taxable INTEGER DEFAULT 0,

                amount REAL DEFAULT 0,

                FOREIGN KEY (invoice_id)
                    REFERENCES invoices(id)
                    ON DELETE CASCADE
            )
        """)

        # ====================================================
        # UPGRADE OLD DATABASES
        # ====================================================

        upgrade_database(cursor)

        # ====================================================
        # SAVE CHANGES
        # ====================================================

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()