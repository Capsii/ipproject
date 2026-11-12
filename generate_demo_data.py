"""Generate a fictional, repeatable portfolio dataset for the chemist shop."""

import argparse
import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
import random

import mysql.connector

from db_config import DB_CONFIG


DATABASE_NAME = "ip_project2022"
PREFIX = "LARGEDEMO"
BATCH_PREFIX = PREFIX + "-BATCH-"
EMPLOYEE_PREFIX = PREFIX + "-EMP-"
CUSTOMER_PREFIX = PREFIX + "-CUST-"
RECEIPT_PREFIX = PREFIX + "-"
EXPENSE_PREFIX = PREFIX + "-EXPENSE-"

STOCK_BATCH_COUNT = 118
EMPLOYEE_COUNT = 18
CUSTOMER_COUNT = 90
BILL_COUNTS_BY_MONTH = [20, 24, 28, 32, 36, 40]
EXPENSES_PER_MONTH = 8
GST_RATE = Decimal("5.00")
MONEY_PLACES = Decimal("0.01")
RANDOM_SEED = 20261112

REQUIRED_TABLES = {
    "stocks",
    "staffinfo",
    "customerinformation",
    "bills",
    "bill_items",
    "expenses",
}

PRODUCTS = [
    ("Paracetamol 500 mg Tablet", 12, 45),
    ("Ibuprofen 200 mg Tablet", 18, 70),
    ("Cetirizine 10 mg Tablet", 10, 55),
    ("Calcium 500 mg Tablet", 35, 130),
    ("Antacid Chewable Tablet", 18, 85),
    ("ORS Electrolyte Sachet", 12, 60),
    ("Vitamin C 500 mg Tablet", 30, 120),
    ("Multivitamin Tablet", 45, 180),
    ("Iron Supplement Tablet", 30, 145),
    ("Demo Amoxicillin Capsule", 55, 190),
    ("Demo Probiotic Capsule", 65, 220),
    ("Cough Relief Syrup 100 ml", 70, 190),
    ("Oral Rehydration Syrup 200 ml", 80, 210),
    ("Calamine Lotion 100 ml", 55, 160),
    ("Skin Care Ointment 20 g", 65, 240),
    ("Antiseptic Liquid 100 ml", 35, 145),
    ("Hand Sanitizer 100 ml", 35, 110),
    ("Digital Thermometer", 180, 420),
    ("Cotton Bandage Roll", 25, 100),
    ("First Aid Dressing Pack", 80, 250),
    ("Heating Pad", 250, 650),
    ("Basic Glucose Meter", 550, 950),
]

MANUFACTURERS = [
    "Fictional Health Works",
    "SampleCare Laboratories",
    "DemoWell Remedies",
    "Northstar Sample Pharma",
    "BrightLeaf Health Products",
    "Placeholder Medical Supplies",
    "CedarHill Demo Labs",
    "Everyday Sample Healthcare",
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Anaya", "Arjun", "Diya", "Ishaan", "Kabir",
    "Kavya", "Meera", "Neel", "Nisha", "Priya", "Rohan", "Saanvi",
    "Tara", "Vihaan", "Yash", "Zoya",
]

LAST_NAMES = [
    "Sample", "Placeholder", "Demo", "Fiction", "Practice", "Example",
    "Mock", "Test", "Illustration", "Portfolio",
]

DESIGNATIONS = [
    ("Shop Assistant", 14000, 22000),
    ("Cashier", 15000, 24000),
    ("Inventory Assistant", 16000, 26000),
    ("Store Supervisor", 24000, 36000),
    ("Pharmacy Assistant", 18000, 30000),
]

EXPENSE_CATEGORIES = [
    "Rent",
    "Electricity",
    "Staff salaries",
    "Maintenance",
    "Packaging",
    "Stationery",
    "Shop supplies",
    "Local transport",
]


def round_money(value):
    return Decimal(value).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def get_recent_months(today):
    months = []
    current_index = today.year * 12 + today.month - 1
    for offset in range(5, -1, -1):
        year, month_index = divmod(current_index - offset, 12)
        month = month_index + 1
        first_day = date(year, month, 1)
        last_day_number = calendar.monthrange(year, month)[1]
        last_day = date(year, month, last_day_number)
        if year == today.year and month == today.month:
            last_day = today
        months.append((first_day, last_day))
    return months


