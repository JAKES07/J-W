import sys
from pathlib import Path

# ============================================================
# JANW ENTERPRISE - QUOTATION PDF GENERATOR
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
from config import QUOTATIONS_DIR, LETTERHEAD_FILE


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
# MONEY FORMAT
# ============================================================

def money(value):

    if value is None:
        value = 0

    return f"R {float(value):,.2f}"


# ============================================================
# SHOW SAVED QUOTATIONS
# ============================================================

def show_quotations():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            q.id,
            q.quote_number,
            q.quote_date,
            q.total,
            c.name AS customer_name

        FROM quotations q

        LEFT JOIN customers c
            ON q.customer_id = c.id

        ORDER BY q.id DESC
    """)

    quotations = cursor.fetchall()

    connection.close()

    print()
    print("=" * 65)
    print("JANW ENTERPRISE - QUOTATION PDF GENERATOR")
    print("=" * 65)

    if not quotations:

        print()
        print("No quotations have been saved yet.")
        print()

        return []

    print()
    print("SAVED QUOTATIONS")
    print("-" * 65)

    for quote in quotations:

        print()

        print(
            f"ID: {quote['id']}  |  "
            f"{quote['quote_number']}"
        )

        print(
            f"Customer: "
            f"{quote['customer_name'] or 'No customer'}"
        )

        print(
            f"Date: {quote['quote_date']}  |  "
            f"Total: {money(quote['total'])}"
        )

        print("-" * 65)

    return quotations


# ============================================================
# CHOOSE QUOTATION
# ============================================================

def choose_quotation():

    quotations = show_quotations()

    if not quotations:
        return None

    valid_ids = {
        quote["id"]
        for quote in quotations
    }

    while True:

        print()

        choice = input(
            "Enter quotation ID to generate PDF "
            "(0 to cancel): "
        ).strip()

        if choice == "0":

            print()
            print("PDF generation cancelled.")

            return None

        try:

            quotation_id = int(choice)

        except ValueError:

            print()
            print("Please enter a quotation ID number.")

            continue

        if quotation_id not in valid_ids:

            print()
            print(
                "That quotation ID does not exist."
            )

            continue

        return quotation_id


# ============================================================
# GENERATE QUOTATION PDF
# ============================================================

def generate_quote_pdf(quotation_id):

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # GET QUOTATION
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            q.*,

            c.customer_number,
            c.name AS customer_name,
            c.company AS customer_company,
            c.address AS customer_address,
            c.phone AS customer_phone,
            c.email AS customer_email

        FROM quotations q

        LEFT JOIN customers c
            ON q.customer_id = c.id

        WHERE q.id = ?
    """, (quotation_id,))

    quote = cursor.fetchone()

    if quote is None:

        connection.close()

        print()
        print("=" * 50)
        print("QUOTATION NOT FOUND")
        print("=" * 50)

        return None

    # --------------------------------------------------------
    # GET ITEMS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            description,
            quantity,
            unit,
            unit_price,
            amount

        FROM quotation_items

        WHERE quotation_id = ?

        ORDER BY id
    """, (quotation_id,))

    items = cursor.fetchall()

    connection.close()

    # --------------------------------------------------------
    # OUTPUT FILE
    # --------------------------------------------------------

    QUOTATIONS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    quote_number = quote["quote_number"]

    output_file = (
        QUOTATIONS_DIR
        / f"{quote_number}.pdf"
    )

    # --------------------------------------------------------
    # CREATE PDF
    # --------------------------------------------------------

    pdf = canvas.Canvas(
        str(output_file),
        pagesize=A4
    )

    pdf.setTitle(
        f"JANW Enterprise - {quote_number}"
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

    # Orange separator

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
        "QUOTATION"
    )

    # ========================================================
    # PREPARED BY
    # ========================================================

    prepared_by = (
        quote["prepared_by"] or ""
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
        quote["customer_name"],
        quote["customer_company"],
        quote["customer_address"],
        quote["customer_phone"],
        quote["customer_email"]
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
    # QUOTATION INFORMATION
    # ========================================================

    info_x = 365
    info_y = PAGE_HEIGHT - 250

    information = [
        (
            "DATE",
            quote["quote_date"]
        ),
        (
            "QUOTE #",
            quote["quote_number"]
        ),
        (
            "CUSTOMER ID",
            quote["customer_number"]
        ),
        (
            "VALID UNTIL",
            quote["valid_until"]
        )
    ]

    for label, value in information:

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
    # HEADER BACKGROUND
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

    # --------------------------------------------------------
    # HEADER TEXT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # HEADER SEPARATORS
    # --------------------------------------------------------

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

        # Row line

        pdf.setStrokeColor(
            LIGHT_GREY
        )

        pdf.line(
            table_left,
            table_y,
            table_right,
            table_y
        )

        # Vertical column lines

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
        quote["subtotal"] or 0
    )

    other_amount = float(
        quote["other_amount"] or 0
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
    # TERMS AND CONDITIONS
    # ========================================================

    terms_y = 160

    pdf.setFillColor(NAVY)

    pdf.rect(
        40,
        terms_y,
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
        terms_y + 5,
        "TERMS AND CONDITIONS"
    )

    pdf.setFillColor(BLACK)

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        45,
        terms_y - 15,
        "1. This quotation is valid for 30 days from the quotation date."
    )

    pdf.drawString(
        45,
        terms_y - 29,
        "2. Work will commence after receipt of a 50% deposit of the quoted amount."
    )

    pdf.drawString(
        45,
        terms_y - 43,
        "3. Additional work may require a revised quotation."
    )

    # ========================================================
    # CUSTOMER ACCEPTANCE
    # ========================================================

    pdf.setFillColor(ORANGE)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        45,
        terms_y - 65,
        "Customer Acceptance"
    )

    pdf.setFillColor(BLACK)

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        45,
        terms_y - 83,
        "Signature: ______________________________"
    )

    pdf.drawString(
        45,
        terms_y - 99,
        "Print Name: _____________________________"
    )

    # ========================================================
    # FOOTER
    # ========================================================

    pdf.setStrokeColor(ORANGE)

    pdf.line(
        40,
        55,
        PAGE_WIDTH - 40,
        55
    )

    pdf.setFillColor(ORANGE)

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawCentredString(
        PAGE_WIDTH / 2,
        35,
        "Thank You For Your Business!"
    )

    # ========================================================
    # SAVE
    # ========================================================

    pdf.save()

    print()
    print("=" * 55)
    print("PDF CREATED SUCCESSFULLY")
    print("=" * 55)

    print()
    print("Quotation:")
    print(quote_number)

    print()
    print("Customer:")
    print(
        quote["customer_name"] or ""
    )

    print()
    print("Total Due:")
    print(money(total))

    print()
    print("Saved to:")
    print(output_file)

    print()
    print("=" * 55)

    return output_file


# ============================================================
# MAIN PDF MENU
# ============================================================

def main():

    quotation_id = choose_quotation()

    if quotation_id is None:
        return

    print()
    print("Generating quotation PDF...")

    generate_quote_pdf(
        quotation_id
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()