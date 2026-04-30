"""
CS 3560 E-Commerce GUI (MySQL-backed)

# High-level description:
# This is a GUI-based e-commerce application built with Tkinter.
# It connects to a MySQL database and uses helper functions
# from database_methods.py to perform all database operations.

# Notes about schema:
# - buyer table uses `passw` for password
# - item uses `itemName` (not `name`)
# - no price column exists in item
# - payment expiration is stored as DATE

# Backend functions used:
# These abstract all SQL logic so the GUI never directly runs SQL queries.

# Requirements:
# - mysql-connector-python installed
# - MySQL server running
# - database 'basic_business_backend' must exist
# - connection settings defined either in database_methods.py or env vars
"""

"""
CS 3560 E-Commerce GUI (MySQL-backed)

Matches the latest schema on the team GitHub (with the `passw` column on
buyer, `itemName` on item, no `price` column on item, and DATE-typed
`expiration` on payment). All database interaction goes through the
helpers in database_methods.py:

    add_account, view_account, login_account, update_account,
    remove_account, view_category, search_item, update_inventory,
    low_stock_alert, create_order, view_order, view_order_items,
    add_payment, view_payment, update_payment, remove_payment,
    refresh_id_counters, ID_COUNTS

Requirements on the user's machine:
    pip install mysql-connector-python
    A running MySQL server with the `basic_business_backend` schema.
    Connection settings come from database_methods.py (host, user,
    password, database) or DB_* environment variables.
"""

import re                      # Used for regex validation (email, card cleanup)
import mysql.connector        # MySQL connection driver
from datetime import datetime # Used for validating date formats
from tkinter import Tk, Toplevel, StringVar, END, messagebox, simpledialog
from tkinter import ttk       # Tkinter themed widgets (modern UI)
import database_methods as db



'''
# Hardcoded connection test to verify database + tables exist

host="127.0.0.1"
user="root"
conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="YourNewPassword123!",
    database="basic_business_backend"
)

cursor = conn.cursor()
cursor.execute("SHOW TABLES")

print("Tables seen by Python:")
for t in cursor:
    print(t)

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="YourNewPassword123!"
    )
    print("Connected!")
except Exception as e:
    print("Error:", e)

'''


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))

'''
Checks:

Has @
Has domain
No spaces
'''


