import os
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, request, redirect, url_for, render_template_string, send_file, flash
from database import get_connection, create_database
from config import (
    COMPANY_NAME, SLOGAN, QUOTATIONS_DIR, INVOICES_DIR,
    DEFAULT_QUOTE_VALID_DAYS
)

from pdf.quote_pdf import generate_quote_pdf
from pdf.invoice_pdf import generate_invoice_pdf

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "janw-private-secret")

create_database()

UNITS = ["Each", "m", "m²", "m³", "kg", "L", "Hour", "Day"]

BASE_STYLE = """
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,sans-serif;background:#f3f4f6;color:#172033}
header{background:#0b1e33;color:#fff;padding:18px 20px}
header h1{margin:0;font-size:22px}
header p{margin:5px 0 0;font-size:13px}
nav{background:#fff;padding:12px 20px;box-shadow:0 2px 8px #0001}
nav a{margin-right:10px;text-decoration:none;color:#0b5ed7;font-weight:bold}
main{max-width:1100px;margin:20px auto;padding:0 14px}
.card{background:#fff;border-radius:12px;padding:18px;margin-bottom:18px;box-shadow:0 2px 10px #0001}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.stat{background:#fff;padding:18px;border-radius:12px;box-shadow:0 2px 8px #0001}
.stat b{font-size:28px;display:block}
label{display:block;font-weight:bold;margin-top:10px}
input,textarea,select{width:100%;padding:11px;border:1px solid #ccd3dd;border-radius:8px;font-size:15px}
textarea{min-height:80px}
button,.button{border:0;border-radius:8px;padding:11px 15px;background:#0b5ed7;color:#fff;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block}
button.secondary,.button.secondary{background:#475467}
button.danger{background:#b42318}
.item{border:1px solid #d8dee8;border-radius:10px;padding:14px;margin:12px 0;background:#fafbfc}
.units{display:flex;flex-wrap:wrap;gap:7px;margin-top:7px}
.unit{background:#eef2f6;color:#172033;border:1px solid #c9d2dd;padding:9px 12px;border-radius:8px}
.unit.selected{background:#0b5ed7;color:white}
.row{display:grid;grid-template-columns:2fr 1fr 1fr 1fr auto;gap:8px;align-items:end}
@media(max-width:700px){.row{grid-template-columns:1fr}.grid{grid-template-columns:1fr 1fr}}
table{width:100%;border-collapse:collapse;background:#fff}
th,td{padding:9px;border-bottom:1px solid #e1e5ea;text-align:left}
.actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.success{background:#ecfdf3;color:#067647;padding:10px;border-radius:8px;margin-bottom:12px}
.error{background:#fef3f2;color:#b42318;padding:10px;border-radius:8px;margin-bottom:12px}
.total{text-align:right;font-size:20px;font-weight:bold;margin-top:15px}
</style>
"""

HEADER = """
<header>
<h1>{{ company }}</h1>
<p>{{ slogan }}</p>
</header>
<nav>
<a href="/">Dashboard</a>
<a href="/quotation/new">New Quotation</a>
<a href="/invoice/new">New Invoice</a>
</nav>
"""

FORM_JS = r"""
<script>
function addItem(){
  const box=document.getElementById('items');
  const first=box.querySelector('.item');
  const clone=first.cloneNode(true);
  clone.querySelectorAll('input').forEach(i=>i.value='');
  clone.querySelector('input[name="quantity[]"]').value='1';
  clone.querySelector('input[name="unit[]"]').value='Each';
  clone.querySelectorAll('.unit').forEach(b=>b.classList.remove('selected'));
  clone.querySelector('.unit[data-unit="Each"]').classList.add('selected');
  box.appendChild(clone);
}
function removeItem(btn){
  const items=document.querySelectorAll('.item');
  if(items.length>1) btn.closest('.item').remove();
}
function chooseUnit(btn){
  const item=btn.closest('.item');
  item.querySelectorAll('.unit').forEach(b=>b.classList.remove('selected'));
  btn.classList.add('selected');
  item.querySelector('input[name="unit[]"]').value=btn.dataset.unit;
}
function calculate(){
  let subtotal=0;
  document.querySelectorAll('.item').forEach(item=>{
    const q=parseFloat(item.querySelector('input[name="quantity[]"]').value)||0;
    const p=parseFloat(item.querySelector('input[name="unit_price[]"]').value)||0;
    subtotal+=q*p;
    const amount=item.querySelector('.amount');
    if(amount) amount.textContent='R '+(q*p).toFixed(2);
  });
  const other=parseFloat(document.querySelector('input[name="other_amount"]').value)||0;
  const total=subtotal+other;
  document.getElementById('subtotal').textContent='R '+subtotal.toFixed(2);
  document.getElementById('total').textContent='R '+total.toFixed(2);
}
document.addEventListener('input',calculate);
document.addEventListener('click',e=>{
  if(e.target.classList.contains('unit')) chooseUnit(e.target);
});
</script>
"""

