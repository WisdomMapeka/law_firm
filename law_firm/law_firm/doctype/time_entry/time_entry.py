# file: law_firm/law_firm/doctype/time_entry/time_entry.py

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, get_datetime, get_timespan_from_time_string

class TimeEntry(Document):
    def before_insert(self):
        """
        Sets default values before a new Time Entry is saved to the database.
        Automatically sets the 'Activity Date' to today and 'Billing Status' to 'Draft'.
        Also sets the 'Employee' if not already provided, typically to the current user.
        """
        if not self.activity_date:
            self.activity_date = nowdate()
        if not self.billing_status:
            self.billing_status = "Draft"
        if not self.employee:
            self.employee = frappe.session.user

    def before_validate(self):
        """
        Calculate values before validation runs.
        This prevents infinite loops that can occur if calculations are done in validate().
        """
        self.calculate_hours()
        self.calculate_billable_amount()
        self.set_client_from_case()

    def validate(self):
        """
        Performs validation checks before saving the Time Entry.
        Contains only checks, not calculations that modify fields.
        """
        self.validate_time_and_activity()
        self.validate_billing_details()

    def calculate_hours(self):
        """
        Calculates the total hours worked based on 'From Time' and 'To Time'.
        Ensures 'To Time' is after 'From Time'.
        """
        if self.from_time and self.to_time:
            try:
                # Convert time strings to datetime objects for calculation
                from_dt = get_datetime(f"{self.activity_date} {self.from_time}")
                to_dt = get_datetime(f"{self.activity_date} {self.to_time}")

                # If to_time is earlier than from_time, assume it's the next day
                if to_dt < from_dt:
                    to_dt = frappe.utils.add_days(to_dt, 1)

                time_difference_seconds = (to_dt - from_dt).total_seconds()
                self.hours = round(time_difference_seconds / 3600, 2) # Convert seconds to hours
            except Exception as e:
                # Log technical error for developers and show user-friendly message
                frappe.log_error(f"TimeEntry calculate_hours error: {e}", "Time Entry Calculation Error")
                frappe.throw("Please check your 'From Time' and 'To Time'. They must be in a valid format (e.g., '14:00:00').")
        else:
            self.hours = 0.0

    def calculate_billable_amount(self):
        """
        Calculates the billable amount if the entry is marked as billable.
        """
        self.billable_amount = 0.0 # Initialize to 0
        
        if self.billable:
            if not self.billable_hours or self.billable_hours == 0:
                # If billable_hours is not explicitly set, use total hours
                self.billable_hours = self.hours

            if not self.billing_rate:
                frappe.throw("A <b>Billing Rate</b> is required for billable entries.")
                
            if not self.billable_hours or self.billable_hours <= 0:
                frappe.throw("Billable Hours must be a positive number for billable entries.")

            self.billable_amount = self.billing_rate * self.billable_hours
        else:
            # If not billable, ensure billable fields are zero
            self.billable_hours = 0.0
            self.billing_rate = 0.0
            self.billable_amount = 0.0

    def validate_time_and_activity(self):
        """
        Validates time range and ensures activity details are present.
        """
        if self.from_time and self.to_time:
            # Check if from_time is logically before to_time
            from_span = get_timespan_from_time_string(self.from_time)
            to_span = get_timespan_from_time_string(self.to_time)
            
            # For same-day entries, ensure to_time is after from_time
            if self.hours <= 0 and (from_span >= to_span):
                frappe.throw("To Time must be after From Time.")

        if not self.activity_type:
            frappe.throw("Activity Type is required for time entry.")
            
        if not self.description:
            frappe.throw("Description of activity is required.")

    def validate_billing_details(self):
        """
        Validates billing-specific fields based on the 'Billable' checkbox.
        """
        if self.billable:
            if not self.billing_rate or self.billing_rate <= 0:
                frappe.throw("Billing Rate must be a positive number for billable entries.")
                
            if not self.billable_hours or self.billable_hours <= 0:
                frappe.throw("Billable Hours must be a positive number for billable entries.")
                
            if not self.billable_amount or self.billable_amount < 0:
                frappe.throw("Billable Amount must be calculated correctly for billable entries.")

    def set_client_from_case(self):
        """
        Fetches the Client from the linked Legal Case and sets it on the Time Entry.
        This ensures data consistency.
        """
        if self.legal_case and not self.client:
            client_name = frappe.db.get_value("Legal Case", self.legal_case, "client")
            if client_name:
                self.client = client_name
            else:
                frappe.msgprint(f"Client not found for Legal Case: {self.legal_case}", alert=True)
        elif not self.legal_case:
            self.client = None # Clear client if no case is linked

    def on_submit(self):
        """
        Actions to perform when the Time Entry is submitted.
        Sets the 'Billing Status' to 'Approved'.
        """
        self.db_set('billing_status', 'Approved')
        frappe.msgprint(f"Time Entry {self.name} has been approved.", alert=True)

    def on_cancel(self):
        """
        Actions to perform when the Time Entry is cancelled.
        Changes status to 'Cancelled' for better audit trail.
        """
        self.db_set('billing_status', 'Cancelled')
        frappe.msgprint(f"Time Entry {self.name} has been cancelled.", alert=True)