from datetime import date

from database import get_connection


# ============================================================
# JANW ENTERPRISE - INVOICE SYSTEM
# ============================================================


def get_number(message, default=None):
    """
    Ask for a number and keep asking until
    a valid positive number or zero is entered.
    """

    while True:

        value = input(message).strip()

        if value == "" and default is not None:
            return default

        try:
            number = float(value)

            if number < 0:
                print("Please enter 0 or a positive number.")
                continue

            return number

        except ValueError:
            print("Please enter a valid number.")


# ============================================================
# CREATE INVOICE
# ============================================================


def create_invoice():

    print()
    print("=" * 50)
    print("CREATE NEW INVOICE")
    print("=" * 50)

    # --------------------------------------------------------
    # CUSTOMER DETAILS
    # --------------------------------------------------------

    customer_name = input(
        "Customer name: "
    ).strip()

    if not customer_name:

        print()
        print("Customer name is required.")

        return None

    company = input(
        "Company name (optional): "
    ).strip()

    address = input(
        "Customer address: "
    ).strip()

    phone = input(
        "Phone number: "
    ).strip()

    email = input(
        "Email address: "
    ).strip()

    prepared_by = input(
        "Prepared by: "
    ).strip()

    # --------------------------------------------------------
    # INVOICE DATE
    # --------------------------------------------------------

    invoice_date = date.today()

    print()
    print(
        "Invoice date:",
        invoice_date.isoformat()
    )

    # --------------------------------------------------------
    # OPEN DATABASE
    # --------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # SAVE CUSTOMER
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO customers (
                name,
                company,
                address,
                phone,
                email
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            customer_name,
            company,
            address,
            phone,
            email
        ))

        customer_id = cursor.lastrowid

        customer_number = (
            f"CUST-{customer_id:04d}"
        )

        cursor.execute("""
            UPDATE customers
            SET customer_number = ?
            WHERE id = ?
        """, (
            customer_number,
            customer_id
        ))

        # ----------------------------------------------------
        # CREATE INVOICE NUMBER
        # ----------------------------------------------------

        cursor.execute("""
            SELECT MAX(id)
            FROM invoices
        """)

        result = cursor.fetchone()[0]

        if result is None:
            next_number = 1
        else:
            next_number = result + 1

        current_year = invoice_date.year

        invoice_number = (
            f"INV-{current_year}-{next_number:04d}"
        )

        # ----------------------------------------------------
        # ADD INVOICE ITEMS
        # ----------------------------------------------------

        items = []

        print()
        print("ADD INVOICE ITEMS")
        print("-" * 50)

        while True:

            print()

            description = input(
                "Description: "
            ).strip()

            if not description:

                print(
                    "Description cannot be empty."
                )

                continue

            # ------------------------------------------------
            # QUANTITY
            # ------------------------------------------------

            quantity = get_number(
                "Quantity [1]: ",
                default=1
            )

            # ------------------------------------------------
            # UNIT SELECTION BUTTONS
            # ------------------------------------------------

            # Select a unit using the numbered button-style menu.
            # Option 9 allows a custom unit to be entered.
            unit_options = [
                ("1", "Each"),
                ("2", "m"),
                ("3", "m²"),
                ("4", "m³"),
                ("5", "kg"),
                ("6", "L"),
                ("7", "Hour"),
                ("8", "Day"),
            ]

            print("\nUNIT OF MEASUREMENT")
            print("[1] Each   [2] m      [3] m²   [4] m³")
            print("[5] kg     [6] L      [7] Hour  [8] Day")
            print("[9] Custom")

            while True:
                unit_choice = input("Select unit: ").strip()

                selected = dict(unit_options).get(unit_choice)
                if selected:
                    unit = selected
                    break

                if unit_choice == "9":
                    unit = input("Enter custom unit: ").strip()
                    if unit:
                        break

                print("Please select one of the unit buttons [1-9].")

            # ------------------------------------------------
            # UNIT PRICE
            # ------------------------------------------------

            unit_price = get_number(
                "Unit price (R): "
            )

            # ------------------------------------------------
            # ITEM TOTAL
            # ------------------------------------------------

            amount = (
                quantity * unit_price
            )

            items.append({
                "description": description,
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "amount": amount
            })

            print()

            if unit:

                print(
                    f"{quantity:g} {unit} x "
                    f"R {unit_price:,.2f}"
                )

            print(
                f"Amount: R {amount:,.2f}"
            )

            # ------------------------------------------------
            # ANOTHER ITEM?
            # ------------------------------------------------

            another = input(
                "\nAdd another item? (Y/N): "
            ).strip().lower()

            if another != "y":
                break

        # ----------------------------------------------------
        # SUBTOTAL
        # ----------------------------------------------------

        subtotal = sum(
            item["amount"]
            for item in items
        )

        print()
        print("-" * 50)

        print(
            f"SUBTOTAL: R {subtotal:,.2f}"
        )

        # ----------------------------------------------------
        # OTHER COSTS
        # ----------------------------------------------------

        other_amount = get_number(
            "Other amount [0]: R ",
            default=0
        )

        # ----------------------------------------------------
        # NO VAT
        # ----------------------------------------------------

        tax_rate = 0
        tax_amount = 0

        # ----------------------------------------------------
        # TOTAL
        # ----------------------------------------------------

        total = (
            subtotal
            + other_amount
        )

        print()
        print("=" * 50)

        print(
            f"TOTAL DUE: R {total:,.2f}"
        )

        print("=" * 50)

        # ----------------------------------------------------
        # SAVE INVOICE
        # ----------------------------------------------------
        #
        # due_date is stored as NULL because invoices
        # no longer use a due date.
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO invoices (
                invoice_number,
                customer_id,
                invoice_date,
                due_date,
                prepared_by,
                subtotal,
                tax_rate,
                tax_amount,
                other_amount,
                total,
                status,
                source_quote_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_number,
            customer_id,
            invoice_date.isoformat(),
            None,
            prepared_by,
            subtotal,
            tax_rate,
            tax_amount,
            other_amount,
            total,
            "UNPAID",
            None
        ))

        invoice_id = cursor.lastrowid

        # ----------------------------------------------------
        # SAVE ITEMS
        # ----------------------------------------------------

        for item in items:

            cursor.execute("""
                INSERT INTO invoice_items (
                    invoice_id,
                    description,
                    quantity,
                    unit,
                    unit_price,
                    taxable,
                    amount
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                item["description"],
                item["quantity"],
                item["unit"],
                item["unit_price"],
                0,
                item["amount"]
            ))

        # ----------------------------------------------------
        # SAVE DATABASE
        # ----------------------------------------------------

        connection.commit()

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print()
        print("=" * 50)
        print("INVOICE SAVED SUCCESSFULLY")
        print("=" * 50)

        print()
        print(
            "Invoice number:",
            invoice_number
        )

        print(
            "Customer:",
            customer_name
        )

        print(
            "Invoice date:",
            invoice_date.isoformat()
        )

        print(
            f"Subtotal: R {subtotal:,.2f}"
        )

        if other_amount > 0:

            print(
                f"Other: R {other_amount:,.2f}"
            )

        print(
            f"Total Due: R {total:,.2f}"
        )

        print()

        return invoice_id

    # --------------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------------

    except Exception as error:

        connection.rollback()

        print()
        print("=" * 50)
        print("INVOICE COULD NOT BE SAVED")
        print("=" * 50)

        print()
        print("Error:")
        print(error)

        return None

    finally:

        connection.close()