def make_stock_batches(today, generator):
    batches = []
    low_stock_indexes = {20, 21, 22, 23, 70, 71}

    for index in range(STOCK_BATCH_COUNT):
        if index < 8:
            expiry_date = today - timedelta(days=generator.randint(1, 120))
        elif index < 20:
            expiry_date = today + timedelta(days=generator.randint(30, 60))
        else:
            expiry_date = today + timedelta(days=generator.randint(120, 1460))

        manufacture_date = expiry_date - timedelta(
            days=generator.randint(365, 1095)
        )
        product = PRODUCTS[index % len(PRODUCTS)]
        price = round_money(
            Decimal(generator.randint(product[1] * 100, product[2] * 100))
            / Decimal("100")
        )
        cost_fraction = Decimal(generator.randint(55, 78)) / Decimal("100")
        cost_price = round_money(price * cost_fraction)
        quantity = (
            generator.randint(4, 10)
            if index in low_stock_indexes
            else generator.randint(35, 180)
        )
        manufacturer_index = index % len(MANUFACTURERS)

        batches.append({
            "batch_no": "{}{:04d}".format(BATCH_PREFIX, index + 1),
            "expiry_date": expiry_date,
            "name": product[0],
            "initial_quantity": quantity,
            "remaining_quantity": quantity,
            "price": price,
            "cost_price": cost_price,
            "manufacturer": MANUFACTURERS[manufacturer_index],
            "manufacturer_phone": "000000{:04d}".format(manufacturer_index + 1),
            "manufacture_date": manufacture_date,
            "low_stock": index in low_stock_indexes,
        })

    return batches


