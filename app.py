from flask import Flask, render_template, request, send_file
import mysql.connector
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io
import os

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME"),
    "port": int(os.environ.get("DB_PORT", 3306))
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/save", methods=["POST"])
def save():
    emp_id = request.form["emp_id"]
    name = request.form["name"]
    mobile = request.form["mobile"]
    basic = float(request.form["basic_salary"])
    allowance = float(request.form["allowance"])
    deduction = float(request.form["deduction"])
    net_salary = basic + allowance - deduction
    month = int(request.form["month"])
    year = int(request.form["year"])

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO salary_records (emp_id, name, mobile, month, year, basic_salary, allowance, deduction, net_salary)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (emp_id, name, mobile, month, year, basic, allowance, deduction, net_salary))
    conn.commit()
    conn.close()
    return "✅ Data Saved!"

@app.route("/report/excel/<int:year>/<int:month>")
def report_excel(year, month):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT emp_id, name, mobile, basic_salary, allowance, deduction, net_salary
        FROM salary_records WHERE month=%s AND year=%s
    """, (month, year))
    rows = cursor.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = f"Salary_{month}_{year}"
    ws.append(["ID","Name","Mobile","Basic","Allowance","Deduction","Net Salary"])
    for row in rows:
        ws.append(row)

    file_stream = io.BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    return send_file(file_stream, as_attachment=True,
                     download_name=f"salary_report_{year}_{month}.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/report/pdf/<int:year>/<int:month>")
def report_pdf(year, month):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT emp_id, name, mobile, basic_salary, allowance, deduction, net_salary
        FROM salary_records WHERE month=%s AND year=%s
    """, (month, year))
    rows = cursor.fetchall()
    conn.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    data = [["ID","Name","Mobile","Basic","Allowance","Deduction","Net Salary"]] + [list(r) for r in rows]
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.gray),
        ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
        ("GRID",(0,0),(-1,-1),1,colors.black)
    ]))
    doc.build([table])
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f"salary_report_{year}_{month}.pdf",
                     mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
