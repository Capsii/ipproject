import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import mysql.connector

import ip_project


class Entry:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeCursor:
    def __init__(self, error=None):
        self.error = error
        self.rowcount = 1
        self.closed = False

    def execute(self, query, parameters=()):
        if self.error:
            raise self.error
        self.query = query
        self.parameters = parameters

    def fetchall(self):
        return [{"value": 1}]

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, error=None):
        self.fake_cursor = FakeCursor(error)
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self, dictionary=False):
        self.dictionary_cursor = dictionary
        return self.fake_cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class HelperTests(unittest.TestCase):
    def test_round_money_uses_two_decimal_places(self):
        self.assertEqual(ip_project.round_money(Decimal("2.675")), Decimal("2.68"))

    def test_round_money_rejects_non_finite_amount(self):
        with self.assertRaises(ValueError):
            ip_project.round_money(Decimal("NaN"))

    def test_parse_value_validates_date_and_optional_blank(self):
        parsed_date = ip_project.parse_value(
            Entry("2026-02-28"), "Expiry date", "date", True
        )
        self.assertEqual(parsed_date, date(2026, 2, 28))
        self.assertIsNone(ip_project.parse_value(Entry(""), "Optional", "text", False))

    def test_read_form_rejects_manufacture_date_after_expiry(self):
        values = {
            "BatchNo": "00001",
            "ExpiryDate": "2027-01-01",
            "NameofMedicine": "Example",
            "Quantity": "5",
            "Price": "12.50",
            "CostPrice": "7.25",
            "ManufacturerName": "",
            "ManufacturerPhoneNo": "",
            "MfgDate": "2028-01-01",
        }
        entries = {name: Entry(value) for name, value in values.items()}
        with self.assertRaises(ValueError):
            ip_project.read_form(ip_project.STOCK_FIELDS, entries, "stocks")

    def test_fetch_all_closes_connection_and_cursor(self):
        connection = FakeConnection()
        with patch("ip_project.connect_database", return_value=connection):
            rows = ip_project.fetch_all("SELECT value FROM sample")
        self.assertEqual(rows, [{"value": 1}])
        self.assertTrue(connection.dictionary_cursor)
        self.assertTrue(connection.fake_cursor.closed)
        self.assertTrue(connection.closed)

    def test_execute_write_commits_successful_change(self):
        connection = FakeConnection()
        with patch("ip_project.connect_database", return_value=connection):
            changed = ip_project.execute_write(
                "UPDATE sample SET value = %s", (2,)
            )
        self.assertEqual(changed, 1)
        self.assertEqual(connection.commits, 1)
        self.assertEqual(connection.rollbacks, 0)
        self.assertTrue(connection.closed)

    def test_execute_write_rolls_back_and_surfaces_database_error(self):
        connection = FakeConnection(mysql.connector.Error("test failure"))
        with patch("ip_project.connect_database", return_value=connection):
            with self.assertRaises(mysql.connector.Error):
                ip_project.execute_write("UPDATE sample SET value = %s", (2,))
        self.assertEqual(connection.commits, 0)
        self.assertEqual(connection.rollbacks, 1)
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