def valid_date(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False

'''
Ensures format: YYYY-MM-DD
'''

def item_name(item_row) -> str:
    """Prefer `itemName` per the current schema, with fallbacks."""
    if not item_row:
        return "?"
    return (item_row.get("itemName") or item_row.get("name")
            or f"Item #{item_row.get('itemID', '?')}")

'''
Handles schema differences:

prefers itemName
fallback to name
fallback to Item #ID
'''

def check_db_connection():
    """Try a connection up front so the user gets a clear error."""
    try:
        conn = db._get_connection()
        conn.close()
    except mysql.connector.Error as e:
        raise SystemExit(
            "Could not connect to MySQL.\n\n"
            f"Error: {e}\n\n"
            "Check that MySQL is running and that the host/user/password/"
            "database in database_methods.py (or DB_HOST, DB_USER, "
            "DB_PASSWORD, DB_NAME env vars) are correct."
        )
    
'''
Called at program start:

Tries connecting using backend config
If it fails → exits with clear error
'''


def iter_ids(counter_name):
    """Yield 1..N for a given counter, refreshing from the DB first."""
    try:
        db.refresh_id_counters()
    except mysql.connector.Error:
        pass
    count = db.ID_COUNTS.get(counter_name, 0)
    return range(1, count + 1)

'''
Used everywhere instead of SQL queries like SELECT *

Gets max IDs from backend
Iterates 1 → N
Used to loop through records
'''


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------



class StoreApp:
    """Top-level controller. Manages login, main window, and cart state."""

    def __init__(self, root: Tk):
        self.root = root
        self.root.title("CS 3560 E-Commerce (MySQL)")
        self.root.geometry("1000x650")

        self.account_id = None       # int, the logged-in buyer
        self.account = None          # dict from view_account()
        self.cart = {}               # itemID -> quantity

        self._style()
        self._show_login()

    '''
    window size/title
    logged-in user (account_id)
    cart (dictionary: itemID → quantity)
    '''    

    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", padding=6, relief="raised")
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", font=("Segoe UI", 11, "bold"))

    '''
    Defines style of various ttk objects
    button styling
    header styling
    sub-label styling
    '''

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ==== LOGIN / REGISTER ===============================================
    def _show_login(self):
        self._clear()
        frame = ttk.Frame(self.root, padding=40, relief="raised")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(frame, text="CS 3560 E-Commerce",
                  style="Header.TLabel").grid(row=0, column=0, columnspan=2,
                                              pady=(0, 20))

        ttk.Label(frame, text="Email:").grid(row=1, column=0, sticky="e",
                                             padx=5, pady=5)
        email_v = StringVar()
        ttk.Entry(frame, textvariable=email_v,
                  width=30).grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky="e",
                                                padx=5, pady=5)
        pw_v = StringVar()
        ttk.Entry(frame, textvariable=pw_v, width=30,
                  show="*").grid(row=2, column=1, pady=5)
        
        '''
        Shows login screen. has:
        email input
        password input
        login button
        create account button
        '''

        def do_login():
            email = email_v.get().strip()
            pw = pw_v.get()
            if not email or not pw:
                messagebox.showerror("Error", "Fill in both fields.")
                return
            try:
                row = db.login_account(email, pw)
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))
                return
            if not row:
                messagebox.showerror("Login failed",
                                     "Invalid email or password.")
                return
            self.account_id = row["accountID"]
            self.account = row
            self.cart = {}
            self._show_main()

        '''
        Validate inputs
        Call db.login_account
        If valid:
        store account info
        reset cart
        go to main UI
        '''

        ttk.Button(frame, text="Log In", cursor="hand2", 
                   command=do_login).grid(row=3, column=0, columnspan=2,
                                          pady=(15, 5), sticky="ew")
        ttk.Button(frame, text="Create Account", cursor="hand2", 
                   command=self._show_create_account).grid(
            row=4, column=0, columnspan=2, pady=5, sticky="ew")

    def _show_create_account(self):
        win = Toplevel(self.root)
        win.title("Create Account")
        win.geometry("440x400")
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win, padding=20)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Create a new account",
                  style="Header.TLabel").pack(pady=(0, 15))

        fields = {}
        for label, show in (("Email", None), ("Password", "*"),
                            ("Phone", None), ("Address", None)):
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label + ":", width=12,
                      anchor="e").pack(side="left")
            v = StringVar()
            entry = ttk.Entry(row, textvariable=v)
            if show:
                entry.config(show=show)
            entry.pack(side="left", fill="x", expand=True)
            fields[label] = v
        
        '''
        Submit logic 

        Validate:
            - all fields filled
            - email format
            - password length
        Check duplicate email
        Call:
        '''

        def submit():
            email = fields["Email"].get().strip()
            pw = fields["Password"].get()
            phone = fields["Phone"].get().strip()
            address = fields["Address"].get().strip()

            if not email or not pw or not phone or not address:
                messagebox.showerror("Error", "All fields are required.",
                                     parent=win)
                return
            if not valid_email(email):
                messagebox.showerror("Error", "Invalid email format.",
                                     parent=win)
                return
            if len(pw) < 4:
                messagebox.showerror(
                    "Error", "Password must be at least 4 characters.",
                    parent=win)
                return

            # Check for duplicate email via login_account() — a matching
            # email is enough to reject even if the password differs.
            try:
                # There's no "lookup by email" helper in the backend, but
                # we can try logging in with whatever password the user
                # entered and additionally scan for a same-email row.
                existing = None
                for aid in iter_ids("account"):
                    row = db.view_account(aid)
                    if row and row.get("email") == email:
                        existing = row
                        break
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e), parent=win)
                return

            if existing:
                messagebox.showerror(
                    "Error", "An account with that email already exists.",
                    parent=win)
                return

            try:
                account_id = db.add_account(phone, email, address,
                                            password=pw)
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e), parent=win)
                return

            messagebox.showinfo(
                "Success",
                f"Account created!\nAccount ID: {account_id}\n"
                "You can now log in with your email and password.",
                parent=win)
            win.destroy()

        ttk.Button(frm, text="Create Account", cursor="hand2", 
                   command=submit).pack(pady=(15, 0), fill="x")

    # ==== MAIN WINDOW ====================================================
    def _show_main(self):
        self._clear()

        top = ttk.Frame(self.root, padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(
            top,
            text=f"Logged in: {self.account.get('email', '-')}",
            style="Sub.TLabel"
        ).pack(side="left")
        ttk.Button(top, text="Logout", cursor="hand2", command=self._logout).pack(side="right")

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.shop_tab = ttk.Frame(nb)
        self.cart_tab = ttk.Frame(nb)
        self.orders_tab = ttk.Frame(nb)
        self.account_tab = ttk.Frame(nb)
        self.payment_tab = ttk.Frame(nb)
        self.inv_tab = ttk.Frame(nb)

        nb.add(self.shop_tab, text="Shop")
        nb.add(self.cart_tab, text="Cart (0)")
        nb.add(self.orders_tab, text="My Orders")
        nb.add(self.account_tab, text="My Account")
        nb.add(self.payment_tab, text="Payments")
        nb.add(self.inv_tab, text="Inventory")

        self.nb = nb
        self._build_shop(self.shop_tab)
        self._build_cart(self.cart_tab)
        self._build_orders(self.orders_tab)
        self._build_account(self.account_tab)
        self._build_payments(self.payment_tab)
        self._build_inventory(self.inv_tab)

        nb.bind("<Motion>", self.on_mouse_move)

    '''
    Creates tabs:

    Shop
    Cart
    Orders
    Account
    Payments
    Inventory
    '''

    def _refresh_cart_tab_label(self):
        if hasattr(self, "nb"):
            self.nb.tab(1, text=f"Cart ({sum(self.cart.values())})")

    def _logout(self):
        self.account_id = None
        self.account = None
        self.cart.clear()
        self._show_login()

    def on_mouse_move(self, event):
        element = event.widget.identify(event.x, event.y)
        if "label" in element or "tab" in element:
            event.widget.config(cursor="hand2")
        else:
            event.widget.config(cursor="")

    # ==== SHOP ===========================================================
    def _build_shop(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", padx=5, pady=5)

        ttk.Label(bar, text="Search (name contains):").pack(side="left")
        search_v = StringVar()
        entry = ttk.Entry(bar, textvariable=search_v, width=30)
        entry.pack(side="left", padx=5)

        cols = ("id", "name", "category", "stock")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=15)
        headings = {"id": "ID", "name": "Item",
                    "category": "Category", "stock": "Stock"}
        widths = {"id": 50, "name": 380, "category": 180, "stock": 100}
        for c in cols:
            tree.heading(c, text=headings[c])
            tree.column(c, width=widths[c],
                        anchor="w" if c == "name" else "center")
        tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        '''
        search items
        view items
        add to cart
        '''

        def refresh():
            for r in tree.get_children():
                tree.delete(r)
            term = search_v.get().strip().lower()
            for item_id in iter_ids("item"):
                item = db.search_item(item_id)
                if not item:
                    continue
                name = item_name(item)
                if term and term not in name.lower():
                    continue
                stock = item.get("stock", 0)
                if stock <= 0:
                    continue
                cat_id = item.get("categoryID")
                cat_name = "-"
                if cat_id:
                    cat = db.view_category(cat_id)
                    if cat:
                        cat_name = (cat.get("categoryName")
                                    or cat.get("name") or "-")
                tree.insert("", END, values=(item_id, name, cat_name, stock))

        '''
        Loops through all items:

        filters by search
        displays:
        name
        category
        stock
        '''

        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=5, pady=5)
        ttk.Button(btns, text="Search", cursor="hand2", command=refresh).pack(side="left",
                                                              padx=3)
        ttk.Button(btns, text="View Details", cursor="hand2", 
                   command=lambda: self._view_item_details(tree)).pack(
            side="left", padx=3)
        ttk.Button(btns, text="Add to Cart", cursor="hand2", 
                   command=lambda: self._add_to_cart(tree)).pack(
            side="left", padx=3)
        ttk.Button(btns, text="Refresh", cursor="hand2", 
                   command=refresh).pack(side="right", padx=3)
        entry.bind("<Return>", lambda _e: refresh())

        refresh()

    def _view_item_details(self, tree):
        sel = tree.focus()
        if not sel:
            messagebox.showinfo("Info", "Select an item first.")
            return
        item_id = int(tree.item(sel)["values"][0])
        item = db.search_item(item_id)
        if not item:
            messagebox.showerror("Error", "Item not found.")
            return
        cat = None
        if item.get("categoryID"):
            cat = db.view_category(item["categoryID"])

        lines = [f"Item #{item_id} — {item_name(item)}", ""]
        for k, v in item.items():
            lines.append(f"  {k}: {v}")
        if cat:
            lines.append("")
            lines.append("Category: " + str(
                cat.get("categoryName") or cat.get("name") or "-"))
        messagebox.showinfo("Item Details", "\n".join(lines))

    def _add_to_cart(self, tree):
        sel = tree.focus()
        if not sel:
            messagebox.showinfo("Info", "Select an item first.")
            return
        values = tree.item(sel)["values"]
        item_id = int(values[0])
        name = values[1]
        item = db.search_item(item_id)
        if not item:
            return
        stock = int(item.get("stock", 0) or 0)
        if stock <= 0:
            messagebox.showwarning("Out of stock",
                                   f"{name} is out of stock.")
            return
        qty = simpledialog.askinteger(
            "Quantity", f"How many of '{name}'? (max {stock})",
            minvalue=1, maxvalue=stock, parent=self.root)
        if not qty:
            return
        self.cart[item_id] = self.cart.get(item_id, 0) + qty
        if self.cart[item_id] > stock:
            self.cart[item_id] = stock
        messagebox.showinfo("Added", f"Added {qty} x {name} to cart.")
        self._refresh_cart_tab_label()
        self._build_cart(self.cart_tab)

    '''
    Checks:

    stock availability
    user quantity input
    '''

    # ==== CART / CHECKOUT ================================================
    def _build_cart(self, parent):
        for w in parent.winfo_children():
            w.destroy()

        cols = ("id", "name", "qty")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        for c, t, w in (("id", "ID", 60), ("name", "Item", 500),
                        ("qty", "Qty", 120)):
            tree.heading(c, text=t)
            tree.column(c, width=w,
                        anchor="w" if c == "name" else "center")
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        for item_id, qty in self.cart.items():
            item = db.search_item(item_id)
            tree.insert("", END, values=(item_id, item_name(item), qty))

        footer = ttk.Frame(parent)
        footer.pack(fill="x", padx=5, pady=5)
        ttk.Label(footer,
                  text=f"Items in cart: {sum(self.cart.values())}",
                  style="Sub.TLabel").pack(side="left")

        ttk.Button(footer, text="Remove Selected", cursor="hand2", 
                   command=lambda: self._remove_from_cart(tree)).pack(
            side="right", padx=3)
        ttk.Button(footer, text="Clear Cart", cursor="hand2",
                   command=self._clear_cart).pack(side="right", padx=3)
        ttk.Button(footer, text="Checkout", cursor="hand2",
                   command=self._checkout).pack(side="right", padx=3)

    def _remove_from_cart(self, tree):
        sel = tree.focus()
        if not sel:
            return
        item_id = int(tree.item(sel)["values"][0])
        self.cart.pop(item_id, None)
        self._refresh_cart_tab_label()
        self._build_cart(self.cart_tab)

    def _clear_cart(self):
        if not self.cart:
            return
        if messagebox.askyesno("Confirm", "Empty the cart?"):
            self.cart.clear()
            self._refresh_cart_tab_label()
            self._build_cart(self.cart_tab)

    def _checkout(self):
        if not self.cart:
            messagebox.showinfo("Cart empty", "Add items before checkout.")
            return
        CheckoutDialog(self.root, self, self._after_purchase)

    def _after_purchase(self, order_id):
        self.cart.clear()
        self._refresh_cart_tab_label()
        self._build_cart(self.cart_tab)
        self._build_orders(self.orders_tab)
        messagebox.showinfo(
            "Order placed",
            f"Order #{order_id} placed successfully!\n"
            "See 'My Orders' for details.")

    # ==== MY ORDERS ======================================================
    def _build_orders(self, parent):
        for w in parent.winfo_children():
            w.destroy()

        cols = ("id", "date")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=15)
        for c, t, w in (("id", "Order #", 100),
                        ("date", "Purchase Date", 200)):
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor="center")
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        try:
            orders = db.view_orders_by_account(self.account_id)
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))
            orders = []

        if not orders:
            tree.insert("", END, values=("-", "No orders found"))
        else:
            for order in orders:
                tree.insert("", END, values=(
                    order.get("orderID", "-"),
                    str(order.get("purchaseDate", "-"))))

        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=5, pady=5)
        ttk.Button(btns, text="View Items", cursor="hand2",
                   command=lambda: self._view_order_items(tree)).pack(
            side="left", padx=3)
        ttk.Button(btns, text="Refresh", cursor="hand2",
                   command=lambda: self._build_orders(self.orders_tab)).pack(
            side="right", padx=3)

    def _view_order_items(self, tree):
        sel = tree.focus()
        if not sel:
            messagebox.showinfo("Info", "Select an order first.")
            return
        raw_order_id = tree.item(sel)["values"][0]
        if raw_order_id == "-":
            messagebox.showinfo("Info", "No order selected.")
            return
        order_id = int(raw_order_id)
        rows = db.view_orderItems(order_id)
        if not rows:
            messagebox.showinfo("Info", "No items on this order.")
            return
        msg = f"Order #{order_id} items:\n\n"
        for r in rows:
            item = db.search_item(r["itemID"])
            msg += f"  {item_name(item)} x {r.get('itemQuantity', '?')}\n"
        messagebox.showinfo("Order Items", msg)

    # ==== MY ACCOUNT =====================================================
    def _build_account(self, parent):
        for w in parent.winfo_children():
            w.destroy()

        frm = ttk.Frame(parent, padding=20)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=f"Account #{self.account_id}",
                  style="Header.TLabel").pack(pady=(0, 15))

        email_v = StringVar(value=self.account.get("email", "") or "")
        phone_v = StringVar(value=self.account.get("phoneNum", "") or "")
        addr_v = StringVar(value=self.account.get("address", "") or "")
        pw_v = StringVar()

        for label, var, show in (("Email:", email_v, None),
                                 ("Phone:", phone_v, None),
                                 ("Address:", addr_v, None),
                                 ("New Password:", pw_v, "*")):
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label, width=14,
                      anchor="e").pack(side="left")
            entry = ttk.Entry(row, textvariable=var, width=40)
            if show:
                entry.config(show=show)
            entry.pack(side="left", fill="x", expand=True)

        ttk.Label(frm, text="(Leave 'New Password' blank to keep current.)",
                  foreground="#666").pack(anchor="w", pady=(0, 5))

        def save():
            new_pw = pw_v.get()
            try:
                changed = db.update_account(
                    self.account_id,
                    phone_number=phone_v.get().strip(),
                    e_mail=email_v.get().strip(),
                    address=addr_v.get().strip(),
                    password=new_pw if new_pw else None,
                )
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))
                return
            if changed:
                self.account = db.view_account(self.account_id)
                messagebox.showinfo("Saved", "Account updated.")
            else:
                messagebox.showinfo("Info", "No changes made.")

        def delete():
            if not messagebox.askyesno(
                    "Confirm",
                    "Delete your account? This cannot be undone."):
                return
            try:
                ok = db.remove_account(self.account_id)
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))
                return
            if ok:
                messagebox.showinfo("Deleted", "Account deleted.")
                self._logout()
            else:
                messagebox.showerror("Error", "Could not delete account.")

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(15, 0))
        ttk.Button(btns, text="Save Changes", cursor="hand2",
                   command=save).pack(side="left", padx=3)
        ttk.Button(btns, text="Delete Account", cursor="hand2",
                   command=delete).pack(side="right", padx=3)

    # ==== PAYMENTS =======================================================
    def _build_payments(self, parent):
        for w in parent.winfo_children():
            w.destroy()

        cols = ("id", "card", "exp", "pin")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        for c, t, w in (("id", "Payment #", 90),
                        ("card", "Card Number", 220),
                        ("exp", "Expiration", 140),
                        ("pin", "PIN", 80)):
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor="center")
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        for pid in iter_ids("payment"):
            p = db.view_payment(pid)
            if not p or p.get("accountID") != self.account_id:
                continue
            card = str(p.get("cardNum", "") or "")
            masked = (("*" * (len(card) - 4)) + card[-4:]) if len(card) > 4 \
                else card
            tree.insert("", END, values=(pid, masked,
                                         str(p.get("expiration", "") or ""),
                                         "****"))

        def add_pay():
            PaymentDialog(self.root, self.account_id, None,
                          on_save=lambda: self._build_payments(parent))

        def edit_pay():
            sel = tree.focus()
            if not sel:
                return
            pid = int(tree.item(sel)["values"][0])
            PaymentDialog(self.root, self.account_id, pid,
                          on_save=lambda: self._build_payments(parent))

        def remove_pay():
            sel = tree.focus()
            if not sel:
                return
            pid = int(tree.item(sel)["values"][0])
            if not messagebox.askyesno("Confirm",
                                       f"Delete payment #{pid}?"):
                return
            try:
                db.remove_payment(pid)
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))
                return
            self._build_payments(parent)

        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=5, pady=5)
        ttk.Button(btns, text="Add Payment", cursor="hand2",
                   command=add_pay).pack(side="left", padx=3)
        ttk.Button(btns, text="Edit Payment", cursor="hand2",
                   command=edit_pay).pack(side="left", padx=3)
        ttk.Button(btns, text="Remove Payment", cursor="hand2",
                   command=remove_pay).pack(side="left", padx=3)
        ttk.Button(btns, text="Refresh", cursor="hand2",
                   command=lambda: self._build_payments(parent)).pack(
            side="right", padx=3)

    # ==== INVENTORY ======================================================
    def _build_inventory(self, parent):
        for w in parent.winfo_children():
            w.destroy()

        info = ttk.Label(
            parent,
            text=("Inventory view — uses update_inventory() from the backend. "
                  "If stock falls below threshold, it auto-restocks by 30. "
                  "Stock changes can be negative (remove) or positive (restock)."),
            foreground="#555", wraplength=900, justify="left")
        info.pack(anchor="w", padx=10, pady=(10, 5))

        cols = ("id", "name", "stock", "threshold")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=14)
        for c, t, w in (("id", "ID", 60), ("name", "Item", 360),
                        ("stock", "Stock", 120),
                        ("threshold", "Threshold", 120)):
            tree.heading(c, text=t)
            tree.column(c, width=w,
                        anchor="w" if c == "name" else "center")
        tree.pack(fill="both", expand=True, padx=10, pady=5)

        def refresh():
            for r in tree.get_children():
                tree.delete(r)
            for item_id in iter_ids("item"):
                item = db.search_item(item_id)
                if not item:
                    continue
                stock = item.get("stock", "-")
                threshold = item.get("threshold", "-")
                tree.insert("", END,
                            values=(item_id, item_name(item), stock, threshold))

        def change_stock():
            sel = tree.focus()
            if not sel:
                messagebox.showinfo("Info", "Select an item.")
                return
            values = tree.item(sel)["values"]
            item_id = int(values[0])
            name = values[1]
            delta = simpledialog.askinteger(
                "Update Inventory",
                f"Change stock for '{name}'\n"
                "(positive to add, negative to remove):",
                parent=self.root)
            if delta is None:
                return
            try:
                ok = db.update_inventory(item_id, delta)
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))
                return
            if not ok:
                messagebox.showerror(
                    "Error",
                    "Could not apply change. Stock would go negative or "
                    "the item was not found.")
            refresh()

        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(btns, text="Change Stock (+/-)", cursor="hand2",
                   command=change_stock).pack(side="left", padx=3)
        ttk.Button(btns, text="Refresh", cursor="hand2",
                   command=refresh).pack(side="right", padx=3)
        refresh()


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

