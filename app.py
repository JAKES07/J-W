from pathlib import Path
from flask import Flask, render_template_string, send_file, abort
from config import (
    COMPANY_NAME,
    SLOGAN,
    QUOTATIONS_DIR,
    INVOICES_DIR,
    DEFAULT_QUOTE_VALID_DAYS,
)
from database import create_database, get_connection

app = Flask(__name__)

# Make sure the SQLite structure exists when the service starts.
create_database()

HTML = """
<!doctype html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ company }}</title>
<style>
body{font-family:Arial,sans-serif;margin:0;background:#f3f4f6;color:#172033}
header{background:#0b1e33;color:white;padding:24px}
header h1{margin:0 0 6px}
main{max-width:1000px;margin:24px auto;padding:0 16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.card{background:white;border-radius:12px;padding:20px;box-shadow:0 2px 10px #0001}
.number{font-size:32px;font-weight:bold}
a{color:#0b5ed7;text-decoration:none}
table{width:100%;border-collapse:collapse;background:white;margin-top:20px}
th,td{padding:10px;border-bottom:1px solid #ddd;text-align:left}
.small{color:#667085}
</style>
</head>
<body>
<header>
<h1>{{ company }}</h1>
<div>{{ slogan }}</div>
</header>
<main>
<div class="cards">
<div class="card"><div class="small">Customers</div><div class="number">{{ customers }}</div></div>
<div class="card"><div class="small">Quotations</div><div class="number">{{ quotations }}</div></div>
<div class="card"><div class="small">Invoices</div><div class="number">{{ invoices }}</div></div>
<div class="card"><div class="small">Quote validity</div><div class="number">{{ valid_days }} days</div></div>
</div>

<h2>Recent quotations</h2>
<table>
<tr><th>Quote</th><th>Date</th><th>Customer</th><th>Total</th><th>PDF</th></tr>
{% for q in quote_rows %}
<tr>
<td>{{ q["quote_number"] }}</td>
<td>{{ q["quote_date"] }}</td>
<td>{{ q["customer_name"] or "" }}</td>
<td>R {{ "%.2f"|format(q["total"] or 0) }}</td>
<td><a href="/documents/quotation/{{ q["quote_number"] }}">Open PDF</a></td>
</tr>
{% else %}
<tr><td colspan="5">No quotations yet.</td></tr>
{% endfor %}
</table>

<h2>Recent invoices</h2>
<table>
<tr><th>Invoice</th><th>Date</th><th>Customer</th><th>Total</th><th>PDF</th></tr>
{% for i in invoice_rows %}
<tr>
<td>{{ i["invoice_number"] }}</td>
<td>{{ i["invoice_date"] }}</td>
<td>{{ i["customer_name"] or "" }}</td>
<td>R {{ "%.2f"|format(i["total"] or 0) }}</td>
<td><a href="/documents/invoice/{{ i["invoice_number"] }}">Open PDF</a></td>
</tr>
{% else %}
<tr><td colspan="5">No invoices yet.</td></tr>
{% endfor %}
</table>
</main>
</body>
</html>
"""

@app.get("/")
def dashboard():
    connection = get_connection()
    cursor = connection.cursor()

    customers = cursor.execute(
        "SELECT COUNT(*) FROM customers"
    ).fetchone()[0]

    quotations = cursor.execute(
        "SELECT COUNT(*) FROM quotations"
    ).fetchone()[0]

    invoices = cursor.execute(
        "SELECT COUNT(*) FROM invoices"
    ).fetchone()[0]

    quote_rows = cursor.execute(
        """
        SELECT q.quote_number,q.quote_date,q.total,c.name AS customer_name
        FROM quotations q
        LEFT JOIN customers c ON q.customer_id=c.id
        ORDER BY q.id DESC
        LIMIT 20
        """
    ).fetchall()

    invoice_rows = cursor.execute(
        """
        SELECT i.invoice_number,i.invoice_date,i.total,c.name AS customer_name
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id=c.id
        ORDER BY i.id DESC
        LIMIT 20
        """
    ).fetchall()

    connection.close()

    return render_template_string(
        HTML,
        company=COMPANY_NAME,
        slogan=SLOGAN,
        customers=customers,
        quotations=quotations,
        invoices=invoices,
        valid_days=DEFAULT_QUOTE_VALID_DAYS,
        quote_rows=quote_rows,
        invoice_rows=invoice_rows,
    )

@app.get("/documents/quotation/<quote_number>")
def quotation_pdf(quote_number):
    file_path = Path(QUOTATIONS_DIR) / f"{quote_number}.pdf"
    if not file_path.is_file():
        abort(404)
    return send_file(file_path, mimetype="application/pdf")

@app.get("/documents/invoice/<invoice_number>")
def invoice_pdf(invoice_number):
    file_path = Path(INVOICES_DIR) / f"{invoice_number}.pdf"
    if not file_path.is_file():
        abort(404)
    return send_file(file_path, mimetype="application/pdf")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
