from database import get_connection, create_database

# THIS IS A ONE-TIME TEST-DATA RESET.
# It removes all customers, quotations, invoices and their items.
# It does not remove the database structure.

create_database()
connection = get_connection()
cursor = connection.cursor()

cursor.execute("DELETE FROM quotation_items")
cursor.execute("DELETE FROM invoice_items")
cursor.execute("DELETE FROM quotations")
cursor.execute("DELETE FROM invoices")
cursor.execute("DELETE FROM customers")

connection.commit()
connection.close()

print("JANW test data cleared.")
print("Customers: 0")
print("Quotations: 0")
print("Invoices: 0")