def make_employees(generator):
    employees = []
    for index in range(EMPLOYEE_COUNT):
        first_name = FIRST_NAMES[index % len(FIRST_NAMES)]
        last_name = LAST_NAMES[(index // len(FIRST_NAMES)) % len(LAST_NAMES)]
        designation, minimum_salary, maximum_salary = DESIGNATIONS[
            index % len(DESIGNATIONS)
        ]
        employees.append((
            "{}{:04d}".format(EMPLOYEE_PREFIX, index + 1),
            "Demo {} {} {:02d}".format(first_name, last_name, index + 1),
            ["Female", "Male", "Not specified"][index % 3],
            generator.randint(20, 59),
            designation,
            Decimal(generator.randint(minimum_salary, maximum_salary)),
            "FAKE-EMP-{:04d}".format(index + 1),
            date.today() - timedelta(days=generator.randint(60, 3650)),
        ))
    return employees


def make_customers(generator):
    customers = []
    for index in range(CUSTOMER_COUNT):
        first_name = FIRST_NAMES[index % len(FIRST_NAMES)]
        last_name = LAST_NAMES[(index // len(FIRST_NAMES)) % len(LAST_NAMES)]
        customers.append({
            "id": "{}{:04d}".format(CUSTOMER_PREFIX, index + 1),
            "name": "Demo {} {} {:03d}".format(first_name, last_name, index + 1),
            "gender": ["Female", "Male", "Not specified"][index % 3],
            "age": generator.randint(18, 75),
            "phone": "000000{:04d}".format(index + 1),
            "doctor": "Dr Demo Sample {:02d}".format(index % 20 + 1),
            "address": "Demo House {}, Sample Nagar".format(index + 1),
            "reason": [
                "Fictional demonstration purchase",
                "Sample customer record",
                "Demo entry only",
            ][index % 3],
        })
    return customers


def make_bill_schedule(today, generator):
    schedule = []
    months = get_recent_months(today)
    for month_index, (first_day, last_day) in enumerate(months):
        days_in_range = max(1, (last_day - first_day).days + 1)
        for _ in range(BILL_COUNTS_BY_MONTH[month_index]):
            bill_date = first_day + timedelta(
                days=generator.randrange(days_in_range)
            )
            schedule.append((bill_date, month_index))
    schedule.sort(key=lambda item: item[0])
    return schedule


def make_expenses(today, generator):
    expenses = []
    expense_number = 0
    for first_day, last_day in get_recent_months(today):
        days_in_range = max(1, (last_day - first_day).days + 1)
        for category in EXPENSE_CATEGORIES:
            expense_number += 1
            if category == "Rent":
                amount = generator.randint(7000, 13000)
            elif category == "Electricity":
                amount = generator.randint(1800, 5200)
            elif category == "Staff salaries":
                amount = generator.randint(12000, 25000)
            elif category == "Maintenance":
                amount = generator.randint(500, 4500)
            elif category == "Packaging":
                amount = generator.randint(350, 2200)
            elif category == "Stationery":
                amount = generator.randint(200, 1300)
            elif category == "Shop supplies":
                amount = generator.randint(600, 3200)
            else:
                amount = generator.randint(250, 1600)

            expense_date = first_day + timedelta(
                days=generator.randrange(days_in_range)
            )
            expenses.append((
                expense_date,
                category,
                Decimal(amount),
                "{}{:04d}: fictional {} expense".format(
                    EXPENSE_PREFIX, expense_number, category
                ),
            ))
    return expenses


def check_database_and_schema(cursor):
    configured_database = DB_CONFIG.get("database")
    if configured_database != DATABASE_NAME:
        raise RuntimeError(
            "Refusing to generate data: db_config.py must target {}.".format(
                DATABASE_NAME
            )
        )

    cursor.execute(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
        (DATABASE_NAME,),
    )
    existing_tables = {row["TABLE_NAME"] for row in cursor.fetchall()}
    missing_tables = REQUIRED_TABLES - existing_tables
    if missing_tables:
        raise RuntimeError(
            "Run database.sql first; missing tables: {}.".format(
                ", ".join(sorted(missing_tables))
            )
        )


def find_existing_bulk_data(cursor):
    checks = [
        ("stocks", "BatchNo", BATCH_PREFIX + "%"),
        ("staffinfo", "EmpNo", EMPLOYEE_PREFIX + "%"),
        ("customerinformation", "ID", CUSTOMER_PREFIX + "%"),
        ("bills", "ReceiptNumber", RECEIPT_PREFIX + "%"),
        ("expenses", "Description", EXPENSE_PREFIX + "%"),
    ]
    found = []
    for table, column, pattern in checks:
        cursor.execute(
            "SELECT COUNT(*) AS RecordCount FROM {} WHERE {} LIKE %s".format(
                table, column
            ),
            (pattern,),
        )
        if cursor.fetchone()["RecordCount"]:
            found.append(table)
    return found


def reset_bulk_data(connection, cursor):
    cursor.execute(
        "SELECT COUNT(*) AS RecordCount FROM bill_items i "
        "JOIN stocks s ON s.BatchNo = i.BatchNo "
        "JOIN bills b ON b.BillID = i.BillID "
        "WHERE s.BatchNo LIKE %s AND b.ReceiptNumber NOT LIKE %s",
        (BATCH_PREFIX + "%", RECEIPT_PREFIX + "%"),
    )
    if cursor.fetchone()["RecordCount"]:
        raise RuntimeError(
            "Reset refused: non-demo bills refer to generated stock batches."
        )

    cursor.execute(
        "SELECT COUNT(*) AS RecordCount FROM bills "
        "WHERE CustomerID LIKE %s AND ReceiptNumber NOT LIKE %s",
        (CUSTOMER_PREFIX + "%", RECEIPT_PREFIX + "%"),
    )
    if cursor.fetchone()["RecordCount"]:
        raise RuntimeError(
            "Reset refused: non-demo bills refer to generated customers."
        )

    try:
        connection.start_transaction()
        cursor.execute(
            "DELETE FROM bills WHERE ReceiptNumber LIKE %s",
            (RECEIPT_PREFIX + "%",),
        )
        deleted_bills = cursor.rowcount
        cursor.execute(
            "DELETE FROM expenses WHERE Description LIKE %s",
            (EXPENSE_PREFIX + "%",),
        )
        deleted_expenses = cursor.rowcount
        cursor.execute(
            "DELETE FROM staffinfo WHERE EmpNo LIKE %s",
            (EMPLOYEE_PREFIX + "%",),
        )
        deleted_employees = cursor.rowcount
        cursor.execute(
            "DELETE FROM customerinformation WHERE ID LIKE %s",
            (CUSTOMER_PREFIX + "%",),
        )
        deleted_customers = cursor.rowcount
        cursor.execute(
            "DELETE FROM stocks WHERE BatchNo LIKE %s",
            (BATCH_PREFIX + "%",),
        )
        deleted_batches = cursor.rowcount
        connection.commit()
    except mysql.connector.Error:
        connection.rollback()
        raise

    print("Removed only the LARGEDEMO-prefixed dataset:")
    print("  bills:", deleted_bills)
    print("  expenses:", deleted_expenses)
    print("  employees:", deleted_employees)
    print("  customers:", deleted_customers)
    print("  stock batches:", deleted_batches)


def add_records(connection, cursor, today, generator):
    batches = make_stock_batches(today, generator)
    employees = make_employees(generator)
    customers = make_customers(generator)
    schedule = make_bill_schedule(today, generator)
    expenses = make_expenses(today, generator)
    remaining = {
        batch["batch_no"]: batch["remaining_quantity"] for batch in batches
    }
    initial = {
        batch["batch_no"]: batch["initial_quantity"] for batch in batches
    }
    low_stock_batches = {
        batch["batch_no"] for batch in batches if batch["low_stock"]
    }
    generated_item_count = 0

    try:
        connection.start_transaction()

        cursor.executemany(
            "INSERT INTO stocks "
            "(BatchNo, ExpiryDate, NameofMedicine, Quantity, Price, CostPrice, "
            "ManufacturerName, ManufacturerPhoneNo, MfgDate) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    batch["batch_no"], batch["expiry_date"], batch["name"],
                    batch["initial_quantity"], batch["price"], batch["cost_price"],
                    batch["manufacturer"], batch["manufacturer_phone"],
                    batch["manufacture_date"],
                )
                for batch in batches
            ],
        )

        cursor.executemany(
            "INSERT INTO staffinfo "
            "(EmpNo, Name, Gender, Age, Designation, Salary, AdharNo, Doj) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            employees,
        )

        cursor.executemany(
            "INSERT INTO customerinformation "
            "(ID, NAME, GENDER, AGE, PhoneNumber, ReceiptNumber, DoctorName, "
            "Address, ReasonForVisit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    customer["id"], customer["name"], customer["gender"],
                    customer["age"], customer["phone"], None, customer["doctor"],
                    customer["address"], customer["reason"],
                )
                for customer in customers
            ],
        )

        latest_receipt_by_customer = {}
        bill_counter_by_month = {index: 0 for index in range(6)}
        for bill_number, (bill_date, month_index) in enumerate(schedule, start=1):
            bill_counter_by_month[month_index] += 1
            receipt_number = "{}{:04d}-{:03d}".format(
                RECEIPT_PREFIX,
                bill_date.year * 100 + bill_date.month,
                bill_counter_by_month[month_index],
            )

            customer = (
                customers[generator.randrange(len(customers))]
                if generator.random() < 0.82
                else None
            )
            item_count = generator.choices(
                [1, 2, 3, 4, 5], weights=[8, 28, 32, 22, 10], k=1
            )[0]
            used_batch_numbers = set()
            line_items = []

            for _ in range(item_count):
                requested_quantity = generator.choices(
                    [1, 2, 3, 4], weights=[24, 40, 26, 10], k=1
                )[0]
                candidates = [
                    batch for batch in batches
                    if batch["batch_no"] not in used_batch_numbers
                    and batch["batch_no"] not in low_stock_batches
                    and batch["expiry_date"] > bill_date
                    and remaining[batch["batch_no"]] >= requested_quantity
                ]
                if not candidates:
                    candidates = [
                        batch for batch in batches
                        if batch["batch_no"] not in used_batch_numbers
                        and batch["batch_no"] not in low_stock_batches
                        and batch["expiry_date"] > bill_date
                        and remaining[batch["batch_no"]] > 0
                    ]
                if not candidates:
                    raise RuntimeError(
                        "Could not find eligible stock for bill {}.".format(
                            receipt_number
                        )
                    )

                batch = generator.choice(candidates)
                quantity = min(
                    requested_quantity, remaining[batch["batch_no"]]
                )
                remaining[batch["batch_no"]] -= quantity
                used_batch_numbers.add(batch["batch_no"])
                line_total = round_money(batch["price"] * quantity)
                line_items.append({
                    "batch": batch,
                    "quantity": quantity,
                    "line_total": line_total,
                })

            generated_item_count += len(line_items)
            subtotal = round_money(sum(
                (item["line_total"] for item in line_items), Decimal("0.00")
            ))
            gst_amount = round_money(subtotal * GST_RATE / Decimal("100"))
            total = round_money(subtotal + gst_amount)
            customer_name = customer["name"] if customer else None
            customer_phone = customer["phone"] if customer else None

            cursor.execute(
                "INSERT INTO bills "
                "(ReceiptNumber, DATEOFBILL, CustomerID, CustomerName, "
                "CustomerPhone, Subtotal, GSTRate, GSTAmount, Total) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    receipt_number,
                    datetime.combine(bill_date, time(12, 0)),
                    customer["id"] if customer else None,
                    customer_name,
                    customer_phone,
                    subtotal,
                    GST_RATE,
                    gst_amount,
                    total,
                ),
            )
            bill_id = cursor.lastrowid

            cursor.executemany(
                "INSERT INTO bill_items "
                "(BillID, BatchNo, MedicineName, BillQuantity, UnitPrice, "
                "UnitCost, LineTotal) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        bill_id,
                        item["batch"]["batch_no"],
                        item["batch"]["name"],
                        item["quantity"],
                        item["batch"]["price"],
                        item["batch"]["cost_price"],
                        item["line_total"],
                    )
                    for item in line_items
                ],
            )

            if customer:
                latest_receipt_by_customer[customer["id"]] = receipt_number

        for batch_number, opening_quantity in initial.items():
            sold_quantity = opening_quantity - remaining[batch_number]
            if sold_quantity:
                cursor.execute(
                    "UPDATE stocks SET Quantity = Quantity - %s "
                    "WHERE BatchNo = %s AND Quantity >= %s",
                    (sold_quantity, batch_number, sold_quantity),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "Stock deduction failed for batch {}.".format(
                            batch_number
                        )
                    )

        for customer_id, receipt_number in latest_receipt_by_customer.items():
            cursor.execute(
                "UPDATE customerinformation SET ReceiptNumber = %s WHERE ID = %s",
                (receipt_number, customer_id),
            )

        cursor.executemany(
            "INSERT INTO expenses (ExpenseDate, Category, Amount, Description) "
            "VALUES (%s, %s, %s, %s)",
            expenses,
        )

        connection.commit()
    except (mysql.connector.Error, RuntimeError):
        connection.rollback()
        raise

    print("Generated records:")
    print("  stock batches:", len(batches))
    print("  employees:", len(employees))
    print("  customers:", len(customers))
    print("  bills:", len(schedule))
    print("  bill items:", generated_item_count)
    print("  expenses:", len(expenses))
    return initial


