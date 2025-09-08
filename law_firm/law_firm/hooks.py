# hooks.py
app_name = "law_firm"
app_title = "Law Firm"
app_publisher = "Law Tech Solutions"
app_description = "Complete legal practice management system"
app_icon = "octicon octicon-law"
app_color = "#1f4e79"
app_email = "mtawedzerwadonald17@gmail.com"
app_license = "MIT"
app_version = "1.0.0"

# # Required apps
# required_apps = ["erpnext"]

# # Include js, css files in header of desk.html
# app_include_css = [
#     "/assets/law_firm/css/law_firm.css"
# ]
# app_include_js = [
#     "/assets/law_firm/js/law_firm.js"
# ]
# # Required for DocType discovery
# include_js = {
#     "doctype": ["client.js", "legal_case.js", "time_entry.js"]
# }
# # Website context
# website_context = {
#     "favicon": "/assets/law_firm/images/favicon.png",
#     "splash_image": "/assets/law_firm/images/splash.png"
# }
# doctype_js = {
#     "Client": "public/js/client.js",
#     "Time Entry": "public/js/time_entry.js",
#     "Legal Case": "public/js/legal_case.js"
# }
# # Document Events
# doc_events = {
#     "User": {
#         "after_insert": "law_firm.api.create_user_profile"
#     },
#     "Customer": {
#         "validate": "law_firm.api.sync_client_data"
#     }
# }

# # Scheduled Tasks
# scheduler_events = {
#     "daily": [
#         "law_firm.api.send_hearing_reminders",
#         "law_firm.api.update_case_statuses"
#     ],
#     "weekly": [
#         "law_firm.api.generate_weekly_reports"
#     ],
#     "monthly": [
#         "law_firm.api.archive_old_documents"
#     ]
# }

# # Authentication and authorization
# has_permission = {
#     "Legal Case": "law_firm.law_firm.doctype.legal_case.legal_case.has_permission",
#     "Client": "law_firm.law_firm.doctype.client.client.has_permission",
#     "Legal Document": "law_firm.law_firm.doctype.legal_document.legal_document.has_permission"
# }

# # Email notifications
# standard_email_footer = """<div style='text-align: center; color: #888; font-size: 12px;'>
#     <p>This email was sent from Law Firm Management System</p></div>"""