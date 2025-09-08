import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

class LegalDocument(Document):
    def before_insert(self):
        """
        Set default values before inserting a new document
        """
        if not self.creation_date:
            self.creation_date = nowdate()
        if not self.last_modified:
            self.last_modified = nowdate()
        if not self.author:
            self.author = frappe.session.user
        if not self.status:
            self.status = "Draft"
        if not self.version:
            self.version = "1.0"

    def before_save(self):
        """
        Update last modified timestamp before saving
        """
        self.last_modified = nowdate()
        self.validate_document_rules()

    def validate(self):
        """
        Main validation method
        """
        self.validate_required_fields()
        self.validate_document_rules()

    def validate_required_fields(self):
        """
        Validate required fields
        """
        if not self.document_name:
            frappe.throw("Document Name is required")
            
        if not self.document_type:
            frappe.throw("Document Type is required")

    def validate_document_rules(self):
        """
        Validate specific rules based on document type
        """
        if self.document_type == "Contract" and not self.legal_case:
            frappe.throw("Contracts must be linked to a Legal Case")
        
        if self.document_type == "Pleading" and not self.legal_case:
            frappe.throw("Pleadings must be linked to a Legal Case")
        
        if self.document_type in ["Motion", "Brief", "Affidavit"] and not self.legal_case:
            frappe.throw(f"{self.document_type}s must be linked to a Legal Case")