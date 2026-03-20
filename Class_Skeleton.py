class Account:
    def __init__(self, acc_num: int, email: str, phone_num: str, address: str):
        self.acc_num = acc_num
        self.email = email
        self.phone_num = phone_num
        self.address = address


class Buyer(Account): # inherits from Account
    def __init__(self, acc_num: int, email: str, phone_num: str, address: str, payment: str):
        super().__init__(acc_num, email, phone_num, address)
        self.payment = payment
        self.cart = []            # list of item_ids
        self.orders = []          # list of order_ids



class Inventory:
    def __init__(self):
        self.stock = {}           # dictioanry of item_ids. Key -> item_id, Value -> quantity
        self.restock_threshold = {}



class Item:
    def __init__(self, item_id: int, name: str, description: str, price: float, market_val: float):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.price = price
        self.market_val = market_val
       


class Order:
    def __init__(self, order_num: int, acc_num: int, item_ids: list[int], item_quantities: list[int], order_date: str, order_status: str):
        self.order_num = order_num
        self.acc_num = acc_num
        self.item_ids = item_ids
        self.item_quantities = item_quantities
        self.order_date = order_date
        self.order_status = order_status


