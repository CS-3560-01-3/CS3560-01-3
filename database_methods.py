import os

import mysql.connector


def _get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "01072005"),
        database=os.getenv("DB_NAME", "basic_business_backend"),
    )


ID_TABLES = {
    "buyer": "account",
    "category": "category",
    "item": "item",
    "order": "order",
    "payment": "payment",
    "supplier": "supplier",
}

ID_COUNTS = {
    "account": 0,
    "category": 0,
    "item": 0,
    "order": 0,
    "payment": 0,
    "supplier": 0,
}

NEXT_IDS = {
    "account": 1,
    "category": 1,
    "item": 1,
    "order": 1,
    "payment": 1,
    "supplier": 1,
}


def refresh_id_counters():
    connection = _get_connection()
    cursor = connection.cursor()
    try:
        for table_name, counter_name in ID_TABLES.items():
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            count = cursor.fetchone()[0]
            ID_COUNTS[counter_name] = count
            NEXT_IDS[counter_name] = count + 1

        return {
            "counts": ID_COUNTS.copy(),
            "next_ids": NEXT_IDS.copy(),
        }
    finally:
        cursor.close()
        connection.close()


try:
    refresh_id_counters()
except mysql.connector.Error:
    pass


def _get_next_id(counter_name):
    refresh_id_counters()
    return NEXT_IDS[counter_name]


def add_account(phone_number, e_mail, password, address):
    """
    Adds a new buyer row to the database and returns the account ID used.
    """
    account_id = _get_next_id("account")
    connection = _get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO buyer (accountID, email, phoneNum, passw, address)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (account_id, e_mail, phone_number, password, address),
        )
        connection.commit()
        refresh_id_counters()
        return account_id
    finally:
        cursor.close()
        connection.close()

def view_account(account_id):
    """
    Returns the buyer row for the given account ID.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM buyer WHERE accountID = %s", (account_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def update_account(account_id, phone_number=None, e_mail=None, password=None, address=None):
    """
    Updates buyer contact information.
    """
    fields = {
        "phoneNum": phone_number,
        "email": e_mail,
        "passw": password,
        "address": address,
    }
    updates = [(column, value) for column, value in fields.items() if value is not None]

    if not updates:
        return False

    set_clause = ", ".join(f"{column} = %s" for column, _ in updates)
    values = [value for _, value in updates]
    values.append(account_id)

    connection = _get_connection()
    cursor = connection.cursor()
    try:
        query = f"UPDATE buyer SET {set_clause} WHERE accountID = %s"
        cursor.execute(query, tuple(values))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        connection.close()


def remove_account(account_id):
    """
    Deletes a buyer row by account ID.
    """
    connection = _get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM buyer WHERE accountID = %s", (account_id,))
        connection.commit()
        refresh_id_counters()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        connection.close()

def login(e_mail, password):
    """
    Verifies login credentials and returns the account ID if valid.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT accountID, passw FROM buyer WHERE email = %s", (e_mail,))
        result = cursor.fetchone()
        if result and result.get("passw") == password:
            return result["accountID"]
        else:
            return None
    finally:
        cursor.close()
        connection.close()