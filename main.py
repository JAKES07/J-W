from database import create_database
from modules.quotations import create_quotation
from modules.invoices import create_invoice


def show_menu():

    print()
    print("=" * 45)
    print("        JANW ENTERPRISE (PTY) LTD")
    print("=" * 45)

    print()
    print("1. CREATE QUOTATION")
    print("2. CREATE INVOICE")
    print()
    print("0. EXIT")


def main():

    # Make sure the database exists
    create_database()

    while True:

        show_menu()

        choice = input(
            "\nEnter choice: "
        ).strip()

        if choice == "1":

            create_quotation()

        elif choice == "2":

            create_invoice()

        elif choice == "0":

            print()
            print("JANW Enterprise system closed.")

            break

        else:

            print()
            print("Invalid option. Please choose 0, 1 or 2.")


if __name__ == "__main__":
    main()