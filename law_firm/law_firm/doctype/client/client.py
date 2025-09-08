import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate, validate_email_address
from frappe import _

class Client(Document):
    def before_insert(self):
        """
        Set default values for new clients
        """
        if not self.client_since:
            self.client_since = nowdate()
        if not self.status:
            self.status = "Active"
        if not self.billing_currency:
            self.billing_currency = "USD"
            
    def validate(self):
        """
        Validate client data
        """
        self.validate_contact_info()
        self.validate_demographics()
        self.validate_billing_info()
        self.update_client_id()
        self.set_full_address()
        
    def validate_contact_info(self):
        """
        Validate contact information
        """
        if self.email and not validate_email_address(self.email):
            frappe.throw(_("Please enter a valid email address"))
            
        # Validate phone numbers
        if self.mobile and not self.validate_phone_number(self.mobile):
            frappe.throw(_("Please enter a valid mobile number"))
            
        if self.phone and not self.validate_phone_number(self.phone):
            frappe.throw(_("Please enter a valid phone number"))
            
    def validate_demographics(self):
        """
        Validate demographic information
        """
        if self.date_of_birth and getdate(self.date_of_birth) > getdate(nowdate()):
            frappe.throw(_("Date of Birth cannot be in the future"))
            
        # Validate SSN format if provided (basic validation)
        if self.ssn and not self.validate_ssn_format(self.ssn):
            frappe.throw(_("Please enter a valid SSN format (XXX-XX-XXXX)"))
            
    def validate_billing_info(self):
        """
        Validate billing information
        """
        if self.credit_limit and float(self.credit_limit or 0) < 0:
            frappe.throw(_("Credit Limit cannot be negative"))
            
        if self.tax_rate and (float(self.tax_rate or 0) < 0 or float(self.tax_rate or 0) > 100):
            frappe.throw(_("Tax Rate must be between 0 and 100"))
            
        if self.discount_percentage and (float(self.discount_percentage or 0) < 0 or float(self.discount_percentage or 0) > 100):
            frappe.throw(_("Discount Percentage must be between 0 and 100"))
    
    def validate_phone_number(self, phone_number):
        """
        Basic phone number validation
        """
        # Remove non-digit characters
        digits = ''.join(filter(str.isdigit, phone_number))
        return len(digits) >= 10  # Basic validation for at least 10 digits
    
    def validate_ssn_format(self, ssn):
        """
        Basic SSN format validation
        """
        # Simple format check (XXX-XX-XXXX)
        import re
        pattern = r'^\d{3}-\d{2}-\d{4}$'
        return bool(re.match(pattern, ssn))
    
    def update_client_id(self):
        """
        Generate or update client ID if not set
        """
        if not self.client_id:
            # Generate client ID based on client type and name
            client_type_prefix = self.client_type[:3].upper() if self.client_type else "CLI"
            name_part = self.client_name[:3].upper().replace(" ", "") if self.client_name else "000"
            self.client_id = f"{client_type_prefix}-{name_part}-{frappe.generate_hash(length=4)}"
    
    def set_full_address(self):
        """
        Create a full address string for display purposes
        """
        address_parts = []
        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.zip_code:
            address_parts.append(self.zip_code)
        if self.country and self.country != "United States":
            address_parts.append(self.country)
        
        self.full_address = ", ".join(address_parts) if address_parts else None
    
    def on_update(self):
        """
        Update last contact date and log changes
        """
        self.db_set('last_contact', nowdate())
        
        # Log the update event
        frappe.log_event(
            "Client Updated",
            f"Client {self.client_name} was updated",
            doctype="Client",
            name=self.name
        )
    
    def after_insert(self):
        """
        Actions after client is created
        """
        self.create_client_folder()
        self.send_welcome_email()
    
    def create_client_folder(self):
        """
        Create a folder for client documents
        """
        try:
            folder_name = f"Client {self.client_name} - {self.name}"
            folder = frappe.get_doc({
                "doctype": "File",
                "file_name": folder_name,
                "is_folder": 1,
                "folder": "Home"
            })
            folder.insert(ignore_permissions=True)
            self.db_set('client_folder', folder.name)
        except Exception as e:
            frappe.log_error(f"Error creating client folder: {e}")
    
    def send_welcome_email(self):
        """
        Send welcome email to new client
        """
        if self.email and self.status == "Active":
            try:
                subject = f"Welcome to Our Law Firm - {self.client_name}"
                message = f"""
                Dear {self.client_name},
                
                Thank you for choosing our law firm. We're excited to work with you!
                
                Your client ID: {self.client_id}
                Primary Contact: {self.primary_contact or 'N/A'}
                
                Please don't hesitate to contact us with any questions.
                
                Best regards,
                The Legal Team
                """
                
                frappe.sendmail(
                    recipients=self.email,
                    subject=subject,
                    message=message
                )
            except Exception as e:
                frappe.log_error(f"Error sending welcome email: {e}")
    
    def on_trash(self):
        """
        Cleanup when client is deleted
        """
        self.archive_client_data()
    
    def archive_client_data(self):
        """
        Archive client data before deletion
        """
        frappe.log_event(
            "Client Archived",
            f"Client {self.client_name} was deleted and archived",
            doctype="Client",
            name=self.name
        )
    
    @frappe.whitelist()
    def update_contact_info(self, contact_data):
        """
        Method to update client contact information via API
        """
        try:
            if isinstance(contact_data, str):
                contact_data = frappe.parse_json(contact_data)
            
            for field, value in contact_data.items():
                if hasattr(self, field):
                    self.db_set(field, value)
            
            self.db_set('last_contact', nowdate())
            frappe.msgprint(_("Contact information updated successfully"))
            
        except Exception as e:
            frappe.log_error(f"Error updating contact info: {e}")
            frappe.throw(_("Error updating contact information"))