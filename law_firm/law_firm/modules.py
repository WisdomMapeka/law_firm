from frappe import _

def get_data():
    return [
        {
            "label": _("Case Management"),
            "icon": "fa fa-legal",
            "items": [
                {
                    "type": "doctype",
                    "name": "LegalCase",
                    "description": _("Manage all legal cases.")
                },
                {
                    "type": "doctype",
                    "name": "Client",
                    "description": _("Client database and information.")
                },
                {
                    "type": "doctype",
                    "name": "CourtHearing",
                    "description": _("Schedule and track court appearances.")
                }
            ]
        },
        {
            "label": _("Time & Billing"),
            "icon": "fa fa-clock-o",
            "items": [
                {
                    "type": "doctype",
                    "name": "TimeEntry",
                    "description": _("Track time spent on legal cases.")
                },
                {
                    "type": "doctype",
                    "name": "LegalInvoice",
                    "description": _("Generate invoices for clients.")
                }
            ]
        },
        {
            "label": _("Documents"),
            "icon": "fa fa-file-text",
            "items": [
                {
                    "type": "doctype",
                    "name": "LegalDocument",
                    "description": _("Manage legal documents and filings.")
                }
            ]
        },
        {
            "label": _("References"),
            "icon": "fa fa-list",
            "items": [
                {
                    "type": "doctype",
                    "name": "CaseTeamMember",
                    "description": _("Legal team assignments and roles.")
                },
                {
                    "type": "doctype",
                    "name": "HearingWitness",
                    "description": _("Witness information for court hearings.")
                },
                {
                    "type": "doctype",
                    "name": "InvoiceItem",
                    "description": _("Invoice line items and billing details.")
                },
                {
                    "type": "doctype",
                    "name": "LegalDocumentReference",
                    "description": _("Document references and relationships.")
                }
            ]
        },
        {
            "label": _("Settings"),
            "icon": "fa fa-cog",
            "items": [
                {
                    "type": "doctype",
                    "name": "Legal Settings",
                    "description": _("Configure law firm settings and preferences.")
                },
                {
                    "type": "doctype", 
                    "name": "Billing Rate",
                    "description": _("Manage attorney billing rates and fee structures.")
                },
                {
                    "type": "doctype",
                    "name": "Practice Area",
                    "description": _("Manage legal practice areas and specialties.")
                }
            ]
        }
    ]