"""Copy this file to db_config.py and enter values for your local setup.

DB_CONFIG connects to the MySQL Server. The account must be able to access
ip_project2022; use a database account with only the permissions the app needs.
The LOGIN values are separate credentials for the application's login screen.
"""

DB_CONFIG = {
    "host": "localhost",  # MySQL Server computer; localhost for this PC.
    "user": "your_mysql_username",  # Your MySQL account name.
    "password": "your_mysql_password",  # That MySQL account's password.
    "database": "ip_project2022",  # Created by database.sql.
}

# This local login is a basic screen-level gate for the school project.
# Choose your own values; they are not MySQL credentials.
LOGIN_USERNAME = "change_this_username"
LOGIN_PASSWORD = "change_this_password"
