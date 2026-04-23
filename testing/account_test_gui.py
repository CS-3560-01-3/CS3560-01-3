import tkinter as tk
from tkinter import messagebox

import mysql.connector

from database_methods import add_account, login, remove_account, update_account, view_account


class LoginFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()

        tk.Label(self, text="Login", font=("Arial", 18, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(10, 20)
        )

        tk.Label(self, text="Email:").grid(row=1, column=0, sticky="w", padx=12, pady=8)
        tk.Entry(self, textvariable=self.email_var, width=36).grid(row=1, column=1, padx=12, pady=8)

        tk.Label(self, text="Password:").grid(row=2, column=0, sticky="w", padx=12, pady=8)
        tk.Entry(self, textvariable=self.password_var, show="*", width=36).grid(row=2, column=1, padx=12, pady=8)

        tk.Button(self, text="Login", command=self.handle_login, width=16).grid(
            row=3, column=0, padx=12, pady=18, sticky="w"
        )
        tk.Button(self, text="Create Account", command=self.app.show_create_account, width=16).grid(
            row=3, column=1, padx=12, pady=18, sticky="e"
        )

    def handle_login(self):
        e_mail = self.email_var.get().strip()
        password = self.password_var.get().strip()

        if not e_mail or not password:
            messagebox.showwarning("Missing Information", "Please enter both email and password.", parent=self)
            return

        try:
            account_id = login(e_mail, password)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error", f"MySQL error: {exc}", parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Error", f"Unexpected error: {exc}", parent=self)
            return

        if not account_id:
            messagebox.showerror("Login Failed", "Invalid email or password.", parent=self)
            return

        self.app.show_account_info(account_id)


class CreateAccountFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.address_var = tk.StringVar()

        tk.Label(self, text="Create Account", font=("Arial", 18, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(10, 20)
        )

        labels = [
            ("Phone Number:", self.phone_var),
            ("Email:", self.email_var),
            ("Password:", self.password_var),
            ("Address:", self.address_var),
        ]

        for row, (label_text, variable) in enumerate(labels, start=1):
            tk.Label(self, text=label_text).grid(row=row, column=0, sticky="w", padx=12, pady=8)
            entry_kwargs = {"textvariable": variable, "width": 36}
            if label_text == "Password:":
                entry_kwargs["show"] = "*"
            tk.Entry(self, **entry_kwargs).grid(row=row, column=1, padx=12, pady=8)

        tk.Button(self, text="Create Account", command=self.handle_create, width=16).grid(
            row=5, column=0, padx=12, pady=18, sticky="w"
        )
        tk.Button(self, text="Back to Login", command=self.app.show_login, width=16).grid(
            row=5, column=1, padx=12, pady=18, sticky="e"
        )

    def handle_create(self):
        phone_number = self.phone_var.get().strip()
        e_mail = self.email_var.get().strip()
        password = self.password_var.get().strip()
        address = self.address_var.get().strip()

        if not all([phone_number, e_mail, password, address]):
            messagebox.showwarning("Missing Information", "Please fill in all fields.", parent=self)
            return

        try:
            account_id = add_account(phone_number, e_mail, password, address)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error", f"MySQL error: {exc}", parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Error", f"Unexpected error: {exc}", parent=self)
            return

        messagebox.showinfo("Success", f"Account created successfully. Your account ID is {account_id}.", parent=self)
        self.app.show_account_info(account_id)


class AccountInfoFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.account_id = None

        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.address_var = tk.StringVar()

        self.title_label = tk.Label(self, text="Account Info", font=("Arial", 18, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(10, 10))

        self.account_id_label = tk.Label(self, text="Account ID: ")
        self.account_id_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 12))

        labels = [
            ("Phone Number:", self.phone_var),
            ("Email:", self.email_var),
            ("Password:", self.password_var),
            ("Address:", self.address_var),
        ]

        for row, (label_text, variable) in enumerate(labels, start=2):
            tk.Label(self, text=label_text).grid(row=row, column=0, sticky="w", padx=12, pady=8)
            entry_kwargs = {"textvariable": variable, "width": 36}
            if label_text == "Password:":
                entry_kwargs["show"] = "*"
            tk.Entry(self, **entry_kwargs).grid(row=row, column=1, padx=12, pady=8)

        tk.Button(self, text="Save Changes", command=self.save_changes, width=16).grid(
            row=6, column=0, padx=12, pady=18, sticky="w"
        )
        tk.Button(self, text="Delete Account", command=self.delete_account, width=16).grid(
            row=6, column=1, padx=12, pady=18, sticky="e"
        )
        tk.Button(self, text="Logout", command=self.app.show_login, width=16).grid(
            row=7, column=1, padx=12, pady=(0, 16), sticky="e"
        )

    def load_account(self, account_id):
        self.account_id = account_id

        try:
            account_data = view_account(account_id)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error", f"MySQL error: {exc}", parent=self)
            self.app.show_login()
            return
        except Exception as exc:
            messagebox.showerror("Error", f"Unexpected error: {exc}", parent=self)
            self.app.show_login()
            return

        if not account_data:
            messagebox.showinfo("Not Found", f"No account found for ID {account_id}.", parent=self)
            self.app.show_login()
            return

        self.account_id_label.config(text=f"Account ID: {account_id}")
        self.phone_var.set(account_data.get("phoneNum") or "")
        self.email_var.set(account_data.get("email") or "")
        self.password_var.set(account_data.get("passw") or "")
        self.address_var.set(account_data.get("address") or "")

    def save_changes(self):
        if not self.account_id:
            messagebox.showwarning("Missing Account", "No account is loaded.", parent=self)
            return

        phone_number = self.phone_var.get().strip()
        e_mail = self.email_var.get().strip()
        password = self.password_var.get().strip()
        address = self.address_var.get().strip()

        if not all([phone_number, e_mail, password, address]):
            messagebox.showwarning("Missing Information", "Please fill in all fields.", parent=self)
            return

        try:
            updated = update_account(
                self.account_id,
                phone_number=phone_number,
                e_mail=e_mail,
                password=password,
                address=address,
            )
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error", f"MySQL error: {exc}", parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Error", f"Unexpected error: {exc}", parent=self)
            return

        if updated:
            messagebox.showinfo("Success", "Account information updated.", parent=self)
            self.load_account(self.account_id)
        else:
            messagebox.showinfo("Not Found", "No account was updated.", parent=self)

    def delete_account(self):
        if not self.account_id:
            messagebox.showwarning("Missing Account", "No account is loaded.", parent=self)
            return

        confirm = messagebox.askyesno(
            "Delete Account",
            "Are you sure you want to delete this account? This cannot be undone.",
            parent=self,
        )
        if not confirm:
            return

        try:
            deleted = remove_account(self.account_id)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error", f"MySQL error: {exc}", parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Error", f"Unexpected error: {exc}", parent=self)
            return

        if deleted:
            messagebox.showinfo("Deleted", "Account deleted successfully.", parent=self)
            self.app.show_login()
        else:
            messagebox.showinfo("Not Found", "No account was deleted.", parent=self)


class AccountApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Account Login")
        self.geometry("520x420")
        self.resizable(False, False)

        self.login_frame = LoginFrame(self, self)
        self.create_frame = CreateAccountFrame(self, self)
        self.account_frame = AccountInfoFrame(self, self)

        for frame in (self.login_frame, self.create_frame, self.account_frame):
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_login()

    def _show_frame(self, frame):
        frame.tkraise()

    def show_login(self):
        self.title("Account Login")
        self.login_frame.email_var.set("")
        self.login_frame.password_var.set("")
        self._show_frame(self.login_frame)

    def show_create_account(self):
        self.title("Create Account")
        self.create_frame.phone_var.set("")
        self.create_frame.email_var.set("")
        self.create_frame.password_var.set("")
        self.create_frame.address_var.set("")
        self._show_frame(self.create_frame)

    def show_account_info(self, account_id):
        self.title("Account Info")
        self._show_frame(self.account_frame)
        self.account_frame.load_account(account_id)


if __name__ == "__main__":
    app = AccountApp()
    app.mainloop()