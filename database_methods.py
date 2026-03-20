def add_account(name, password, phone_number, e_mail, address):
    """
    Adds new customer account to the database after inputting the necessary information.
    Generates a new account ID for the customer. Returns newly generated
    account ID.

    :param name: name of the customer creating the account
    :param password: password of the account being created
    :param phone_number: phone number of the customer
    :param e_mail: e-mail address of the customer
    :param address: physical address of the customer
    :return: returns account_id
    """
    pass

def view_account(account_id):
    """
    Searches the information of the account associated with the account id.
    Adds account details to a dictionary and returns it.

    :param account_id: ID of the account being viewed
    :return: returns account_details
    """
    pass

def update_account(account_id, name=None, password=None, phone_number=None, e_mail=None, address=None):
    """
    Updates account information of the account associated with the
    account id with optional parameters. If the parameters are empty,
    does not update the information. Returns whether update is successful.

    :param account_id: ID of the account being updates
    :param name: (optional) new name for the account
    :param password: (optional) new password for the account
    :param phone_number: (optional) new phone number for the account
    :param e_mail: (optional) new e-mail for the account
    :param address: (optional) new physical address for the account
    :return: returns is_successful
    """
    pass

def remove_account(account_id):
    """
    Removes the account associated with the account ID from the database.
    Returns whether removal was successful.

    :param account_id: ID of the account being removed
    :return: returns is_successful
    """
    pass

def add_product(product_name, description, price):
    """
    Adds new product to the database after inputting the necessary information.
    Generates a new product ID for the product. Returns newly generated product ID.

    :param product_name: name of the product being added
    :param description: brief description of the product
    :param price: price of the product
    :return: returns product_id
    """
    pass

def search_product(product_id):
    """
    Searches the information of the product associated with the product id.
    Adds product details to a dictionary and returns it.

    :param product_id: ID of the product being searched
    :return: returns product_details
    """
    pass

def update_product(product_id, product_name=None, description=None, price=None):
    """
    Updates product information of the product associated with the
    product id with optional parameters. If the parameters are empty,
    does not update the information. Returns whether update is successful.

    :param product_id: ID of the product being updated
    :param product_name: (optional) new name for the product
    :param description: (optional) new description of the product
    :param price: (optional) new price of the product
    :return: returns is_successful
    """
    pass

def remove_product(product_id):
    """
    Sets the product associated with the product ID as ignored by the database.
    Returns whether removal was successful.

    :param product_id: ID of the product being removed
    :return: returns is_successful
    """
    pass

def create_customer_order(account_id, product_ids, product_quantities):
    """
    Creates customer order using product IDs and quantities,
    then generates a customer order ID. Associates the created
    customer order with the customer account. Returns newly
    generated order ID.

    :param account_id: ID of the customer account associated with the order
    :param product_ids: list of product IDs to add to order
    :param product_quantities: list of product quantities to add to order
    :return: returns new customer_order_id
    """
    pass

def search_customer_order(customer_order_id):
    """
    Searches the information of the customer order associated with the
    customer order id. Adds customer order details to a dictionary
    and returns it.

    :param customer_order_id: ID of the order being searched.
    :return: returns customer_order_details
    """
    pass

def remove_customer_order(customer_order_id):
    """
    Sets the customer order associated with the customer order id to be
    ignored by the database. Returns whether removal was successful.

    :param customer_order_id: ID of the order being removed
    :return: returns None
    """
    pass

def create_purchase_order(product_id, product_quantity):
    """
    Creates purchase order of the product associated with the product id
    and the quantity of the product being purchased. Sends notification to
    an outside supplier for purchase. Generates purchase order ID
    and returns it.

    :param product_id: ID of the product being ordered
    :param product_quantity: quantity of the product being ordered
    :return: returns new purchase_order_id
    """
    pass

def search_purchase_order(purchase_order_id):
    """
    Searches the information of the purchase order associated with the
    purchase order id. Adds purchase order details to a dictionary
    and returns it.

    :param purchase_order_id: ID of the order being searched.
    :return: returns purchase_order_details
    """
    pass

def cancel_purchase_order(purchase_order_id):
    """
    Sends cancel notification to the supplier of the purchase order.
    Updates the purchase order to be ignored by the database. Returns
    whether cancellation was successful.

    :param purchase_order_id: ID of the order being canceled
    :return: returns is_successful
    """

    pass

def update_inventory(product_id, quantity):
    """
    Updates product inventory to add or remove stock. Calls
    low_stock_alert() to determine whether the product stock
    is too low after the update. Returns whether update was successful.

    :param product_id: ID of the product to update
    :param quantity: quantity of the product (can be positive or negative)
    :return: returns is_successful
    """
    pass

def low_stock_alert(product_id):
    """
    Alerts the owner if the product stock is below a certain
    threshold, which is stored in the product information. Returns
    whether alert was issued.

    :param product_id: ID of the product to check
    :return: returns is_low
    """
    pass

def view_sales_report(date_start, date_end):
    """
    Goes through every completed sale within the set time frame. Returns
    information on the overall sales performance on that timeframe as a dictionary.
    Returns information such as sales number, total revenue, and total profit.

    :param date_start: start date of sales to view in database
    :param date_end: end date of sales to view in database
    :return: returns sales_report
    """
    pass

def process_transaction(customer_order_id):
    """
    Updates customer order status after customer payment. Records transaction
    and changes status to 'paid' if payment is approved.
    Notifies customer and stays as 'pending' if not approved. Returns
    whether transaction was successful.

    :param customer_order_id: ID of the customer order being processed
    :return: returns is_successful
    """
    pass

def ship_customer_order(customer_order_id, tracking_number, ship_date, carrier):
    """
    Updates customer order status after product shipment. Creates and records
    shipment information, then notifies customer of the shipment. Calls
    update_inventory() to update the number of products available after shipment
    using customer order information. Returns newly generated shipment ID.

    :param customer_order_id: ID of the customer order being shipped
    :param tracking_number: tracking number of the shipment
    :param ship_date: the date the order is shipped
    :param carrier: the carrier assigned to the shipment
    :return: returns new shipment_id
    """
    pass

def receive_purchase_order(purchase_order_id):
    """
    Calls update_inventory() to update product quantity after product
    shipment is received. Updates purchase order to 'received'. Returns whether
    update is successful.

    :param purchase_order_id: ID of the purchase order being received
    :return: returns is_successful
    """
    pass


