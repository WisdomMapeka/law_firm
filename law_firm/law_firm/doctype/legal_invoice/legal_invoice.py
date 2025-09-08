import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate, flt

class LegalInvoice(Document):
    def before_validate(self):
        """Calculate values before validation runs"""
        self.calculate_totals()

    def validate(self):
        """Perform validation checks"""
        self.validate_dates()
        self.validate_amounts()
        self.validate_status()

    def validate_dates(self):
        if self.due_date and self.invoice_date:
            if getdate(self.due_date) < getdate(self.invoice_date):
                frappe.throw("Due date cannot be before invoice date")

    def validate_amounts(self):
        if flt(self.balance_due) < 0:
            frappe.throw("Balance due cannot be negative")
        
        # Validate items
        for item in self.items:
            if flt(item.quantity) <= 0:
                frappe.throw(f"Quantity must be greater than 0 for item {item.item_code or item.description}")
            if flt(item.rate) < 0:
                frappe.throw(f"Rate cannot be negative for item {item.item_code or item.description}")

    def validate_status(self):
        """Ensure status is consistent with amounts and dates"""
        if self.docstatus == 2:  # Cancelled
            return
            
        if flt(self.balance_due) <= 0 and flt(self.grand_total) > 0:
            self.status = "Paid"
        elif flt(self.balance_due) > 0 and self.due_date and getdate(self.due_date) < getdate(nowdate()):
            self.status = "Overdue"
        elif flt(self.balance_due) > 0:
            self.status = "Unpaid"
        else:
            self.status = "Draft"

    def calculate_totals(self):
        """Calculate all financial totals"""
        # Calculate item amounts and subtotal
        subtotal = 0
        for item in self.items:
            item.amount = flt(item.quantity) * flt(item.rate)
            subtotal += flt(item.amount)

        self.subtotal = subtotal
        self.tax_amount = flt(self.subtotal) * flt(self.tax_rate or 0) / 100
        self.grand_total = flt(self.subtotal) + flt(self.tax_amount) - flt(self.discount_amount or 0)
        self.balance_due = flt(self.grand_total) - flt(self.amount_paid or 0)

    def on_submit(self):
        """Actions when invoice is submitted"""
        if not self.invoice_date:
            self.invoice_date = nowdate()
        self.db_set('status', 'Unpaid')  # Use db_set to avoid recursion
        frappe.msgprint(f"Invoice {self.name} has been submitted successfully.", indicator="green")

    def on_cancel(self):
        """Actions when invoice is cancelled"""
        self.db_set('status', 'Cancelled')  # Use db_set to avoid recursion
        frappe.msgprint(f"Invoice {self.name} has been cancelled.", indicator="red")