class CheckoutDialog(Toplevel):
    """Collect payment, then call create_order()."""

    def __init__(self, parent, app: StoreApp, on_success):
        super().__init__(parent)
        self.title("Checkout")
        self.geometry("480x450")
        self.transient(parent)
        self.grab_set()
        self.app = app
        self.on_success = on_success

        frm = ttk.Frame(self, padding=20)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="Checkout",
                  style="Header.TLabel").pack(pady=(0, 10))
        ttk.Label(frm,
                  text=f"Items in order: {sum(app.cart.values())}",
                  style="Sub.TLabel").pack(pady=(0, 10))

        saved = []
        for pid in iter_ids("payment"):
            p = db.view_payment(pid)
            if p and p.get("accountID") == app.account_id:
                saved.append(p)

        self.use_saved_v = StringVar(value="new")
        ttk.Radiobutton(frm, text="Use a new card",
                        variable=self.use_saved_v,
                        value="new").pack(anchor="w")

        self.saved_combo = None
        if saved:
            ttk.Radiobutton(frm, text="Use a saved payment",
                            variable=self.use_saved_v,
                            value="saved").pack(anchor="w")
            labels = []
            self._saved = saved
            for p in saved:
                card = str(p.get("cardNum", "") or "")
                masked = (("*" * (len(card) - 4)) + card[-4:]) \
                    if len(card) > 4 else card
                labels.append(f"#{p.get('paymentID', '?')} — {masked}")
            self.saved_v = StringVar()
            self.saved_combo = ttk.Combobox(frm, textvariable=self.saved_v,
                                            values=labels, state="readonly")
            self.saved_combo.pack(fill="x", pady=3)

        self.card_v = StringVar()
        self.exp_v = StringVar()
        self.pin_v = StringVar()
        self.save_card_v = StringVar(value="0")

        card_frm = ttk.LabelFrame(frm, text="New Card", padding=8)
        card_frm.pack(fill="x", pady=(10, 0))

        for label, var, show in (("Card Number (16 digits)", self.card_v, None),
                                 ("Expiration (YYYY-MM-DD)", self.exp_v, None),
                                 ("PIN (4 digits)", self.pin_v, "*")):
            row = ttk.Frame(card_frm)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=label, width=22,
                      anchor="e").pack(side="left")
            e = ttk.Entry(row, textvariable=var)
            if show:
                e.config(show=show)
            e.pack(side="left", fill="x", expand=True)

        ttk.Checkbutton(card_frm, text="Save this card for next time",
                        variable=self.save_card_v,
                        onvalue="1", offvalue="0").pack(anchor="w",
                                                        pady=(3, 0))

        ttk.Button(frm, text="Place Order", cursor="hand2",
                   command=self._place).pack(pady=(15, 0), fill="x")
        ttk.Button(frm, text="Cancel", cursor="hand2",
                   command=self.destroy).pack(pady=(5, 0), fill="x")

    def _place(self):
        if self.use_saved_v.get() == "saved":
            if not self.saved_combo or not self.saved_v.get():
                messagebox.showerror("Error",
                                     "Select a saved payment.", parent=self)
                return
        else:
            card = re.sub(r"\s+", "", self.card_v.get())
            exp = self.exp_v.get().strip()
            pin = self.pin_v.get().strip()
            if not (card.isdigit() and len(card) == 16):
                messagebox.showerror("Payment",
                                     "Card number must be 16 digits.",
                                     parent=self)
                return
            if not valid_date(exp):
                messagebox.showerror("Payment",
                                     "Expiration must be YYYY-MM-DD.",
                                     parent=self)
                return
            if not (pin.isdigit() and len(pin) == 4):
                messagebox.showerror("Payment",
                                     "PIN must be 4 digits.", parent=self)
                return
            # Simulated gateway — cards ending in 0 decline
            if card.endswith("0"):
                messagebox.showerror(
                    "Payment Failure",
                    "Payment was declined by the gateway.\n"
                    "Please try a different card.",
                    parent=self)
                return
            if self.save_card_v.get() == "1":
                try:
                    db.add_payment(self.app.account_id, card, exp, int(pin))
                except mysql.connector.Error as e:
                    messagebox.showerror("Database Error", str(e),
                                         parent=self)
                    return

        item_ids = list(self.app.cart.keys())
        quantities = [self.app.cart[i] for i in item_ids]
        try:
            order_id = db.create_order(self.app.account_id,
                                       item_ids, quantities)
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e), parent=self)
            return

        if not order_id:
            messagebox.showerror(
                "Order Failed",
                "Could not create the order. Stock may be insufficient.",
                parent=self)
            return

        self.destroy()
        self.on_success(order_id)

