import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate

class CourtHearing(Document):
    def validate(self):
        self.validate_hearing_date()
        self.validate_participants()

    def validate_hearing_date(self):
        if self.hearing_date and getdate(self.hearing_date) < getdate(nowdate()):
            frappe.throw("Hearing date cannot be in the past")

    def validate_participants(self):
        if not self.attending_attorneys:
            frappe.throw("At least one attending attorney is required")

    def on_update(self):
        # Update next hearing date in linked legal case
        if self.legal_case and self.hearing_date:
            legal_case = frappe.get_doc("Legal Case", self.legal_case)
            if not legal_case.next_hearing_date or getdate(self.hearing_date) > getdate(legal_case.next_hearing_date):
                legal_case.db_set('next_hearing_date', self.hearing_date)