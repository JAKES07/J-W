import sys
from pathlib import Path

# ============================================================
# JANW ENTERPRISE - INVOICE PDF GENERATOR
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


# ============================================================
# IMPORTS
# ============================================================

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

from database import get_connection
from config import INVOICES_DIR, LETTERHEAD_FILE


# ============================================================
# PAGE SETTINGS
# ============================================================

PAGE_WIDTH, PAGE_HEIGHT = A4

NAVY = colors.HexColor("#0B1E33")
ORANGE = colors.HexColor("#E87513")
LIGHT_GREY = colors.HexColor("#EAEAEA")
WHITE = colors.white
BLACK = colors.black


# ============================================================
# BANKING DETAILS
# ============================================================

BANK_NAME = "Capitec Business"
ACCOUNT_NUMBER = "1053543956"
BRANCH_CODE = "450105"


# ============================================================
# MONEY FORMAT
# ============================================================

def money(value):

    if value is None:
        value = 0

    return f"R {float(value):,.2f}"


# ============================================================
# SHOW SAVED INVOICES
# ============================================================

def show_invoices():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            i.id,
            i.invoice_number,
            i.invoice_date,
            i.total,
            c.name AS customer_name

        FROM invoices i

        LEFT JOIN customers c
            ON i.customer_id = c.id

        ORDER BY i.id DESC
    """)

    invoices = cursor.fetchall()

    connection.close()

    print()
    print("=" * 65)
    print("JANW ENTERPRISE - INVOICE PDF GENERATOR")
    print("=" * 65)

    if not invoices:

        print()
        print("No invoices have been saved yet.")
        print()

        return []

    print()
    print("SAVED INVOICES")
    print("-" * 65)

    for invoice in invoices:

        print()

        print(
            f"ID: {invoice['id']}  |  "
            f"{invoice['invoice_number']}"
        )

        print(
            f"Customer: "
            f"{invoice['customer_name'] or 'No customer'}"
        )

        print(
            f"Date: {invoice['invoice_date']}  |  "
            f"Total: {money(invoice['total'])}"
        )

        print("-" * 65)

    return invoices


# ============================================================
# CHOOSE INVOICE
# ============================================================

def choose_invoice():

    invoices = show_invoices()

    if not invoices:
        return None

    valid_ids = {
        invoice["id"]
        for invoice in invoices
    }

    while True:

        print()

        choice = input(
            "Enter invoice ID to generate PDF "
            "(0 to cancel): "
        ).strip()

        if choice == "0":

            print()
            print("PDF generation cancelled.")

            return None

        try:

            invoice_id = int(choice)

        except ValueError:

            print()
            print("Please enter an invoice ID number.")

            continue

        if invoice_id not in valid_ids:

            print()
            print("That invoice ID does not exist.")

            continue

        return invoice_id


# ============================================================
# GENERATE INVOICE PDF
# ============================================================

def generate_invoice_pdf(invoice_id):

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # GET INVOICE
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            i.*,

            c.customer_number,
            c.name AS customer_name,
            c.company AS customer_company,
            c.address AS customer_address,
            c.phone AS customer_phone,
            c.email AS customer_email

        FROM invoices i

        LEFT JOIN customers c
            ON i.customer_id = c.id

        WHERE i.id = ?
    """, (invoice_id,))

    invoice = cursor.fetchone()

    if invoice is None:

        connection.close()

        print()
        print("=" * 50)
        print("INVOICE NOT FOUND")
        print("=" * 50)

        return None

    # --------------------------------------------------------
    # GET INVOICE ITEMS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            description,
            quantity,
            unit,
            unit_price,
            amount

        FROM invoice_items

        WHERE invoice_id = ?

        ORDER BY id
    """, (invoice_id,))

    items = cursor.fetchall()

    connection.close()

    # --------------------------------------------------------
    # OUTPUT FILE
    # --------------------------------------------------------

    INVOICES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    invoice_number = invoice["invoice_number"]

    output_file = (
        INVOICES_DIR
        / f"{invoice_number}.pdf"
    )

    # --------------------------------------------------------
    # CREATE PDF
    # --------------------------------------------------------

    pdf = canvas.Canvas(
        str(output_file),
        pagesize=A4
    )

    pdf.setTitle(
        f"JANW Enterprise - {invoice_number}"
    )

    pdf.setAuthor(
        "JANW ENTERPRISE (PTY) LTD"
    )

    # ========================================================
    # LETTERHEAD
    # ========================================================

    HEADER_HEIGHT = 170

    if LETTERHEAD_FILE.exists():

        try:

            letterhead = ImageReader(
                str(LETTERHEAD_FILE)
            )

            pdf.drawImage(
                letterhead,
                0,
                PAGE_HEIGHT - HEADER_HEIGHT,
                width=PAGE_WIDTH,
                height=HEADER_HEIGHT,
                preserveAspectRatio=False,
                mask="auto"
            )

        except Exception as error:

            print()
            print("Could not load letterhead:")
            print(error)

    else:

        print()
        print(
            "WARNING: assets/letterhead.png "
            "was not found."
        )

    # Orange separator line

    pdf.setFillColor(ORANGE)

    pdf.rect(
        0,
        PAGE_HEIGHT - HEADER_HEIGHT - 4,
        PAGE_WIDTH,
        4,
        fill=1,
        stroke=0
    )

    # ========================================================
    # TITLE
    # ========================================================

    title_y = PAGE_HEIGHT - 210

    pdf.setFillColor(ORANGE)

    pdf.setFont(
        "Helvetica-Bold",
        22
    )

    pdf.drawRightString(
        PAGE_WIDTH - 40,
        title_y,
        "INVOICE"
    )

    # ========================================================
    # PREPARED BY
    # ========================================================

    prepared_by = (
        invoice["prepared_by"] or ""
    )

    pdf.setFillColor(BLACK)

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        40,
        title_y,
        f"Prepared by: {prepared_by}"
    )

    # ========================================================
    # CUSTOMER
    # ========================================================

    customer_header_y = title_y - 45

    pdf.setFillColor(NAVY)

    pdf.rect(
        40,
        customer_header_y,
        245,
        18,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(WHITE)

    pdf.setFont(
        "Helvetica-Bold",
        9
    )

    pdf.drawString(
        46,
        customer_header_y + 5,
        "CUSTOMER"
    )

    customer_y = customer_header_y - 16

    pdf.setFillColor(BLACK)

    pdf.setFont(
        "Helvetica",
        9
    )

    customer_details = [
        invoice["customer_name"],
        invoice["customer_company"],
        invoice["customer_address"],
        invoice["customer_phone"],
        invoice["customer_email"]
    ]

    for detail in customer_details:

        if detail:

            pdf.drawString(
                42,
                customer_y,
                str(detail)[:60]
            )

            customer_y -= 13

    # ========================================================
    # INVOICE INFORMATION
    # ========================================================

    info_x = 365
    info_y = PAGE_HEIGHT - 250

    information = [
        (
            "DATE",
            invoice["invoice_date"]
        ),
        (
            "INVOICE #",
            invoice["invoice_number"]
        ),
        (
            "CUSTOMER ID",
            invoice["customer_number"]
        )
    ]

    for label, value in information:

        # Label box

        pdf.setFillColor(NAVY)

        pdf.rect(
            info_x,
            info_y,
            90,
            20,
            fill=1,
            stroke=1
        )

        pdf.setFillColor(WHITE)

        pdf.setFont(
            "Helvetica-Bold",
            8
        )

        pdf.drawString(
            info_x + 5,
            info_y + 6,
            label
        )

        # Value box

        pdf.setFillColor(WHITE)

        pdf.rect(
            info_x + 90,
            info_y,
            100,
            20,
            fill=1,
            stroke=1
        )

        pdf.setFillColor(BLACK)

        pdf.setFont(
            "Helvetica",
            8
        )

        pdf.drawString(
            info_x + 95,
            info_y + 6,
            str(value or "")
        )

        info_y -= 20

    # ========================================================
    # ITEM TABLE
    #
    # DESCRIPTION | QTY | UNIT | UNIT PRICE | AMOUNT
    # ========================================================

    table_y = PAGE_HEIGHT - 390

    table_left = 40
    table_right = 555

    # Column boundaries

    description_end = 285
    qty_end = 335
    unit_end = 385
    price_end = 465

    # --------------------------------------------------------
    # TABLE HEADER
    # --------------------------------------------------------

    pdf.setFillColor(NAVY)

    pdf.rect(
        table_left,
        table_y,
        table_right - table_left,
        22,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(WHITE)

    pdf.setFont(
        "Helvetica-Bold",
        7.5
    )

    pdf.drawString(
        50,
        table_y + 7,
        "DESCRIPTION"
    )

    pdf.drawCentredString(
        310,
        table_y + 7,
        "QTY"
    )

    pdf.drawCentredString(
        360,
        table_y + 7,
        "UNIT"
    )

    pdf.drawCentredString(
        425,
        table_y + 7,
        "UNIT PRICE"
    )

    pdf.drawCentredString(
        510,
        table_y + 7,
        "AMOUNT"
    )

    # Header separators

    pdf.setStrokeColor(BLACK)

    pdf.line(
        description_end,
        table_y,
        description_end,
        table_y + 22
    )

    pdf.line(
        qty_end,
        table_y,
        qty_end,
        table_y + 22
    )

    pdf.line(
        unit_end,
        table_y,
        unit_end,
        table_y + 22
    )

    pdf.line(
        price_end,
        table_y,
        price_end,
        table_y + 22
    )

    table_y -= 20

    # ========================================================
    # ITEMS
    # ========================================================

    for item in items:

        description = str(
            item["description"] or ""
        )

        quantity = float(
            item["quantity"] or 0
        )

        unit = str(
            item["unit"] or ""
        )

        unit_price = float(
            item["unit_price"] or 0
        )

        amount = float(
            item["amount"] or 0
        )

        pdf.setFillColor(BLACK)

        pdf.setFont(
            "Helvetica",
            8
        )

        # Description

        pdf.drawString(
            50,
            table_y + 5,
            description[:39]
        )

        # Quantity

        pdf.drawCentredString(
            310,
            table_y + 5,
            f"{quantity:g}"
        )

        # Unit

        pdf.drawCentredString(
            360,
            table_y + 5,
            unit[:10]
        )

        # Unit price

        pdf.drawRightString(
            455,
            table_y + 5,
            money(unit_price)
        )

        # Amount

        pdf.drawRightString(
            545,
            table_y + 5,
            money(amount)
        )

        # Row lines

        pdf.setStrokeColor(
            LIGHT_GREY
        )

        pdf.line(
            table_left,
            table_y,
            table_right,
            table_y
        )

        pdf.line(
            description_end,
            table_y,
            description_end,
            table_y + 20
        )

        pdf.line(
            qty_end,
            table_y,
            qty_end,
            table_y + 20
        )

        pdf.line(
            unit_end,
            table_y,
            unit_end,
            table_y + 20
        )

        pdf.line(
            price_end,
            table_y,
            price_end,
            table_y + 20
        )

        table_y -= 20

    # ========================================================
    # EMPTY TABLE ROWS
    # ========================================================

    minimum_rows = 7

    empty_rows = max(
        0,
        minimum_rows - len(items)
    )

    for _ in range(empty_rows):

        pdf.setStrokeColor(
            LIGHT_GREY
        )

        pdf.line(
            table_left,
            table_y,
            table_right,
            table_y
        )

        pdf.line(
            description_end,
            table_y,
            description_end,
            table_y + 20
        )

        pdf.line(
            qty_end,
            table_y,
            qty_end,
            table_y + 20
        )

        pdf.line(
            unit_end,
            table_y,
            unit_end,
            table_y + 20
        )

        pdf.line(
            price_end,
            table_y,
            price_end,
            table_y + 20
        )

        table_y -= 20

    pdf.setStrokeColor(BLACK)

    pdf.line(
        table_left,
        table_y,
        table_right,
        table_y
    )

    # ========================================================
    # TOTALS - NO VAT
    # ========================================================

    subtotal = float(
        invoice["subtotal"] or 0
    )

    other_amount = float(
        invoice["other_amount"] or 0
    )

    total = (
        subtotal
        + other_amount
    )

    totals_y = table_y - 25

    if totals_y < 190:
        totals_y = 190

    totals_x = 380

    # --------------------------------------------------------
    # SUBTOTAL
    # --------------------------------------------------------

    pdf.setFillColor(BLACK)

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        totals_x,
        totals_y,
        "SUBTOTAL"
    )

    pdf.drawRightString(
        545,
        totals_y,
        money(subtotal)
    )

    totals_y -= 18

    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    if other_amount != 0:

        pdf.drawString(
            totals_x,
            totals_y,
            "OTHER"
        )

        pdf.drawRightString(
            545,
            totals_y,
            money(other_amount)
        )

        totals_y -= 18

    # --------------------------------------------------------
    # TOTAL DUE
    # --------------------------------------------------------

    pdf.setStrokeColor(ORANGE)

    pdf.line(
        totals_x,
        totals_y + 10,
        545,
        totals_y + 10
    )

    pdf.setFillColor(ORANGE)

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        totals_x,
        totals_y - 3,
        "TOTAL DUE"
    )

    pdf.drawRightString(
        545,
        totals_y - 3,
        money(total)
    )

    # ========================================================
    # BANKING / PAYMENT INFORMATION
    # ========================================================

    payment_y = 170

    pdf.setFillColor(NAVY)

    pdf.rect(
        40,
        payment_y,
        300,
        18,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(WHITE)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        45,
        payment_y + 5,
        "PAYMENT INFORMATION"
    )

    # --------------------------------------------------------
    # BANK
    # --------------------------------------------------------

    pdf.setFillColor(BLACK)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        45,
        payment_y - 16,
        "Bank:"
    )

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        115,
        payment_y - 16,
        BANK_NAME
    )

    # --------------------------------------------------------
    # ACCOUNT NUMBER
    # --------------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        45,
        payment_y - 31,
        "Account No:"
    )

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        115,
        payment_y - 31,
        ACCOUNT_NUMBER
    )

    # --------------------------------------------------------
    # BRANCH CODE
    # --------------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        45,
        payment_y - 46,
        "Branch Code:"
    )

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        115,
        payment_y - 46,
        BRANCH_CODE
    )

    # --------------------------------------------------------
    # REFERENCE
    # --------------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        45,
        payment_y - 61,
        "Reference:"
    )

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        115,
        payment_y - 61,
        invoice_number
    )

    # --------------------------------------------------------
    # PAYMENT NOTE
    # --------------------------------------------------------

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        45,
        payment_y - 81,
        "Please use the invoice number as your payment reference."
    )

    # ========================================================
    # FOOTER
    # ========================================================

    pdf.setStrokeColor(ORANGE)

    pdf.line(
        40,
        35,
        PAGE_WIDTH - 40,
        35
    )

    pdf.setFillColor(ORANGE)

    pdf.setFont(
        "Helvetica-Bold",
        10
    )

    pdf.drawCentredString(
        PAGE_WIDTH / 2,
        18,
        "Thank You For Your Business!"
    )

    # ========================================================
    # SAVE PDF
    # ========================================================

    pdf.save()

    print()
    print("=" * 55)
    print("INVOICE PDF CREATED SUCCESSFULLY")
    print("=" * 55)

    print()
    print("Invoice:")
    print(invoice_number)

    print()
    print("Customer:")
    print(
        invoice["customer_name"] or ""
    )

    print()
    print("Invoice date:")
    print(
        invoice["invoice_date"]
    )

    print()
    print("Total Due:")
    print(
        money(total)
    )

    print()
    print("Bank:")
    print(BANK_NAME)

    print()
    print("Account:")
    print(ACCOUNT_NUMBER)

    print()
    print("Branch Code:")
    print(BRANCH_CODE)

    print()
    print("Saved to:")
    print(output_file)

    print()
    print("=" * 55)

    return output_file


# ============================================================
# MAIN
# ============================================================

def main():

    invoice_id = choose_invoice()

    if invoice_id is None:
        return

    print()
    print("Generating invoice PDF...")

    generate_invoice_pdf(
        invoice_id
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()