FORM_HTML = BASE_STYLE + HEADER + r"""
<main>
<div class="card">
<h2>{{ title }}</h2>
<p>All fields below are entered through the web page. No terminal input is required.</p>
<form method="post">
<h3>Customer Details</h3>
<div class="grid">
<div><label>Customer name *</label><input name="customer_name" required></div>
<div><label>Company</label><input name="company"></div>
<div><label>Phone</label><input name="phone"></div>
<div><label>Email</label><input name="email" type="email"></div>
</div>
<label>Address</label><textarea name="address"></textarea>
<label>Prepared by</label><input name="prepared_by">

<h3>Items</h3>
<div id="items">
<div class="item">
<div class="row">
<div><label>Description *</label><input name="description[]" required></div>
<div><label>Quantity</label><input name="quantity[]" type="number" min="0" step="any" value="1" required></div>
<div><label>Unit price (R)</label><input name="unit_price[]" type="number" min="0" step="0.01" value="0" required></div>
<div><label>Amount</label><div class="amount" style="padding:11px">R 0.00</div></div>
<div><button type="button" class="danger" onclick="removeItem(this)">Remove</button></div>
</div>
<label>Unit of measurement</label>
<input type="hidden" name="unit[]" value="Each">
<div class="units">
{% for u in units %}<button type="button" class="unit{% if u=='Each' %} selected{% endif %}" data-unit="{{ u }}">{{ u }}</button>{% endfor %}
</div>
</div>
</div>
<div class="actions">
<button type="button" class="secondary" onclick="addItem()">+ Add another item</button>
</div>
<label>Other amount (R)</label><input name="other_amount" type="number" min="0" step="0.01" value="0">
<div class="total">Subtotal: <span id="subtotal">R 0.00</span><br>Total: <span id="total">R 0.00</span></div>

{% if quote %}
<div class="success"><b>Quotation terms:</b> Valid for 30 days. Work will commence after receipt of a 50% deposit of the quoted amount.</div>
{% endif %}

<div class="actions">
<button type="submit">Create {{ document_word }}</button>
<a class="button secondary" href="/">Cancel</a>
</div>
</form>
</div>
</main>
""" + FORM_JS

DASHBOARD = BASE_STYLE + HEADER + r"""
<main>
{% with messages=get_flashed_messages(with_categories=true) %}
{% for category,msg in messages %}<div class="{{ category }}">{{ msg }}</div>{% endfor %}
{% endwith %}
<div class="grid">
<div class="stat">Customers<b>{{ customers }}</b></div>
<div class="stat">Quotations<b>{{ quotations }}</b></div>
<div class="stat">Invoices<b>{{ invoices }}</b></div>
<div class="stat">Quote validity<b>30 days</b></div>
</div>
<div class="card">
<div class="actions">
<a class="button" href="/quotation/new">+ Create Quotation</a>
<a class="button" href="/invoice/new">+ Create Invoice</a>
</div>
</div>
<div class="card">
<h2>Quotations</h2>
<table><tr><th>Quote</th><th>Date</th><th>Customer</th><th>Total</th><th>PDF</th></tr>
{% for q in quote_rows %}<tr><td>{{q.quote_number}}</td><td>{{q.quote_date}}</td><td>{{q.customer_name}}</td><td>R {{'%.2f'|format(q.total or 0)}}</td><td><a href="/documents/quotation/{{q.quote_number}}">Open PDF</a></td></tr>{% else %}<tr><td colspan="5">No quotations yet.</td></tr>{% endfor %}
</table>
</div>
<div class="card">
<h2>Invoices</h2>
<table><tr><th>Invoice</th><th>Date</th><th>Customer</th><th>Total</th><th>PDF</th></tr>
{% for i in invoice_rows %}<tr><td>{{i.invoice_number}}</td><td>{{i.invoice_date}}</td><td>{{i.customer_name}}</td><td>R {{'%.2f'|format(i.total or 0)}}</td><td><a href="/documents/invoice/{{i.invoice_number}}">Open PDF</a></td></tr>{% else %}<tr><td colspan="5">No invoices yet.</td></tr>{% endfor %}
</table>
</div>
</main>
"""

