from database import get_connection


def create_customer():
    print("\n" + "=" * 45)
    print("CREATE CUSTOMER")
    print("=" * 45)

    name = input("Customer name: ").strip()

    if not name:
        print("Customer name cannot be empty.")
        return None

    company = input("Company name (optional): ").strip()
    address = input("Address: ").strip()
    phone = input("Phone number: ").strip()
    email = input("Email address: ").strip()

    connection = get_connection()
    cursor = connection.cursor()

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
        name,
        company,
        address,
        phone,
        email
    ))

    customer_id = cursor.lastrowid

    customer_number = f"CUST-{customer_id:04d}"

    cursor.execute("""
        UPDATE customers
        SET customer_number = ?
        WHERE id = ?
    """, (customer_number, customer_id))

    connection.commit()
    connection.close()

    print()
    print("Customer saved successfully.")
    print("Customer number:", customer_number)

    return customer_id