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


def search_item(item_id):
    """
    Returns the item row for the given item ID.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM item WHERE itemID = %s", (item_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def low_stock_alert(item_id):
    """
    Returns True when an item's stock is at or below its threshold.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT stock, threshold FROM item WHERE itemID = %s",
            (item_id,),
        )
        item = cursor.fetchone()
        if item is None:
            return False

        return item["stock"] <= item["threshold"]
    finally:
        cursor.close()
        connection.close()


def create_order(account_id, item_ids, item_quantities):
    """
    Creates an order and matching orderitem rows using the basic_schema tables.
    """
    if not item_ids or len(item_ids) != len(item_quantities):
        return None

    if any(quantity <= 0 for quantity in item_quantities):
        return None

    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT accountID FROM buyer WHERE accountID = %s", (account_id,))
        if cursor.fetchone() is None:
            connection.rollback()
            return None

        items = []
        for item_id, quantity in zip(item_ids, item_quantities):
            cursor.execute(
                """
                SELECT itemID, stock
                FROM item
                WHERE itemID = %s
                FOR UPDATE
                """,
                (item_id,),
            )
            item = cursor.fetchone()
            if item is None or item["stock"] < quantity:
                connection.rollback()
                return None
            items.append(item)

        cursor.execute(
            "INSERT INTO `order` (accountID, purchaseDate) VALUES (%s, CURDATE())",
            (account_id,),
        )
        order_id = cursor.lastrowid

        for item, quantity in zip(items, item_quantities):
            cursor.execute(
                """
                INSERT INTO orderitem (orderID, itemID, itemQuantity)
                VALUES (%s, %s, %s)
                """,
                (order_id, item["itemID"], quantity),
            )
            cursor.execute(
                "UPDATE item SET stock = stock - %s WHERE itemID = %s",
                (quantity, item["itemID"]),
            )

        connection.commit()
        return order_id
    except mysql.connector.Error:
        connection.rollback()
        return None
    finally:
        cursor.close()
        connection.close()


def view_order(order_id):
    """
    Returns the order row for the given order ID.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `order` WHERE orderID = %s", (order_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def view_order_items(order_id):
    """
    Returns all orderitem rows for a given order ID.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM orderitem WHERE orderID = %s", (order_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


