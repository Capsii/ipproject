"""Class 12 Chemist Shop Management System."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hmac
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib.pyplot as plt
import mysql.connector

try:
    from db_config import DB_CONFIG, LOGIN_PASSWORD, LOGIN_USERNAME
except ImportError as error:
    DB_CONFIG = None
    LOGIN_PASSWORD = None
    LOGIN_USERNAME = None
    CONFIG_IMPORT_ERROR = error
else:
    CONFIG_IMPORT_ERROR = None


GST_RATE = Decimal("5.00")
MONEY_PLACES = Decimal("0.01")

STOCK_FIELDS = [
    ("BatchNo", "Batch number", "text", True),
    ("ExpiryDate", "Expiry date (YYYY-MM-DD)", "date", True),
    ("NameofMedicine", "Medicine name", "text", True),
    ("Quantity", "Quantity", "integer", True),
    ("Price", "Selling price", "money", True),
    ("CostPrice", "Cost price", "money", True),
    ("ManufacturerName", "Manufacturer name", "text", False),
    ("ManufacturerPhoneNo", "Manufacturer phone", "text", False),
    ("MfgDate", "Manufacturing date (YYYY-MM-DD)", "date", False),
]

STAFF_FIELDS = [
    ("EmpNo", "Employee number", "text", True),
    ("Name", "Name", "text", True),
    ("Gender", "Gender", "text", False),
    ("Age", "Age", "integer", False),
    ("Designation", "Designation", "text", False),
    ("Salary", "Salary", "money", False),
    ("AdharNo", "Aadhaar number", "text", True),
    ("Doj", "Date of joining (YYYY-MM-DD)", "date", False),
]

CUSTOMER_FIELDS = [
    ("ID", "Customer ID", "text", True),
    ("NAME", "Name", "text", True),
    ("GENDER", "Gender", "text", True),
    ("AGE", "Age", "integer", False),
    ("PhoneNumber", "Phone number", "text", False),
    ("ReceiptNumber", "Receipt number", "text", False),
    ("DoctorName", "Doctor name", "text", False),
    ("Address", "Address", "text", False),
    ("ReasonForVisit", "Reason for visit", "text", False),
]

EXPENSE_FIELDS = [
    ("ExpenseDate", "Expense date (YYYY-MM-DD)", "date", True),
    ("Category", "Category", "text", True),
    ("Amount", "Amount", "money", True),
    ("Description", "Description", "text", False),
]


def connect_database():
    if DB_CONFIG is None:
        raise RuntimeError(
            "The local db_config.py file is missing or could not be imported. "
            "Copy db_config.example.py to db_config.py and enter your settings."
        )
    return mysql.connector.connect(**DB_CONFIG)


def fetch_all(query, parameters=()):
    connection = connect_database()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, parameters)
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def execute_write(query, parameters=()):
    connection = connect_database()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(query, parameters)
        connection.commit()
        return cursor.rowcount
    except mysql.connector.Error:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def show_operation_error(error, parent):
    if isinstance(error, (mysql.connector.Error, RuntimeError)):
        messagebox.showerror(
            "Operation could not be completed",
            "{}".format(error),
            parent=parent,
        )
    else:
        messagebox.showwarning("Check the entered details", str(error), parent=parent)


def round_money(amount):
    value = Decimal(amount)
    if not value.is_finite():
        raise ValueError("Amounts must be finite numbers.")
    try:
        return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError("Amount is too large to process.")


def parse_value(field, label, kind, required):
    text = field.get().strip()
    if not text:
        if required:
            raise ValueError("{} is required.".format(label))
        return None

    if kind == "date":
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("{} must use YYYY-MM-DD format.".format(label))

    if kind == "integer":
        try:
            value = int(text)
        except ValueError:
            raise ValueError("{} must be a whole number.".format(label))
        if value < 0:
            raise ValueError("{} cannot be negative.".format(label))
        return value

    if kind == "money":
        try:
            value = Decimal(text)
        except InvalidOperation:
            raise ValueError("{} must be a number.".format(label))
        if not value.is_finite():
            raise ValueError("{} must be a finite number.".format(label))
        if value < 0:
            raise ValueError("{} cannot be negative.".format(label))
        return round_money(value)

    return text


def read_form(fields, entries, table_name):
    values = {}
    for column, label, kind, required in fields:
        values[column] = parse_value(entries[column], label, kind, required)

    if table_name == "stocks":
        expiry = values["ExpiryDate"]
        manufacture = values["MfgDate"]
        if manufacture is not None and manufacture > expiry:
            raise ValueError("Manufacturing date cannot be after the expiry date.")

    if table_name == "staffinfo" and values["Age"] is not None:
        if values["Age"] > 120:
            raise ValueError("Age must be 120 or less.")

    if table_name == "customerinformation" and values["AGE"] is not None:
        if values["AGE"] > 120:
            raise ValueError("Age must be 120 or less.")

    return values


def create_window(parent, title, geometry):
    window = tk.Toplevel(parent)
    window.title(title)
    window.geometry(geometry)
    window.configure(bg="#f2f4f7")
    return window


def make_tree(parent, columns, height=10):
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True, padx=10, pady=8)
    keys = [column[0] for column in columns]
    tree = ttk.Treeview(frame, columns=keys, show="headings", height=height)
    for key, label, width in columns:
        tree.heading(key, text=label)
        tree.column(key, width=width, minwidth=70, anchor="center")
    vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return tree


def fill_tree(tree, rows, columns):
    tree.delete(*tree.get_children())
    for row in rows:
        values = []
        for key, _label, _width in columns:
            value = row.get(key)
            if isinstance(value, (date, datetime)):
                value = value.strftime("%Y-%m-%d")
            values.append("" if value is None else str(value))
        tree.insert("", "end", values=values)


def open_table_window(parent, title, rows, columns):
    window = create_window(parent, title, "1100x520")
    tree = make_tree(window, columns, height=17)
    fill_tree(tree, rows, columns)
    ttk.Button(window, text="Back", command=window.destroy).pack(pady=(0, 12))


def open_record_manager(parent, title, table_name, fields, primary_key, search_columns):
    window = create_window(parent, title, "1180x760")
    tk.Label(
        window, text=title, font=("Segoe UI", 19, "bold"),
        bg="#f2f4f7", fg="#17324d",
    ).pack(pady=(12, 4))

    form = ttk.LabelFrame(window, text="Record details", padding=10)
    form.pack(fill="x", padx=12, pady=8)
    entries = {}
    columns_per_row = 3
    for index, (column, label, _kind, _required) in enumerate(fields):
        row = index // columns_per_row
        group = index % columns_per_row
        cell = ttk.Frame(form)
        cell.grid(row=row, column=group, sticky="ew", padx=8, pady=5)
        ttk.Label(cell, text=label).pack(anchor="w")
        entry = ttk.Entry(cell, width=28)
        entry.pack(fill="x")
        entries[column] = entry
        form.columnconfigure(group, weight=1)

    button_row = ttk.Frame(window)
    button_row.pack(fill="x", padx=12, pady=4)
    keyword = ttk.Entry(button_row, width=28)
    keyword.pack(side="left", padx=(0, 6))

    display_columns = [
        (column, label, 150 if len(label) < 18 else 190)
        for column, label, _kind, _required in fields
    ]
    tree = make_tree(window, display_columns, height=12)

    def clear_form():
        for entry in entries.values():
            entry.delete(0, tk.END)
        tree.selection_remove(tree.selection())

    def load_rows(search_text=None):
        try:
            if search_text:
                conditions = " OR ".join(
                    "CAST({} AS CHAR) LIKE %s".format(column)
                    for column in search_columns
                )
                parameters = tuple("%{}%".format(search_text) for _ in search_columns)
                rows = fetch_all(
                    "SELECT * FROM {} WHERE {} ORDER BY {}".format(
                        table_name, conditions, primary_key
                    ),
                    parameters,
                )
            else:
                rows = fetch_all(
                    "SELECT * FROM {} ORDER BY {}".format(table_name, primary_key)
                )
            fill_tree(tree, rows, display_columns)
            return rows
        except (mysql.connector.Error, RuntimeError) as error:
            show_operation_error(error, window)
            return []

    def add_record():
        try:
            values = read_form(fields, entries, table_name)
            names = [field[0] for field in fields]
            placeholders = ", ".join(["%s"] * len(names))
            execute_write(
                "INSERT INTO {} ({}) VALUES ({})".format(
                    table_name, ", ".join(names), placeholders
                ),
                tuple(values[name] for name in names),
            )
        except (ValueError, mysql.connector.Error, RuntimeError) as error:
            show_operation_error(error, window)
            return
        messagebox.showinfo("Saved", "Record added successfully.", parent=window)
        clear_form()
        load_rows()

    def update_record():
        try:
            values = read_form(fields, entries, table_name)
            key_value = values[primary_key]
            if key_value is None:
                raise ValueError("{} is required.".format(primary_key))
            update_fields = [field[0] for field in fields if field[0] != primary_key]
            assignments = ", ".join("{} = %s".format(name) for name in update_fields)
            parameters = tuple(values[name] for name in update_fields) + (key_value,)
            affected = execute_write(
                "UPDATE {} SET {} WHERE {} = %s".format(
                    table_name, assignments, primary_key
                ),
                parameters,
            )
        except (ValueError, mysql.connector.Error, RuntimeError) as error:
            show_operation_error(error, window)
            return
        if affected == 0:
            messagebox.showinfo("No change", "No matching record was updated.", parent=window)
        else:
            messagebox.showinfo("Saved", "Record updated successfully.", parent=window)
        load_rows()

    def delete_record():
        key_value = entries[primary_key].get().strip()
        if not key_value:
            messagebox.showwarning(
                "Required", "{} is required to delete a record.".format(primary_key),
                parent=window,
            )
            return
        if not messagebox.askyesno(
            "Confirm deletion", "Delete this record?", parent=window
        ):
            return
        try:
            affected = execute_write(
                "DELETE FROM {} WHERE {} = %s".format(table_name, primary_key),
                (key_value,),
            )
        except (mysql.connector.Error, RuntimeError) as error:
            show_operation_error(error, window)
            return
        if affected == 0:
            messagebox.showinfo("Not found", "No matching record was deleted.", parent=window)
        else:
            messagebox.showinfo("Deleted", "Record deleted successfully.", parent=window)
        clear_form()
        load_rows()

    def search_records():
        term = keyword.get().strip()
        if not term:
            messagebox.showwarning(
                "Search", "Enter a search term first.", parent=window
            )
            return
        rows = load_rows(term)
        if rows:
            first = rows[0]
            for column, _label, _kind, _required in fields:
                entries[column].delete(0, tk.END)
                value = first.get(column)
                if value is not None:
                    if isinstance(value, (date, datetime)):
                        value = value.strftime("%Y-%m-%d")
                    entries[column].insert(0, str(value))
        else:
            messagebox.showinfo("Search", "No matching record was found.", parent=window)

    def select_record(_event=None):
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0], "values")
        for index, (column, _label, _kind, _required) in enumerate(fields):
            entries[column].delete(0, tk.END)
            if index < len(values):
                entries[column].insert(0, values[index])

    tree.bind("<<TreeviewSelect>>", select_record)
    ttk.Button(button_row, text="Search", command=search_records).pack(side="left", padx=3)
    ttk.Button(button_row, text="Add", command=add_record).pack(side="left", padx=3)
    ttk.Button(button_row, text="Update", command=update_record).pack(side="left", padx=3)
    ttk.Button(button_row, text="Delete", command=delete_record).pack(side="left", padx=3)
    ttk.Button(button_row, text="Clear", command=clear_form).pack(side="left", padx=3)
    ttk.Button(button_row, text="Refresh / View all", command=load_rows).pack(
        side="left", padx=3
    )
    ttk.Button(button_row, text="Back", command=window.destroy).pack(
        side="right", padx=3
    )
    load_rows()


def open_expense_manager(parent):
    window = create_window(parent, "Expense Entry", "1000x620")
    tk.Label(
        window, text="Expense Entry", font=("Segoe UI", 19, "bold"),
        bg="#f2f4f7", fg="#17324d",
    ).pack(pady=12)
    form = ttk.LabelFrame(window, text="Expense details", padding=10)
    form.pack(fill="x", padx=12, pady=8)
    entries = {}
    for column, label, _kind, _required in EXPENSE_FIELDS:
        cell = ttk.Frame(form)
        cell.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Label(cell, text=label).pack(anchor="w")
        entries[column] = ttk.Entry(cell)
        entries[column].pack(fill="x")

    columns = [
        ("ExpenseID", "Expense ID", 100),
        ("ExpenseDate", "Date", 130),
        ("Category", "Category", 160),
        ("Amount", "Amount", 120),
        ("Description", "Description", 360),
    ]
    tree = make_tree(window, columns, height=12)

    def refresh():
        try:
            rows = fetch_all("SELECT * FROM expenses ORDER BY ExpenseDate DESC, ExpenseID DESC")
        except (mysql.connector.Error, RuntimeError) as error:
            show_operation_error(error, window)
            return
        fill_tree(tree, rows, columns)

    def add_expense():
        try:
            values = read_form(EXPENSE_FIELDS, entries, "expenses")
            execute_write(
                "INSERT INTO expenses (ExpenseDate, Category, Amount, Description) "
                "VALUES (%s, %s, %s, %s)",
                (
                    values["ExpenseDate"],
                    values["Category"],
                    values["Amount"],
                    values["Description"],
                ),
            )
        except (ValueError, mysql.connector.Error, RuntimeError) as error:
            show_operation_error(error, window)
            return
        messagebox.showinfo("Saved", "Expense added successfully.", parent=window)
        for entry in entries.values():
            entry.delete(0, tk.END)
        refresh()

    def delete_expense():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning(
                "Select a record", "Select an expense to delete.", parent=window
            )
            return
        expense_id = tree.item(selected[0], "values")[0]
        if not messagebox.askyesno(
            "Confirm deletion", "Delete the selected expense?", parent=window
        ):
            return
        try:
            execute_write("DELETE FROM expenses WHERE ExpenseID = %s", (expense_id,))
        except (mysql.connector.Error, RuntimeError) as error:
            show_operation_error(error, window)
            return
        refresh()

    buttons = ttk.Frame(window)
    buttons.pack(fill="x", padx=12, pady=8)
    ttk.Button(buttons, text="Add expense", command=add_expense).pack(side="left", padx=4)
    ttk.Button(buttons, text="Delete selected", command=delete_expense).pack(
        side="left", padx=4
    )
    ttk.Button(buttons, text="Refresh", command=refresh).pack(side="left", padx=4)
    ttk.Button(buttons, text="Back", command=window.destroy).pack(side="right", padx=4)
    refresh()


def open_billing(parent):
    window = create_window(parent, "Bills", "1120x720")
    tk.Label(
        window, text="Chemist Shop Billing", font=("Segoe UI", 19, "bold"),
        bg="#f2f4f7", fg="#17324d",
    ).pack(pady=(10, 4))

    customer_frame = ttk.LabelFrame(window, text="Customer details", padding=8)
    customer_frame.pack(fill="x", padx=12, pady=6)
    ttk.Label(customer_frame, text="Customer name").grid(row=0, column=0, padx=5)
    customer_name = ttk.Entry(customer_frame, width=30)
    customer_name.grid(row=0, column=1, padx=5)
    ttk.Label(customer_frame, text="Phone number").grid(row=0, column=2, padx=5)
    customer_phone = ttk.Entry(customer_frame, width=22)
    customer_phone.grid(row=0, column=3, padx=5)

    item_frame = ttk.LabelFrame(window, text="Add medicine to bill", padding=8)
    item_frame.pack(fill="x", padx=12, pady=6)
    ttk.Label(item_frame, text="Batch number or exact medicine name").grid(
        row=0, column=0, padx=5
    )
    product_entry = ttk.Entry(item_frame, width=34)
    product_entry.grid(row=0, column=1, padx=5)
    ttk.Label(item_frame, text="Quantity").grid(row=0, column=2, padx=5)
    quantity_entry = ttk.Entry(item_frame, width=10)
    quantity_entry.grid(row=0, column=3, padx=5)

    item_columns = [
        ("BatchNo", "Batch number", 120),
        ("NameofMedicine", "Medicine", 230),
        ("Quantity", "Quantity", 90),
        ("UnitPrice", "Unit price", 120),
        ("LineTotal", "Line total", 120),
    ]
    tree = make_tree(window, item_columns, height=11)
    bill_items = []

    def refresh_items():
        rows = []
        for item in bill_items:
            rows.append({
                "BatchNo": item["BatchNo"],
                "NameofMedicine": item["NameofMedicine"],
                "Quantity": item["Quantity"],
                "UnitPrice": item["UnitPrice"],
                "LineTotal": round_money(item["UnitPrice"] * item["Quantity"]),
            })
        fill_tree(tree, rows, item_columns)

    def add_item():
        search_text = product_entry.get().strip()
        if not search_text:
            raise ValueError("Enter a batch number or medicine name.")
        try:
            quantity = int(quantity_entry.get().strip())
        except ValueError:
            raise ValueError("Quantity must be a whole number.")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        rows = fetch_all(
            "SELECT BatchNo, NameofMedicine, Quantity, Price, CostPrice, ExpiryDate "
            "FROM stocks WHERE (BatchNo = %s OR NameofMedicine = %s) "
            "AND Quantity >= %s AND ExpiryDate > CURDATE() "
            "ORDER BY ExpiryDate, BatchNo",
            (search_text, search_text, quantity),
        )
        pending_quantities = {
            item["BatchNo"]: item["Quantity"] for item in bill_items
        }
        rows = [
            row for row in rows
            if int(row["Quantity"])
            >= quantity + pending_quantities.get(row["BatchNo"], 0)
        ]
        if not rows:
            raise ValueError(
                "No unexpired batch with enough stock was found. "
                "For medicines with several batches, the earliest-expiring "
                "batch with enough stock is selected."
            )
        stock = rows[0]
        for existing in bill_items:
            if existing["BatchNo"] == stock["BatchNo"]:
                existing["Quantity"] += quantity
                refresh_items()
                product_entry.delete(0, tk.END)
                quantity_entry.delete(0, tk.END)
                return
        bill_items.append({
            "BatchNo": stock["BatchNo"],
            "NameofMedicine": stock["NameofMedicine"],
            "Quantity": quantity,
            "UnitPrice": Decimal(str(stock["Price"])),
            "UnitCost": Decimal(str(stock["CostPrice"])),
        })
        refresh_items()
        product_entry.delete(0, tk.END)
        quantity_entry.delete(0, tk.END)

    def remove_item():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning(
                "Select an item", "Select a bill item to remove.", parent=window
            )
            return
        batch_no = tree.item(selected[0], "values")[0]
        bill_items[:] = [
            item for item in bill_items if item["BatchNo"] != batch_no
        ]
        refresh_items()

    def save_bill():
        if not bill_items:
            raise ValueError("Add at least one medicine before generating a bill.")
        name = customer_name.get().strip()
        phone = customer_phone.get().strip()
        if len(phone) > 20:
            raise ValueError("Phone number must be 20 characters or fewer.")

        connection = connect_database()
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            connection.start_transaction()
            customer_id = None
            if phone:
                cursor.execute(
                    "SELECT ID FROM customerinformation "
                    "WHERE PhoneNumber = %s ORDER BY ID LIMIT 1",
                    (phone,),
                )
                customer = cursor.fetchone()
                if customer:
                    customer_id = customer["ID"]

            sale_lines = []
            subtotal = Decimal("0.00")
            for item in bill_items:
                cursor.execute(
                    "SELECT NameofMedicine, Quantity, Price, CostPrice, ExpiryDate "
                    "FROM stocks WHERE BatchNo = %s FOR UPDATE",
                    (item["BatchNo"],),
                )
                stock = cursor.fetchone()
                if stock is None:
                    raise ValueError("Batch {} no longer exists.".format(item["BatchNo"]))
                if stock["ExpiryDate"] <= date.today():
                    raise ValueError("Batch {} has expired.".format(item["BatchNo"]))
                if int(stock["Quantity"]) < item["Quantity"]:
                    raise ValueError(
                        "Not enough stock remains for batch {}.".format(item["BatchNo"])
                    )

                unit_price = Decimal(str(stock["Price"]))
                unit_cost = Decimal(str(stock["CostPrice"]))
                line_total = round_money(unit_price * item["Quantity"])
                subtotal += line_total
                sale_lines.append({
                    "BatchNo": item["BatchNo"],
                    "NameofMedicine": stock["NameofMedicine"],
                    "Quantity": item["Quantity"],
                    "UnitPrice": unit_price,
                    "UnitCost": unit_cost,
                    "LineTotal": line_total,
                })

            subtotal = round_money(subtotal)
            gst_amount = round_money(subtotal * GST_RATE / Decimal("100"))
            total = round_money(subtotal + gst_amount)
            receipt_number = "BILL-{}".format(datetime.now().strftime("%Y%m%d%H%M%S%f"))

            cursor.execute(
                "INSERT INTO bills "
                "(ReceiptNumber, DATEOFBILL, CustomerID, CustomerName, CustomerPhone, "
                "Subtotal, GSTRate, GSTAmount, Total) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    receipt_number, datetime.now(), customer_id, name or None,
                    phone or None, subtotal, GST_RATE, gst_amount, total,
                ),
            )
            bill_id = cursor.lastrowid

            for item in sale_lines:
                cursor.execute(
                    "INSERT INTO bill_items "
                    "(BillID, BatchNo, MedicineName, BillQuantity, UnitPrice, "
                    "UnitCost, LineTotal) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        bill_id, item["BatchNo"], item["NameofMedicine"],
                        item["Quantity"], item["UnitPrice"], item["UnitCost"],
                        item["LineTotal"],
                    ),
                )
                cursor.execute(
                    "UPDATE stocks SET Quantity = Quantity - %s "
                    "WHERE BatchNo = %s AND Quantity >= %s",
                    (item["Quantity"], item["BatchNo"], item["Quantity"]),
                )
                if cursor.rowcount != 1:
                    raise ValueError(
                        "Stock changed while the bill was being saved. Please try again."
                    )

            if customer_id is not None:
                cursor.execute(
                    "UPDATE customerinformation SET ReceiptNumber = %s WHERE ID = %s",
                    (receipt_number, customer_id),
                )

            connection.commit()
            return {
                "receipt": receipt_number,
                "name": name,
                "phone": phone,
                "items": sale_lines,
                "subtotal": subtotal,
                "gst": gst_amount,
                "total": total,
            }
        except (mysql.connector.Error, ValueError):
            connection.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    def show_receipt(receipt):
        receipt_window = create_window(window, "Saved bill", "620x520")
        text = tk.Text(receipt_window, wrap="none", font=("Consolas", 11))
        text.pack(fill="both", expand=True, padx=12, pady=12)
        text.insert("end", "DPK CHEMIST SHOP\n")
        text.insert("end", "Receipt: {}\n".format(receipt["receipt"]))
        text.insert("end", "Customer: {}\n".format(receipt["name"] or "Walk-in"))
        text.insert("end", "Phone: {}\n\n".format(receipt["phone"] or "-"))
        text.insert("end", "{:<24} {:>5} {:>10} {:>10}\n".format(
            "Medicine", "Qty", "Rate", "Amount"
        ))
        text.insert("end", "-" * 54 + "\n")
        for item in receipt["items"]:
            text.insert("end", "{:<24} {:>5} {:>10.2f} {:>10.2f}\n".format(
                item["NameofMedicine"][:24], item["Quantity"],
                item["UnitPrice"], item["LineTotal"],
            ))
        text.insert("end", "\nSubtotal: {:.2f}\n".format(receipt["subtotal"]))
        text.insert("end", "GST ({:.0f}%): {:.2f}\n".format(GST_RATE, receipt["gst"]))
        text.insert("end", "Total: {:.2f}\n".format(receipt["total"]))
        text.configure(state="disabled")
        ttk.Button(receipt_window, text="Close", command=receipt_window.destroy).pack(
            pady=(0, 12)
        )

    def generate_bill():
        try:
            receipt = save_bill()
        except (ValueError, mysql.connector.Error, RuntimeError) as error:
            show_operation_error(error, window)
            return
        messagebox.showinfo(
            "Bill saved",
            "The bill was saved and stock was updated.",
            parent=window,
        )
        bill_items.clear()
        refresh_items()
        show_receipt(receipt)

    buttons = ttk.Frame(window)
    buttons.pack(fill="x", padx=12, pady=8)
    ttk.Button(buttons, text="Add item", command=lambda: run_form_action(
        add_item, window
    )).pack(side="left", padx=4)
    ttk.Button(buttons, text="Remove selected item", command=remove_item).pack(
        side="left", padx=4
    )
    ttk.Button(buttons, text="Generate and save bill", command=generate_bill).pack(
        side="left", padx=4
    )
    ttk.Button(buttons, text="Clear bill", command=lambda: clear_bill()).pack(
        side="left", padx=4
    )
    ttk.Button(buttons, text="Back", command=window.destroy).pack(side="right", padx=4)

    def clear_bill():
        bill_items.clear()
        refresh_items()
        customer_name.delete(0, tk.END)
        customer_phone.delete(0, tk.END)
        product_entry.delete(0, tk.END)
        quantity_entry.delete(0, tk.END)


def run_form_action(action, parent):
    try:
        action()
    except (ValueError, mysql.connector.Error, RuntimeError) as error:
        show_operation_error(error, parent)


def open_expired_products(parent):
    window = create_window(parent, "Expired Products", "900x520")
    columns = [
        ("BatchNo", "Batch number", 130),
        ("NameofMedicine", "Medicine", 260),
        ("Quantity", "Quantity", 100),
        ("ExpiryDate", "Expiry date", 150),
    ]
    tree = make_tree(window, columns, height=16)
    try:
        rows = fetch_all(
            "SELECT BatchNo, NameofMedicine, Quantity, ExpiryDate "
            "FROM stocks WHERE ExpiryDate <= CURDATE() "
            "ORDER BY ExpiryDate, NameofMedicine"
        )
    except (mysql.connector.Error, RuntimeError) as error:
        show_operation_error(error, window)
        rows = []
    fill_tree(tree, rows, columns)
    ttk.Button(window, text="Back", command=window.destroy).pack(pady=(0, 12))


def open_stock_graph(parent):
    try:
        rows = fetch_all(
            "SELECT NameofMedicine, SUM(Quantity) AS Quantity "
            "FROM stocks GROUP BY NameofMedicine ORDER BY NameofMedicine"
        )
    except (mysql.connector.Error, RuntimeError) as error:
        show_operation_error(error, parent)
        return
    if not rows:
        messagebox.showinfo("Stock graph", "There is no stock data to graph.", parent=parent)
        return
    names = [row["NameofMedicine"] for row in rows]
    quantities = [int(row["Quantity"]) for row in rows]
    plt.figure(figsize=(10, 5))
    plt.bar(names, quantities, color="#168a8a")
    plt.title("Current Medicine Stock")
    plt.xlabel("Medicine")
    plt.ylabel("Quantity")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.show()
    plt.close()


def open_sales_graph(parent):
    try:
        sales = fetch_all(
            "SELECT DATE_FORMAT(DATEOFBILL, '%Y-%m') AS Period, "
            "SUM(Subtotal) AS Revenue FROM bills GROUP BY Period ORDER BY Period"
        )
        costs = fetch_all(
            "SELECT DATE_FORMAT(b.DATEOFBILL, '%Y-%m') AS Period, "
            "SUM(i.BillQuantity * i.UnitCost) AS Cost "
            "FROM bills b JOIN bill_items i ON i.BillID = b.BillID "
            "GROUP BY Period ORDER BY Period"
        )
        expenses = fetch_all(
            "SELECT DATE_FORMAT(ExpenseDate, '%Y-%m') AS Period, "
            "SUM(Amount) AS Amount FROM expenses GROUP BY Period ORDER BY Period"
        )
    except (mysql.connector.Error, RuntimeError) as error:
        show_operation_error(error, parent)
        return
    periods = set()
    revenue_by_month = {}
    cost_by_month = {}
    expenses_by_month = {}
    for row in sales:
        periods.add(row["Period"])
        revenue_by_month[row["Period"]] = Decimal(str(row["Revenue"] or 0))
    for row in costs:
        periods.add(row["Period"])
        cost_by_month[row["Period"]] = Decimal(str(row["Cost"] or 0))
    for row in expenses:
        periods.add(row["Period"])
        expenses_by_month[row["Period"]] = Decimal(str(row["Amount"] or 0))
    if not periods:
        messagebox.showinfo("Sales graph", "There is no saved sales or expense data.", parent=parent)
        return
    labels = sorted(periods)
    revenue = [float(revenue_by_month.get(period, 0)) for period in labels]
    net_profit = [
        float(
            revenue_by_month.get(period, Decimal("0"))
            - cost_by_month.get(period, Decimal("0"))
            - expenses_by_month.get(period, Decimal("0"))
        )
        for period in labels
    ]
    plt.figure(figsize=(10, 5))
    plt.plot(labels, revenue, marker="o", label="Sales (before GST)")
    plt.plot(labels, net_profit, marker="o", label="Estimated profit / loss")
    plt.title("Monthly Sales and Estimated Profit / Loss")
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.xticks(rotation=35, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.close()


def open_stock_management(parent):
    open_record_manager(
        parent,
        "Stocks Entry",
        "stocks",
        STOCK_FIELDS,
        "BatchNo",
        ["BatchNo", "NameofMedicine"],
    )


def open_staff_management(parent):
    open_record_manager(
        parent,
        "Employee Entry",
        "staffinfo",
        STAFF_FIELDS,
        "EmpNo",
        ["EmpNo", "Name", "Designation"],
    )


def open_customer_management(parent):
    open_record_manager(
        parent,
        "Customer Entry",
        "customerinformation",
        CUSTOMER_FIELDS,
        "ID",
        ["ID", "NAME", "PhoneNumber"],
    )


def open_database_listing(parent, table_name, title, fields, key):
    columns = [
        (column, label, 150 if len(label) < 18 else 190)
        for column, label, _kind, _required in fields
    ]
    try:
        rows = fetch_all(
            "SELECT * FROM {} ORDER BY {}".format(table_name, key)
        )
    except (mysql.connector.Error, RuntimeError) as error:
        show_operation_error(error, parent)
        return
    open_table_window(parent, title, rows, columns)


def show_menu(root):
    for child in root.winfo_children():
        child.destroy()
    root.title("DPK Chemist Shop Management System")
    root.geometry("980x650")
    root.configure(bg="#17324d")

    tk.Label(
        root,
        text="DPK Chemist Shop",
        font=("Segoe UI", 26, "bold"),
        bg="#17324d",
        fg="white",
    ).pack(pady=(28, 4))
    tk.Label(
        root,
        text="Management System",
        font=("Segoe UI", 14),
        bg="#17324d",
        fg="#d8e6f3",
    ).pack(pady=(0, 20))

    panel = ttk.Frame(root, padding=18)
    panel.pack(fill="both", expand=True, padx=50, pady=12)
    options = [
        ("Stocks Entry", lambda: open_stock_management(root)),
        ("Today's Expired Products", lambda: open_expired_products(root)),
        ("Bills", lambda: open_billing(root)),
        ("Employee Entry", lambda: open_staff_management(root)),
        ("Customer Entry", lambda: open_customer_management(root)),
        ("Sales Graph", lambda: open_sales_graph(root)),
        ("Stock Graph", lambda: open_stock_graph(root)),
        ("Stocks Information", lambda: open_database_listing(
            root, "stocks", "Stocks Information", STOCK_FIELDS, "BatchNo"
        )),
        ("Employee Information", lambda: open_database_listing(
            root, "staffinfo", "Employee Information", STAFF_FIELDS, "EmpNo"
        )),
        ("Customer Information", lambda: open_database_listing(
            root, "customerinformation", "Customer Information",
            CUSTOMER_FIELDS, "ID"
        )),
        ("Expense Entry", lambda: open_expense_manager(root)),
    ]
    for index, (text, command) in enumerate(options):
        button = ttk.Button(panel, text=text, command=command)
        button.grid(row=index // 3, column=index % 3, sticky="nsew", padx=10, pady=10, ipady=14)
    for column in range(3):
        panel.columnconfigure(column, weight=1)
    for row in range(4):
        panel.rowconfigure(row, weight=1)

    footer = ttk.Frame(root, padding=(12, 4))
    footer.pack(fill="x", padx=45, pady=(0, 18))
    ttk.Button(
        footer, text="Exit menu", command=lambda: show_login(root)
    ).pack(side="left")
    ttk.Button(footer, text="Exit", command=root.destroy).pack(side="right")


def show_login(root):
    for child in root.winfo_children():
        child.destroy()
    root.title("Login - DPK Chemist Shop")
    root.geometry("600x420")
    root.configure(bg="#17324d")
    panel = ttk.Frame(root, padding=30)
    panel.place(relx=0.5, rely=0.5, anchor="center")
    ttk.Label(panel, text="Login Area", font=("Segoe UI", 22, "bold")).grid(
        row=0, column=0, columnspan=2, pady=(0, 20)
    )
    ttk.Label(panel, text="Username").grid(row=1, column=0, sticky="w", pady=8)
    username = ttk.Entry(panel, width=28)
    username.grid(row=1, column=1, pady=8)
    ttk.Label(panel, text="Password").grid(row=2, column=0, sticky="w", pady=8)
    password = ttk.Entry(panel, width=28, show="*")
    password.grid(row=2, column=1, pady=8)

    def login():
        entered_username = username.get()
        entered_password = password.get()
        if not entered_username or not entered_password:
            messagebox.showwarning(
                "Login", "Username and password cannot be blank.", parent=root
            )
            return
        if LOGIN_USERNAME is None or LOGIN_PASSWORD is None:
            messagebox.showerror(
                "Configuration",
                "Set LOGIN_USERNAME and LOGIN_PASSWORD in your local db_config.py.",
                parent=root,
            )
            return
        if hmac.compare_digest(
            entered_username.encode("utf-8"), str(LOGIN_USERNAME).encode("utf-8")
        ) and hmac.compare_digest(
            entered_password.encode("utf-8"), str(LOGIN_PASSWORD).encode("utf-8")
        ):
            show_menu(root)
        else:
            messagebox.showerror(
                "Login", "Incorrect username or password.", parent=root
            )
            password.delete(0, tk.END)

    ttk.Button(panel, text="Log in", command=login).grid(
        row=3, column=0, pady=20, padx=8
    )
    ttk.Button(panel, text="Exit", command=root.destroy).grid(
        row=3, column=1, pady=20, padx=8
    )
    password.bind("<Return>", lambda _event: login())


def show_welcome(root):
    root.title("Welcome")
    root.geometry("900x540")
    root.configure(bg="#17324d")
    tk.Label(
        root,
        text="Welcome to DPK Chemist Shop",
        font=("Segoe UI", 27, "bold"),
        bg="#17324d",
        fg="white",
    ).pack(expand=True, pady=(100, 8))
    tk.Label(
        root,
        text="Chemist Shop Management System",
        font=("Segoe UI", 16),
        bg="#17324d",
        fg="#d8e6f3",
    ).pack(pady=(0, 140))
    root.after(1800, lambda: show_login(root))


def main():
    root = tk.Tk()
    root.title("DPK Chemist Shop Management System")
    root.geometry("900x540")
    if CONFIG_IMPORT_ERROR is not None:
        messagebox.showerror(
            "Configuration file missing",
            "Copy db_config.example.py to db_config.py, enter your local "
            "database and login settings, then run the program again.\n\n"
            "Details: {}".format(CONFIG_IMPORT_ERROR),
            parent=root,
        )
        root.destroy()
        return
    show_welcome(root)
    root.mainloop()


if __name__ == "__main__":
    main()