def verify_dataset(connection, cursor, initial_quantities):
    cursor.execute(
        "SELECT COUNT(*) AS RecordCount FROM stocks WHERE BatchNo LIKE %s",
        (BATCH_PREFIX + "%",),
    )
    batch_count = cursor.fetchone()["RecordCount"]
    cursor.execute(
        "SELECT COUNT(*) AS RecordCount FROM staffinfo WHERE EmpNo LIKE %s",
        (EMPLOYEE_PREFIX + "%",),
    )
    employee_count = cursor.fetchone()["RecordCount"]
    cursor.execute(
        "SELECT COUNT(*) AS RecordCount FROM customerinformation WHERE ID LIKE %s",
        (CUSTOMER_PREFIX + "%",),
    )
    customer_count = cursor.fetchone()["RecordCount"]
    cursor.execute(
        "SELECT COUNT(*) AS RecordCount FROM bills WHERE ReceiptNumber LIKE %s",
        (RECEIPT_PREFIX + "%",),
    )
    bill_count = cursor.fetchone()["RecordCount"]
    cursor.execute(
        "SELECT COUNT(*) AS RecordCount FROM bill_items i JOIN bills b "
        "ON b.BillID = i.BillID "
        "WHERE b.ReceiptNumber LIKE %s",
        (RECEIPT_PREFIX + "%",),
    )
    item_count = cursor.fetchone()["RecordCount"]
    cursor.execute(
        "SELECT COUNT(*) AS RecordCount FROM expenses WHERE Description LIKE %s",
        (EXPENSE_PREFIX + "%",),
    )
    expense_count = cursor.fetchone()["RecordCount"]

    expected = {
        "stock batches": STOCK_BATCH_COUNT,
        "employees": EMPLOYEE_COUNT,
        "customers": CUSTOMER_COUNT,
        "bills": sum(BILL_COUNTS_BY_MONTH),
        "bill items": None,
        "expenses": len(get_recent_months(date.today())) * EXPENSES_PER_MONTH,
    }
    actual = {
        "stock batches": batch_count,
        "employees": employee_count,
        "customers": customer_count,
        "bills": bill_count,
        "bill items": item_count,
        "expenses": expense_count,
    }
    if item_count < 300 or item_count > 600:
        raise RuntimeError(
            "Generated bill-item count {} is outside the 300-600 target.".format(
                item_count
            )
        )
    for name, count in actual.items():
        if expected[name] is not None and count != expected[name]:
            raise RuntimeError(
                "Unexpected {} count: {} (expected {}).".format(
                    name, count, expected[name]
                )
            )

    cursor.execute(
        "SELECT b.BillID, b.Subtotal, b.GSTRate, b.GSTAmount, b.Total, "
        "COALESCE(SUM(i.LineTotal), 0) AS ItemSubtotal "
        "FROM bills b JOIN bill_items i ON i.BillID = b.BillID "
        "WHERE b.ReceiptNumber LIKE %s GROUP BY b.BillID",
        (RECEIPT_PREFIX + "%",),
    )
    for bill in cursor.fetchall():
        item_subtotal = round_money(Decimal(str(bill["ItemSubtotal"])))
        gst_amount = round_money(
            item_subtotal * Decimal(str(bill["GSTRate"])) / Decimal("100")
        )
        total = round_money(item_subtotal + gst_amount)
        if (
            Decimal(str(bill["Subtotal"])) != item_subtotal
            or Decimal(str(bill["GSTAmount"])) != gst_amount
            or Decimal(str(bill["Total"])) != total
        ):
            raise RuntimeError(
                "Bill total verification failed for bill {}.".format(
                    bill["BillID"]
                )
            )

    cursor.execute(
        "SELECT COUNT(*) AS RecordCount FROM bill_items i "
        "JOIN bills b ON b.BillID = i.BillID "
        "JOIN stocks s ON s.BatchNo = i.BatchNo "
        "WHERE b.ReceiptNumber LIKE %s AND s.ExpiryDate <= DATE(b.DATEOFBILL)",
        (RECEIPT_PREFIX + "%",),
    )
    if cursor.fetchone()["RecordCount"]:
        raise RuntimeError("An expired batch was sold in the generated bills.")

    cursor.execute(
        "SELECT COUNT(*) AS RecordCount FROM stocks WHERE Quantity < 0"
    )
    if cursor.fetchone()["RecordCount"]:
        raise RuntimeError("A stock quantity is negative.")

    cursor.execute(
        "SELECT s.BatchNo, s.Quantity, "
        "COALESCE(SUM(i.BillQuantity), 0) AS Sold "
        "FROM stocks s LEFT JOIN bill_items i ON i.BatchNo = s.BatchNo "
        "LEFT JOIN bills b ON b.BillID = i.BillID "
        "WHERE s.BatchNo LIKE %s "
        "AND (b.BillID IS NULL OR b.ReceiptNumber LIKE %s) "
        "GROUP BY s.BatchNo, s.Quantity",
        (BATCH_PREFIX + "%", RECEIPT_PREFIX + "%"),
    )
    for row in cursor.fetchall():
        expected_opening = initial_quantities[row["BatchNo"]]
        if int(row["Quantity"]) + int(row["Sold"]) != expected_opening:
            raise RuntimeError(
                "Stock/bill quantity reconciliation failed for {}.".format(
                    row["BatchNo"]
                )
            )

    cursor.execute(
        "SELECT "
        "SUM(ExpiryDate <= CURDATE()) AS Expired, "
        "SUM(ExpiryDate > CURDATE() AND ExpiryDate <= DATE_ADD(CURDATE(), INTERVAL 60 DAY)) AS DueSoon, "
        "SUM(ExpiryDate > DATE_ADD(CURDATE(), INTERVAL 60 DAY)) AS Healthy "
        "FROM stocks WHERE BatchNo LIKE %s",
        (BATCH_PREFIX + "%",),
    )
    expiry_counts = cursor.fetchone()

    cursor.execute(
        "SELECT DATE_FORMAT(b.DATEOFBILL, '%Y-%m') AS Period, "
        "SUM(i.LineTotal) AS Revenue, "
        "SUM(i.BillQuantity * i.UnitCost) AS Cost "
        "FROM bills b JOIN bill_items i ON i.BillID = b.BillID "
        "WHERE b.DATEOFBILL >= %s AND b.ReceiptNumber LIKE %s "
        "GROUP BY Period ORDER BY Period",
        (get_recent_months(date.today())[0][0], RECEIPT_PREFIX + "%"),
    )
    monthly_sales = {
        row["Period"]: {
            "revenue": Decimal(str(row["Revenue"])),
            "cost": Decimal(str(row["Cost"])),
        }
        for row in cursor.fetchall()
    }
    cursor.execute(
        "SELECT DATE_FORMAT(ExpenseDate, '%Y-%m') AS Period, "
        "SUM(Amount) AS Amount FROM expenses WHERE Description LIKE %s "
        "GROUP BY Period ORDER BY Period",
        (EXPENSE_PREFIX + "%",),
    )
    monthly_expenses = {
        row["Period"]: Decimal(str(row["Amount"])) for row in cursor.fetchall()
    }

    print("\nVerified generated record counts:")
    for name, count in actual.items():
        print("  {}: {}".format(name, count))
    print(
        "  expiry categories (expired / due within 60 days / healthy): "
        "{} / {} / {}".format(
            expiry_counts["Expired"] or 0,
            expiry_counts["DueSoon"] or 0,
            expiry_counts["Healthy"] or 0,
        )
    )
    print("\nMonthly generated sales graph data:")
    for first_day, _last_day in get_recent_months(date.today()):
        period = first_day.strftime("%Y-%m")
        sales = monthly_sales.get(
            period, {"revenue": Decimal("0"), "cost": Decimal("0")}
        )
        expenses_amount = monthly_expenses.get(period, Decimal("0"))
        estimated_profit = (
            sales["revenue"] - sales["cost"] - expenses_amount
        )
        print(
            "  {} revenue={} cost={} expenses={} estimated-profit/loss={}".format(
                period,
                round_money(sales["revenue"]),
                round_money(sales["cost"]),
                round_money(expenses_amount),
                round_money(estimated_profit),
            )
        )

    cursor.execute(
        "SELECT "
        "(SELECT COUNT(*) FROM stocks) AS stocks, "
        "(SELECT COUNT(*) FROM staffinfo) AS staff, "
        "(SELECT COUNT(*) FROM customerinformation) AS customers, "
        "(SELECT COUNT(*) FROM bills) AS bills, "
        "(SELECT COUNT(*) FROM bill_items) AS bill_items, "
        "(SELECT COUNT(*) FROM expenses) AS expenses"
    )
    totals = cursor.fetchone()
    print("\nDatabase-wide totals (including starter demo rows):")
    for table, count in totals.items():
        print("  {}: {}".format(table, count))


def main():
    parser = argparse.ArgumentParser(
        description="Generate or safely reset LARGEDEMO-prefixed fictional data."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="remove only this generator's prefixed rows; never drop the database",
    )
    arguments = parser.parse_args()

    generator = random.Random(RANDOM_SEED)
    today = date.today()
    connection = mysql.connector.connect(
        **DB_CONFIG, connection_timeout=10, autocommit=True
    )
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        check_database_and_schema(cursor)

        if arguments.reset:
            reset_bulk_data(connection, cursor)
            return

        existing = find_existing_bulk_data(cursor)
        if existing:
            raise RuntimeError(
                "A LARGEDEMO dataset already exists in {}. No data was changed. "
                "Use --reset to remove only generated rows before regenerating."
                .format(DATABASE_NAME)
            )

        initial_quantities = add_records(
            connection, cursor, today, generator
        )
        verify_dataset(connection, cursor, initial_quantities)
    except (mysql.connector.Error, RuntimeError):
        if connection.is_connected():
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