def save_document(kind, form):
    customer_name = form.get("customer_name","").strip()
    if not customer_name:
        raise ValueError("Customer name is required.")

    descriptions = form.getlist("description[]")
    quantities = form.getlist("quantity[]")
    units = form.getlist("unit[]")
    prices = form.getlist("unit_price[]")
    items = []

    for idx, desc in enumerate(descriptions):
        desc = desc.strip()
        if not desc:
            continue
        q = float(quantities[idx] or 0)
        p = float(prices[idx] or 0)
        unit = units[idx] if idx < len(units) else "Each"
        items.append({
            "description": desc,
            "quantity": q,
            "unit": unit,
            "unit_price": p,
            "amount": q*p
        })

    if not items:
        raise ValueError("Add at least one item.")

    other = float(form.get("other_amount") or 0)
    today = date.today()
    connection = get_connection()
    cur = connection.cursor()

    try:
        cur.execute("""INSERT INTO customers
            (name,company,address,phone,email)
            VALUES (?,?,?,?,?)""", (
            customer_name, form.get("company","").strip(),
            form.get("address","").strip(), form.get("phone","").strip(),
            form.get("email","").strip()
        ))
        customer_id = cur.lastrowid
        cur.execute("UPDATE customers SET customer_number=? WHERE id=?",
                    (f"CUST-{customer_id:04d}", customer_id))

        if kind == "quotation":
            row = cur.execute("SELECT MAX(id) FROM quotations").fetchone()
            number = (row[0] or 0) + 1
            doc_number = f"QT-{today.year}-{number:04d}"
            valid_until = today + timedelta(days=DEFAULT_QUOTE_VALID_DAYS)
            subtotal = sum(x["amount"] for x in items)
            total = subtotal + other
            cur.execute("""INSERT INTO quotations
                (quote_number,customer_id,quote_date,valid_until,prepared_by,
                 subtotal,tax_rate,tax_amount,other_amount,total,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
                doc_number, customer_id, today.isoformat(), valid_until.isoformat(),
                form.get("prepared_by","").strip(), subtotal, 0, 0, other, total, "DRAFT"
            ))
            doc_id = cur.lastrowid
            for x in items:
                cur.execute("""INSERT INTO quotation_items
                    (quotation_id,description,quantity,unit,unit_price,taxable,amount)
                    VALUES (?,?,?,?,?,?,?)""", (
                    doc_id,x["description"],x["quantity"],x["unit"],
                    x["unit_price"],0,x["amount"]
                ))
        else:
            row = cur.execute("SELECT MAX(id) FROM invoices").fetchone()
            number = (row[0] or 0) + 1
            doc_number = f"INV-{today.year}-{number:04d}"
            subtotal = sum(x["amount"] for x in items)
            total = subtotal + other
            cur.execute("""INSERT INTO invoices
                (invoice_number,customer_id,invoice_date,due_date,prepared_by,
                 subtotal,tax_rate,tax_amount,other_amount,total,status,source_quote_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
                doc_number,customer_id,today.isoformat(),None,
                form.get("prepared_by","").strip(),subtotal,0,0,other,total,"UNPAID",None
            ))
            doc_id = cur.lastrowid
            for x in items:
                cur.execute("""INSERT INTO invoice_items
                    (invoice_id,description,quantity,unit,unit_price,taxable,amount)
                    VALUES (?,?,?,?,?,?,?)""", (
                    doc_id,x["description"],x["quantity"],x["unit"],
                    x["unit_price"],0,x["amount"]
                ))

        connection.commit()

        # Use the project's existing PDF generators.
        if kind == "quotation":
            generate_quote_pdf(doc_id)
        else:
            generate_invoice_pdf(doc_id)

        return doc_number
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

@app.get("/")
def dashboard():
    c = get_connection()
    cur = c.cursor()
    customers = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    quotations = cur.execute("SELECT COUNT(*) FROM quotations").fetchone()[0]
    invoices = cur.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    quote_rows = cur.execute("""SELECT q.quote_number,q.quote_date,q.total,
        c.name AS customer_name FROM quotations q
        LEFT JOIN customers c ON q.customer_id=c.id ORDER BY q.id DESC""").fetchall()
    invoice_rows = cur.execute("""SELECT i.invoice_number,i.invoice_date,i.total,
        c.name AS customer_name FROM invoices i
        LEFT JOIN customers c ON i.customer_id=c.id ORDER BY i.id DESC""").fetchall()
    c.close()
    return render_template_string(DASHBOARD, company=COMPANY_NAME, slogan=SLOGAN,
        customers=customers, quotations=quotations, invoices=invoices,
        quote_rows=quote_rows, invoice_rows=invoice_rows)

@app.route("/quotation/new", methods=["GET","POST"])
def new_quotation():
    if request.method == "POST":
        try:
            number = save_document("quotation", request.form)
            flash(f"Quotation {number} created successfully.", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Could not create quotation: {e}", "error")
    return render_template_string(FORM_HTML, company=COMPANY_NAME, slogan=SLOGAN,
        title="Create New Quotation", document_word="Quotation", quote=True, units=UNITS)

@app.route("/invoice/new", methods=["GET","POST"])
def new_invoice():
    if request.method == "POST":
        try:
            number = save_document("invoice", request.form)
            flash(f"Invoice {number} created successfully.", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Could not create invoice: {e}", "error")
    return render_template_string(FORM_HTML, company=COMPANY_NAME, slogan=SLOGAN,
        title="Create New Invoice", document_word="Invoice", quote=False, units=UNITS)

@app.get("/documents/quotation/<quote_number>")
def quotation_pdf(quote_number):
    path = Path(QUOTATIONS_DIR) / f"{quote_number}.pdf"
    if not path.exists():
        return "Quotation PDF not found", 404
    return send_file(path, mimetype="application/pdf")

@app.get("/documents/invoice/<invoice_number>")
def invoice_pdf(invoice_number):
    path = Path(INVOICES_DIR) / f"{invoice_number}.pdf"
    if not path.exists():
        return "Invoice PDF not found", 404
    return send_file(path, mimetype="application/pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT","10000"))
    app.run(host="0.0.0.0", port=port)
