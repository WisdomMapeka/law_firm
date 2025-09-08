# file: law_firm/law_firm/doctype/legalcase/legalcase.py
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate
from frappe.model.mapper import get_mapped_doc
from frappe import _
import json


class LegalCase(Document):
    def before_insert(self):
        """
        Sets default values for a new Legal Case before it is saved.
        """
        if not self.date_opened:
            self.date_opened = nowdate()
        if not self.status:
            self.status = "Open"
        if not self.priority:
            self.priority = "Medium"

    def validate(self):
        """
        Validates the Legal Case document before saving.
        Enforces business rules such as date consistency and billing method requirements.
        """
        self.validate_dates()
        self.validate_billing_method()
        self.validate_case_status()  # Added new validation method

    def validate_dates(self):
        """
        Validates the consistency of date fields.
        """
        if self.date_opened and self.date_closed:
            if getdate(self.date_closed) < getdate(self.date_opened):
                frappe.throw("Date Closed cannot be before Date Opened.")

        if self.date_opened and self.expected_close_date:
            if getdate(self.expected_close_date) < getdate(self.date_opened):
                frappe.throw("Expected Close Date cannot be before Date Opened.")

        if self.status not in ["Closed", "Settled", "Dismissed"] and self.statute_of_limitations:
            if getdate(self.statute_of_limitations) < getdate(nowdate()):
                frappe.throw("Statute of Limitations cannot be in the past for an active case.")

    def validate_billing_method(self):
        """
        Ensures that required fields for the chosen billing method are filled.
        """
        if self.billing_method == "Hourly":
            if not self.hourly_rate:
                frappe.throw("Hourly Rate is required for the Hourly billing method.")
        elif self.billing_method == "Flat Fee":
            if not self.flat_fee_amount:
                frappe.throw("Flat Fee Amount is required for the Flat Fee billing method.")
        elif self.billing_method == "Contingency":
            if not self.contingency_percentage:
                frappe.throw("Contingency Percentage is required for the Contingency billing method.")
        elif self.billing_method == "Retainer":
            if not self.retainer_amount:
                frappe.throw("Retainer Amount is required for the Retainer billing method.")
        elif self.billing_method == "Mixed":
            if not any([self.hourly_rate, self.flat_fee_amount, self.contingency_percentage, self.retainer_amount]):
                frappe.throw("For Mixed billing method, at least one billing field must be filled.")

    # Add to your LegalCase controller
    def calculate_team_costs(self):
        """
        Calculate total team costs based on hourly rates and allocated hours
        """
        total_team_cost = 0
        for member in self.assigned_attorneys:
            # Calculate individual member cost
            member.total_cost = flt(member.hourly_rate or 0) * flt(member.hours_allocated or 0)
            total_team_cost += flt(member.total_cost or 0)
        
        self.total_team_cost = total_team_cost

    def validate_team_members(self):
        """
        Validate team member assignments
        """
        lead_attorneys = [m for m in self.assigned_attorneys if m.is_lead]
        
        if len(lead_attorneys) > 1:
            frappe.throw("Only one team member can be designated as Lead Attorney")
        
        if not lead_attorneys and self.assigned_attorneys:
            frappe.throw("Please designate one team member as Lead Attorney")
    
    def validate_case_status(self):
        """
        Validates status transitions and sets date_closed when appropriate.
        """
        # Auto-set date_closed when case is closed, settled, or dismissed
        if self.status in ["Closed", "Settled", "Dismissed"] and not self.date_closed:
            self.date_closed = nowdate()
        
        # Clear date_closed if case is reopened
        if self.status not in ["Closed", "Settled", "Dismissed"] and self.date_closed:
            self.date_closed = None

    def on_submit(self):
        """
        Actions to perform when a Legal Case is submitted.
        """
        frappe.msgprint(f"Legal Case {self.name} has been submitted successfully.", indicator="green")
        frappe.log_event(
            "Case Submitted",
            f"Legal Case {self.name} has been submitted.",
            doctype="Legal Case",
            name=self.name
        )

    def on_cancel(self):
        """
        Actions to perform when a Legal Case is canceled.
        """
        if self.status != "Closed":
            self.db_set('status', 'Cancelled')
            self.db_set('date_closed', nowdate())
            frappe.msgprint(f"Legal Case {self.name} has been cancelled.", indicator="red")
            frappe.log_event(
                "Case Cancelled",
                f"Legal Case {self.name} has been cancelled.",
                doctype="Legal Case",
                name=self.name
            )