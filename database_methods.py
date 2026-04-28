"""
Database helper functions for the basic business backend.

This module centralizes the MySQL connection setup and provides small CRUD-style
helpers for buyers, items, orders, and payments. Each function opens its own
connection, commits or rolls back its own transaction, and closes database
resources in a `finally` block so callers do not need to manage cursors directly.
"""

import os

import mysql.connector


def _get_connection():
    """
    Create and return a new MySQL database connection.

    Connection values are read from environment variables when available, with
    local-development defaults used as a fallback. Each public helper calls this
    function so every operation gets a fresh connection.
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "01072005"),
        database=os.getenv("DB_NAME", "basic_business_backend"),
    )


# Maps physical table names to the keys used by the ID counter dictionaries.
ID_TABLES = {
    "buyer": "account",
    "category": "category",
    "item": "item",
    "order": "order",
    "payment": "payment",
    "supplier": "supplier",
}

# Stores the current number of rows in each tracked table.
ID_COUNTS = {
    "account": 0,
    "category": 0,
    "item": 0,
    "order": 0,
    "payment": 0,
    "supplier": 0,
}

# Stores the next manual ID value to use for tables that do not rely on
# AUTO_INCREMENT in this code.
NEXT_IDS = {
    "account": 1,
    "category": 1,
    "item": 1,
    "order": 1,
    "payment": 1,
    "supplier": 1,
}


def refresh_id_counters():
    """
    Recalculate row counts and next manual IDs for tracked tables.

    Returns:
        dict: Copies of the updated `ID_COUNTS` and `NEXT_IDS` dictionaries.

    Note:
        This uses `COUNT(*) + 1` as the next ID. That works only when IDs are
        sequential with no gaps. If rows are deleted, this can reuse an existing
        ID. AUTO_INCREMENT columns are usually safer for production systems.
    """
    connection = _get_connection()
    cursor = connection.cursor()
    try:
        for table_name, counter_name in ID_TABLES.items():
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            count = cursor.fetchone()[0]
            ID_COUNTS[counter_name] = count
            NEXT_IDS[counter_name] = count + 1

        # Return copies so callers cannot accidentally mutate the globals.
        return {
            "counts": ID_COUNTS.copy(),
            "next_ids": NEXT_IDS.copy(),
        }
    finally:
        cursor.close()
        connection.close()


# Try to initialize counters when the module is imported. If the database is not
# running yet, allow the import to succeed and refresh counters later on demand.
try:
    refresh_id_counters()
except mysql.connector.Error:
    pass


def _get_next_id(counter_name):
    """
    Refresh counters and return the next manual ID for a tracked entity.

    Args:
        counter_name (str): Key from `NEXT_IDS`, such as "account" or "payment".

    Returns:
        int: The next ID currently calculated for that entity.
    """
    refresh_id_counters()
    return NEXT_IDS[counter_name]


def add_account(phone_number, e_mail, address, password=None):
    """
    Insert a new buyer account.

    Args:
        phone_number (str): Buyer's phone number.
        e_mail (str): Buyer's email address.
        address (str): Buyer's mailing or shipping address.
        password (str | None): Optional account password to store in `passw`.

    Returns:
        int: The account ID assigned to the inserted buyer.
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
    Fetch one buyer account by ID.

    Args:
        account_id (int): Buyer account ID.

    Returns:
        dict | None: Buyer row as a dictionary, or None if no account exists.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM buyer WHERE accountID = %s", (account_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def login_account(e_mail, password):
    """
    Check buyer login credentials.

    Args:
        e_mail (str): Email address entered by the user.
        password (str): Password entered by the user.

    Returns:
        tuple | None: Matching account row when credentials are valid; otherwise None.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM buyer WHERE email = %s", (e_mail,))
        result = cursor.fetchone()
        if result and result.get("passw") == password:
            return result
        else:
            return None
    finally:
        cursor.close()
        connection.close()


def update_account(account_id, phone_number=None, e_mail=None, address=None):
    """
    Update selected contact fields for a buyer account.

    Only arguments that are not None are included in the SQL UPDATE statement.

    Args:
        account_id (int): Buyer account to update.
        phone_number (str | None): New phone number, if changing it.
        e_mail (str | None): New email address, if changing it.
        address (str | None): New address, if changing it.

    Returns:
        bool: True if a row was updated; False if no fields were provided or no
        matching account was found.
    """
    fields = {
        "phoneNum": phone_number,
        "email": e_mail,
        "address": address,
    }
    updates = [(column, value) for column, value in fields.items() if value is not None]

    if not updates:
        return False

    # Build the SET clause from trusted column names while keeping values
    # parameterized to avoid SQL injection.
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
    Delete one buyer account by ID.

    Args:
        account_id (int): Buyer account ID to delete.

    Returns:
        bool: True if a row was deleted; otherwise False.
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


def view_category(category_id):
    """
    Fetch one category by ID.

    Args:
        category_id (int): Category ID.

    Returns:
        dict | None: Category row as a dictionary, or None if not found.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM category WHERE categoryID = %s", (category_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def search_item(item_id):
    """
    Fetch one item by ID.

    Args:
        item_id (int): Item ID.

    Returns:
        dict | None: Item row as a dictionary, or None if no item exists.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM item WHERE itemID = %s", (item_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


# Backward-compatible aliases for callers that use product/item terminology.
search_product = search_item
view_item = search_item


def update_inventory(item_id, quantity):
    """
    Add to or subtract from an item's stock value.

    Args:
        item_id (int): Item to update.
        quantity (int): Amount to add. Use a negative number to reduce stock.

    Returns:
        bool: True if stock was updated; False if the item does not exist or the
        update would make stock negative.
    """
    connection = _get_connection()
    cursor = connection.cursor()
    try:
        # The WHERE condition prevents stock from dropping below zero.
        cursor.execute(
            """
            UPDATE item
            SET stock = stock + %s
            WHERE itemID = %s AND stock + %s >= 0
            """,
            (quantity, item_id, quantity),
        )

        if cursor.rowcount == 0:
            connection.rollback()
            return False

        connection.commit()
        low_stock_alert(item_id)
        return True
    finally:
        cursor.close()
        connection.close()


def low_stock_alert(item_id):
    """
    Check whether an item's stock is at or below its reorder threshold.

    Args:
        item_id (int): Item to check.

    Returns:
        bool: True if stock is less than or equal to threshold; False if the item
        does not exist or is above threshold.
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
    Create an order, add order-item rows, and reduce inventory stock.

    Args:
        account_id (int): Buyer placing the order.
        item_ids (list[int]): Item IDs being purchased.
        item_quantities (list[int]): Quantities matching `item_ids` by position.

    Returns:
        int | None: New order ID when successful; None if validation fails, stock
        is insufficient, or a database error occurs.

    Transaction behavior:
        The order insert, orderitem inserts, and stock updates are committed as
        one transaction. If any validation or SQL step fails, the transaction is
        rolled back so partial orders are not saved.
    """
    if not item_ids or len(item_ids) != len(item_quantities):
        return None

    if any(quantity <= 0 for quantity in item_quantities):
        return None

    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Make sure the buyer exists before creating an order for them.
        cursor.execute("SELECT accountID FROM buyer WHERE accountID = %s", (account_id,))
        if cursor.fetchone() is None:
            connection.rollback()
            return None

        items = []
        for item_id, quantity in zip(item_ids, item_quantities):
            # Lock each item row during the transaction so another order cannot
            # read the same stock and oversell it before this order commits.
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
                INSERT INTO order_item (orderID, itemID, itemQuantity)
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
    Fetch one order by ID.

    Args:
        order_id (int): Order ID.

    Returns:
        dict | None: Order row as a dictionary, or None if not found.
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
    Fetch all line items for an order.

    Args:
        order_id (int): Order ID.

    Returns:
        list[dict]: Zero or more orderitem rows for the order.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM order_item WHERE orderID = %s", (order_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def add_payment(account_id, card_num, expiration, pin):
    """
    Insert a payment method for a buyer account.

    Args:
        account_id (int): Buyer account that owns this payment method.
        card_num (str): Card number to store.
        expiration (str): Card expiration value.
        pin (str): Card PIN value.

    Returns:
        int: The payment ID assigned to the inserted row.
    """
    payment_id = _get_next_id("payment")
    connection = _get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO payment (paymentID, accountID, cardNum, expiration, pin)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (payment_id, account_id, card_num, expiration, pin),
        )
        connection.commit()
        refresh_id_counters()
        return payment_id
    finally:
        cursor.close()
        connection.close()


def view_payment(payment_id):
    """
    Fetch one payment method by ID.

    Args:
        payment_id (int): Payment ID.

    Returns:
        dict | None: Payment row as a dictionary, or None if not found.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM payment WHERE paymentID = %s", (payment_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def update_payment(payment_id, account_id=None, card_num=None, expiration=None, pin=None):
    """
    Update selected fields for a payment method.

    Only arguments that are not None are included in the SQL UPDATE statement.

    Args:
        payment_id (int): Payment row to update.
        account_id (int | None): New owning account ID, if changing it.
        card_num (str | None): New card number, if changing it.
        expiration (str | None): New expiration value, if changing it.
        pin (str | None): New PIN value, if changing it.

    Returns:
        bool: True if a row was updated; False if no fields were provided or no
        matching payment row was found.
    """
    fields = {
        "accountID": account_id,
        "cardNum": card_num,
        "expiration": expiration,
        "pin": pin,
    }
    updates = [(column, value) for column, value in fields.items() if value is not None]

    if not updates:
        return False

    # Build the SET clause from fixed column names and pass all user-provided
    # values separately as query parameters.
    set_clause = ", ".join(f"{column} = %s" for column, _ in updates)
    values = [value for _, value in updates]
    values.append(payment_id)

    connection = _get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"UPDATE payment SET {set_clause} WHERE paymentID = %s",
            tuple(values),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        connection.close()


def remove_payment(payment_id):
    """
    Delete one payment method by ID.

    Args:
        payment_id (int): Payment ID to delete.

    Returns:
        bool: True if a row was deleted; otherwise False.
    """
    connection = _get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM payment WHERE paymentID = %s", (payment_id,))
        connection.commit()
        refresh_id_counters()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        connection.close()
