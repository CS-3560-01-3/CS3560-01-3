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


def add_account(phone_number, e_mail, address):
    """
    Adds a new buyer row to the database and returns the account ID used.
    """
    account_id = _get_next_id("account")
    connection = _get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO buyer (accountID, email, phoneNum, address)
            VALUES (%s, %s, %s, %s)
            """,
            (account_id, e_mail, phone_number, address),
        )
        connection.commit()
        refresh_id_counters()
        return account_id
    finally:
        cursor.close()
        connection.close()