'''
Handles:

payment selection
new card entry
order creation

Ensures:

16-digit card
valid date
4-digit PIN
'''

class PaymentDialog(Toplevel):
    """Add or edit a payment using add_payment / update_payment."""

    def __init__(self, parent, account_id, payment_id, on_save):
        super().__init__(parent)
        self.title("Payment")
        self.geometry("420x280")
        self.transient(parent)
        self.grab_set()
        self.account_id = account_id
        self.payment_id = payment_id
        self.on_save = on_save

        frm = ttk.Frame(self, padding=20)
        frm.pack(fill="both", expand=True)

        self.card_v = StringVar()
        self.exp_v = StringVar()
        self.pin_v = StringVar()

        if payment_id:
            p = db.view_payment(payment_id)
            if p:
                self.card_v.set(str(p.get("cardNum", "") or ""))
                self.exp_v.set(str(p.get("expiration", "") or ""))
                self.pin_v.set(str(p.get("pin", "") or ""))

        for label, var, show in (("Card Number", self.card_v, None),
                                 ("Expiration (YYYY-MM-DD)", self.exp_v, None),
                                 ("PIN (4 digits)", self.pin_v, "*")):
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label, width=22,
                      anchor="e").pack(side="left")
            e = ttk.Entry(row, textvariable=var)
            if show:
                e.config(show=show)
            e.pack(side="left", fill="x", expand=True)

        ttk.Button(frm, text="Save", cursor="hand2",
                   command=self._save).pack(fill="x", pady=(15, 0))
        ttk.Button(frm, text="Cancel", cursor="hand2",
                   command=self.destroy).pack(fill="x", pady=(5, 0))

    def _save(self):
        card = re.sub(r"\s+", "", self.card_v.get())
        exp = self.exp_v.get().strip()
        pin = self.pin_v.get().strip()
        if not (card.isdigit() and len(card) == 16):
            messagebox.showerror("Error",
                                 "Card number must be 16 digits.",
                                 parent=self)
            return
        if not valid_date(exp):
            messagebox.showerror("Error", "Expiration must be YYYY-MM-DD.",
                                 parent=self)
            return
        if not (pin.isdigit() and len(pin) == 4):
            messagebox.showerror("Error", "PIN must be 4 digits.",
                                 parent=self)
            return

        try:
            if self.payment_id:
                db.update_payment(self.payment_id,
                                  card_num=card, expiration=exp,
                                  pin=int(pin))
            else:
                db.add_payment(self.account_id, card, exp, int(pin))
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e), parent=self)
            return

        self.on_save()
        self.destroy()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main():
    check_db_connection()
    root = Tk()
    StoreApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
