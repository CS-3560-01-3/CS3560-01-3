import tkinter as tk
from tkinter import messagebox

import mysql.connector

from database_methods import add_account


class AccountTestApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Account Insert Test")
        self.geometry("460x340")
        self.resizable(False, False)

        self.fields = {
            "Phone Number": tk.StringVar(),
            "Email": tk.StringVar(),
            "Address": tk.StringVar(),
        }

        self._build_form()


    def _build_form(self):
        row = 0
        for label_text, var in self.fields.items():
            label = tk.Label(self, text=label_text + ":", anchor="w")
            label.grid(row=row, column=0, sticky="w", padx=12, pady=8)

            entry = tk.Entry(self, textvariable=var, width=40)
            entry.grid(row=row, column=1, padx=12, pady=8)
            row += 1

        submit_btn = tk.Button(self, text="Create Account", command=self.create_account, width=18)
        submit_btn.grid(row=row, column=0, padx=12, pady=16, sticky="w")

        clear_btn = tk.Button(self, text="Clear", command=self.clear_form, width=18)
        clear_btn.grid(row=row, column=1, padx=12, pady=16, sticky="e")

    def create_account(self):
        phone_number = self.fields["Phone Number"].get().strip()
        e_mail = self.fields["Email"].get().strip()
        address = self.fields["Address"].get().strip()

        if not all([phone_number, e_mail, address]):
            messagebox.showwarning("Missing Information", "Please fill in all fields.")
            return

        try:
            account_id = add_account(phone_number, e_mail, address)
            messagebox.showinfo("Success", f"Account created successfully. New account ID: {account_id}")
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error", f"MySQL error: {exc}")
        except Exception as exc:
            messagebox.showerror("Error", f"Unexpected error: {exc}")

    def clear_form(self):
        for var in self.fields.values():
            var.set("")


if __name__ == "__main__":
    app = AccountTestApp()
    app.mainloop()
