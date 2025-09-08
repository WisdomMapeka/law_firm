# api.py
import frappe
from frappe import _
from frappe.utils import now, today, add_days, get_datetime
import json

@frappe.whitelist()
def get_law_firm_dashboard():
    """Get comprehensive dashboard data for law firm"""
    return {
        "summary_cards": get_summary_cards(),
        "case_statistics": get_case_statistics(),
        "billing_overview": get_billing_overview(),
        "recent_activities": get_recent_activities(),
        "upcoming_deadlines": get_upcoming_deadlines(),
        "team_productivity": get_team_productivity()
    }

def get_summary_cards():
    """Get summary statistics for dashboard cards"""
    return {
        "total_clients": frappe.db.count("Client", {"status": "Active"}),
        "active_cases": frappe.db.count("Legal Case", {"status": ["in", ["Open", "In Progress"]]}),
        "pending_invoices": frappe.db.count("Legal Invoice", {"status": "Unpaid"}),
        "total_revenue_this_month": get_monthly_revenue(),
        "billable_hours_this_month": get_monthly_billable_hours(),
        "team_utilization": get_team_utilization()
    }

def get_case_statistics():
    """Get case statistics by practice area and status"""
    # Cases by practice area
    practice_area_stats = frappe.db.sql("""
        SELECT practice_area, COUNT(*) as count
        FROM `tabLegal Case`
        WHERE status != 'Closed'
        GROUP BY practice_area
        ORDER BY count DESC
    """, as_dict=True)
    
    # Cases by status
    status_stats = frappe.db.sql("""
        SELECT status, COUNT(*) as count
        FROM `tabLegal Case`
        GROUP BY status
        ORDER BY count DESC
    """, as_dict=True)
    
    return {
        "by_practice_area": practice_area_stats,
        "by_status": status_stats
    }

def get_billing_overview():
    """Get billing overview for the firm"""
    # Monthly billing trends
    monthly_billing = frappe.db.sql("""
        SELECT 
            MONTH(posting_date) as month,
            YEAR(posting_date) as year,
            SUM(total_amount) as total_billed,
            SUM(outstanding_amount) as outstanding
        FROM `tabLegal Invoice`
        WHERE posting_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY YEAR(posting_date), MONTH(posting_date)
        ORDER BY year, month
    """, as_dict=True)
    
    # Top billing clients
    top_clients = frappe.db.sql("""
        SELECT 
            client,
            SUM(total_amount) as total_billed
        FROM `tabLegal Invoice`
        WHERE posting_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY client
        ORDER BY total_billed DESC
        LIMIT 10
    """, as_dict=True)
    
    return {
        "monthly_trends": monthly_billing,
        "top_clients": top_clients,
        "total_outstanding": sum([b.outstanding for b in monthly_billing if b.get('outstanding', 0)])
    }

def get_monthly_revenue():
    """Calculate total revenue for current month"""
    result = frappe.db.sql("""
        SELECT SUM(total_amount) as revenue
        FROM `tabLegal Invoice`
        WHERE MONTH(posting_date) = MONTH(CURDATE())
        AND YEAR(posting_date) = YEAR(CURDATE())
        AND docstatus = 1
    """)[0][0]
    
    return result or 0

def get_monthly_billable_hours():
    """Calculate billable hours for current month"""
    result = frappe.db.sql("""
        SELECT SUM(billable_hours) as hours
        FROM `tabTime Entry`
        WHERE MONTH(activity_date) = MONTH(CURDATE())
        AND YEAR(activity_date) = YEAR(CURDATE())
        AND billable = 1
        AND docstatus = 1
    """)[0][0]
    
    return result or 0

def get_team_utilization():
    """Calculate team utilization percentage"""
    # This is a simplified calculation
    # In reality, you'd want more sophisticated utilization tracking
    total_hours = frappe.db.sql("""
        SELECT SUM(hours) as total
        FROM `tabTime Entry`
        WHERE MONTH(activity_date) = MONTH(CURDATE())
        AND YEAR(activity_date) = YEAR(CURDATE())
        AND docstatus = 1
    """)[0][0] or 0
    
    # Assuming 8 hours/day * 22 working days * number of attorneys
    attorney_count = frappe.db.count("User", {"role_profile_name": "Attorney"})
    expected_hours = attorney_count * 8 * 22
    
    return (total_hours / expected_hours * 100) if expected_hours > 0 else 0

def get_recent_activities():
    """Get recent activities across the firm"""
    activities = []
    
    # Recent case updates
    recent_cases = frappe.get_all("Legal Case",
        filters={"modified": [">=", add_days(today(), -7)]},
        fields=["name", "case_title", "status", "modified", "modified_by"],
        order_by="modified desc",
        limit=10
    )
    
    for case in recent_cases:
        activities.append({
            "type": "Case Updated",
            "title": case.case_title,
            "subtitle": f"Status: {case.status}",
            "user": case.modified_by,
            "timestamp": case.modified,
            "link": f"/app/legal-case/{case.name}"
        })
    
    # Recent time entries
    recent_time = frappe.get_all("Time Entry",
        filters={"activity_date": [">=", add_days(today(), -7)]},
        fields=["legal_case", "activity_type", "hours", "employee", "activity_date"],
        order_by="activity_date desc",
        limit=10
    )
    
    for entry in recent_time:
        activities.append({
            "type": "Time Logged",
            "title": f"{entry.activity_type} - {entry.hours} hours",
            "subtitle": f"Case: {entry.legal_case}",
            "user": entry.employee,
            "timestamp": entry.activity_date,
            "link": "#"
        })
    
    # Sort by timestamp and return latest 20
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:20]

def get_upcoming_deadlines():
    """Get upcoming deadlines and important dates"""
    deadlines = []
    
    # Statute of limitations approaching
    sol_cases = frappe.get_all("Legal Case",
        filters={
            "statute_of_limitations": ["between", [today(), add_days(today(), 60)]],
            "status": ["!=", "Closed"]
        },
        fields=["name", "case_title", "statute_of_limitations", "client"],
        order_by="statute_of_limitations asc"
    )
    
    for case in sol_cases:
        deadlines.append({
            "type": "Statute of Limitations",
            "title": case.case_title,
            "date": case.statute_of_limitations,
            "client": case.client,
            "priority": "High",
            "link": f"/app/legal-case/{case.name}"
        })
    
    # Upcoming hearings
    hearings = frappe.get_all("Court Hearing",
        filters={
            "hearing_date": ["between", [now(), add_days(now(), 30)]],
            "status": ["!=", "Completed"]
        },
        fields=["name", "hearing_type", "hearing_date", "legal_case"],
        order_by="hearing_date asc"
    )
    
    for hearing in hearings:
        deadlines.append({
            "type": "Court Hearing",
            "title": f"{hearing.hearing_type}",
            "date": hearing.hearing_date,
            "case": hearing.legal_case,
            "priority": "Medium",
            "link": f"/app/court-hearing/{hearing.name}"
        })
    
    return sorted(deadlines, key=lambda x: x["date"])[:15]

def get_team_productivity():
    """Get team productivity metrics"""
    team_stats = frappe.db.sql("""
        SELECT 
            employee,
            COUNT(*) as total_entries,
            SUM(hours) as total_hours,
            SUM(billable_hours) as billable_hours,
            SUM(billable_amount) as revenue_generated
        FROM `tabTime Entry`
        WHERE activity_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        AND docstatus = 1
        GROUP BY employee
        ORDER BY revenue_generated DESC
    """, as_dict=True)
    
    return team_stats

@frappe.whitelist()
def create_case_from_lead(lead_name, case_title, practice_area):
    """Create a legal case from a lead"""
    lead = frappe.get_doc("Lead", lead_name)
    
    # First create client if doesn't exist
    client_name = create_client_from_lead(lead)
    
    # Create the legal case
    case = frappe.new_doc("Legal Case")
    case.case_title = case_title
    case.client = client_name
    case.practice_area = practice_area
    case.status = "Open"
    case.date_opened = today()
    case.case_description = f"Case created from lead: {lead.lead_name}"
    
    case.insert()
    frappe.db.commit()
    
    return case.name

def create_client_from_lead(lead):
    """Create client from lead data"""
    if frappe.db.exists("Client", {"email": lead.email_id}):
        return frappe.db.get_value("Client", {"email": lead.email_id}, "name")
    
    client = frappe.new_doc("Client")
    client.client_name = lead.lead_name
    client.client_type = "Individual" # Assuming lead is an individual unless specified
    client.email = lead.email_id
    client.phone = lead.phone
    client.mobile = lead.mobile_no
    client.status = "Prospective"
    
    # ERPNext stores addresses in a separate DocType, Address.
    # This is a simplified approach, you might want to create a full Address document.
    # Here, we'll just populate the client's fields directly.
    client.address_line_1 = lead.address_line1
    client.address_line_2 = lead.address_line2
    client.city = lead.city
    client.state = lead.state
    client.country = lead.country
    
    client.insert()
    frappe.db.commit()
    
    return client.name

@frappe.whitelist()
def bulk_time_entry(entries_json):
    """Create multiple time entries at once"""
    entries = json.loads(entries_json) if isinstance(entries_json, str) else entries_json
    created_entries = []
    
    for entry_data in entries:
        time_entry = frappe.new_doc("Time Entry")
        time_entry.update(entry_data)
        time_entry.insert()
        created_entries.append(time_entry.name)
    
    frappe.db.commit()
    return created_entries

@frappe.whitelist()
def generate_case_report(case_name, report_type="summary"):
    """Generate various types of case reports"""
    case = frappe.get_doc("Legal Case", case_name)
    
    if report_type == "summary":
        return generate_case_summary_report(case)
    elif report_type == "billing":
        return generate_case_billing_report(case)
    elif report_type == "timeline":
        return generate_case_timeline_report(case)
    
    return {}

def generate_case_summary_report(case):
    """Generate case summary report"""
    # Get time entries
    time_entries = frappe.get_all("Time Entry",
        filters={"legal_case": case.name, "docstatus": 1},
        fields=["activity_type", "hours", "billable_hours", "billable_amount", "activity_date"]
    )
    
    # Get documents
    documents = frappe.get_all("Legal Document",
        filters={"legal_case": case.name},
        fields=["document_name", "document_type", "creation", "file_url"]
    )
    
    # Get hearings
    hearings = frappe.get_all("Court Hearing",
        filters={"legal_case": case.name},
        fields=["hearing_type", "hearing_date", "status", "outcome"]
    )
    
    return {
        "case_info": case.as_dict(),
        "time_summary": {
            "total_hours": sum([te.hours or 0 for te in time_entries]),
            "billable_hours": sum([te.billable_hours or 0 for te in time_entries]),
            "total_billed": sum([te.billable_amount or 0 for te in time_entries]),
            "entries_by_type": group_by_activity_type(time_entries)
        },
        "documents": documents,
        "hearings": hearings
    }

def group_by_activity_type(time_entries):
    """Group time entries by activity type"""
    grouped = {}
    for entry in time_entries:
        activity_type = entry.activity_type
        if activity_type not in grouped:
            grouped[activity_type] = {"hours": 0, "billable_amount": 0, "count": 0}
        
        grouped[activity_type]["hours"] += entry.hours or 0
        grouped[activity_type]["billable_amount"] += entry.billable_amount or 0
        grouped[activity_type]["count"] += 1
    
    return grouped

def generate_case_billing_report(case):
    """Generate case billing report"""
    # Get all time entries for the case
    time_entries = frappe.get_all("Time Entry",
        filters={"legal_case": case.name, "docstatus": 1},
        fields=["employee", "activity_type", "activity_date", "hours", "billable_hours", "billable_amount"]
    )
    
    # Get all invoices linked to the case
    invoices = frappe.get_all("Legal Invoice",
        filters={"legal_case": case.name, "docstatus": 1},
        fields=["name", "posting_date", "total_amount", "outstanding_amount", "status"]
    )
    
    return {
        "case_info": case.as_dict(),
        "time_entries": time_entries,
        "invoices": invoices,
        "total_billed": sum(i.total_amount for i in invoices),
        "total_outstanding": sum(i.outstanding_amount for i in invoices),
    }

def generate_case_timeline_report(case):
    """Generate a timeline of activities for a case"""
    timeline = []
    
    # Add time entries
    time_entries = frappe.get_all("Time Entry",
        filters={"legal_case": case.name, "docstatus": 1},
        fields=["name", "activity_date", "employee", "activity_type", "hours"]
    )
    for entry in time_entries:
        timeline.append({
            "type": "Time Entry",
            "date": entry.activity_date,
            "title": f"Logged {entry.hours} hours for {entry.activity_type}",
            "author": entry.employee,
            "link": f"/app/time-entry/{entry.name}"
        })
        
    # Add hearings
    hearings = frappe.get_all("Court Hearing",
        filters={"legal_case": case.name},
        fields=["name", "hearing_date", "hearing_type", "status"]
    )
    for hearing in hearings:
        timeline.append({
            "type": "Court Hearing",
            "date": hearing.hearing_date,
            "title": f"{hearing.hearing_type} ({hearing.status})",
            "author": None,
            "link": f"/app/court-hearing/{hearing.name}"
        })

    # Sort the timeline by date
    timeline.sort(key=lambda x: x["date"])
    return {"timeline": timeline, "case_info": case.as_dict()}

@frappe.whitelist()
def get_client_portal_data(client_email):
    """Get data for client portal"""
    # Get client by email
    client = frappe.get_doc("Client", {"email": client_email})
    
    # Get client's cases
    cases = frappe.get_all("Legal Case",
        filters={"client": client.name},
        fields=["name", "case_title", "status", "practice_area", "date_opened", "lead_attorney"]
    )
    
    # Get recent time entries for client's cases
    recent_activities = frappe.get_all("Time Entry",
        filters={"client": client.name, "docstatus": 1},
        fields=["activity_type", "hours", "activity_date", "legal_case"],
        order_by="activity_date desc",
        limit=20
    )
    
    # Get invoices
    invoices = frappe.get_all("Legal Invoice",
        filters={"client": client.name},
        fields=["name", "posting_date", "total_amount", "outstanding_amount", "status"]
    )
    
    return {
        "client": client.as_dict(),
        "cases": cases,
        "recent_activities": recent_activities,
        "invoices": invoices,
        "summary": {
            "total_cases": len(cases),
            "active_cases": len([c for c in cases if c.status in ["Open", "In Progress"]]),
            "total_outstanding": sum([inv.outstanding_amount or 0 for inv in invoices])
        }
    }

# Background Jobs
def send_hearing_reminders():
    """Send reminders for upcoming hearings"""
    upcoming_hearings = frappe.get_all("Court Hearing",
        filters={
            "hearing_date": ["between", [now(), add_days(now(), 1)]],
            "reminder_sent": 0
        },
        fields=["name", "hearing_type", "hearing_date", "legal_case", "attorney"]
    )
    
    for hearing in upcoming_hearings:
        # Send email to attorney
        if hearing.attorney:
            frappe.sendmail(
                recipients=[hearing.attorney],
                subject=f"Reminder: {hearing.hearing_type} Tomorrow",
                message=f"""
                Dear Attorney,
                
                This is a reminder that you have a {hearing.hearing_type} scheduled for tomorrow at {hearing.hearing_date}.
                
                Case: {hearing.legal_case}
                
                Please ensure you are prepared.
                
                Best regards,
                Law Firm Management System
                """
            )
        
        # Mark reminder as sent
        frappe.db.set_value("Court Hearing", hearing.name, "reminder_sent", 1)
    
    frappe.db.commit()

def update_case_statuses():
    """Update case statuses based on various criteria"""
    # Close cases that are past statute of limitations
    overdue_cases = frappe.get_all("Legal Case",
        filters={
            "statute_of_limitations": ["<", today()],
            "status": ["!=", "Closed"]
        }
    )
    
    for case in overdue_cases:
        frappe.db.set_value("Legal Case", case.name, "status", "Closed")
        frappe.db.set_value("Legal Case", case.name, "case_outcome", "Statute Expired")
    
    frappe.db.commit()

# --- NEW FUNCTIONS ADDED BELOW ---

def archive_old_documents():
    """
    Archives legal documents and cases that are old or closed.
    This function can be triggered by a scheduled job.
    """
    frappe.log_error(title="Archive Documents", message="Starting archive process for old cases and documents.")
    
    # Example logic:
    # Find closed cases that were modified more than 5 years ago
    cases_to_archive = frappe.get_all(
        "Legal Case",
        filters={
            "status": "Closed",
            "modified": ["<", frappe.utils.add_years(today(), -5)]
        }
    )
    
    for case in cases_to_archive:
        frappe.db.set_value("Legal Case", case.name, "status", "Archived")
        frappe.log_error(title="Archive Documents", message=f"Case {case.name} has been archived.")
    
    frappe.db.commit()
    frappe.log_error(title="Archive Documents", message="Archive process completed.")

def generate_weekly_reports():
    """
    Generates and sends weekly performance reports to key users.
    This function can be scheduled to run weekly.
    """
    frappe.log_error(title="Weekly Reports", message="Starting weekly report generation.")
    
    # Example logic:
    # You would typically generate a report using data from a specific time period
    # and then send it via email.
    
    # Simple report generation
    billable_hours = frappe.db.sql("""
        SELECT SUM(billable_hours) as hours
        FROM `tabTime Entry`
        WHERE activity_date BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
    """)[0][0] or 0
    
    open_cases = frappe.db.count("Legal Case", filters={"status": ["in", ["Open", "In Progress"]]})
    
    # Example email sending
    subject = "Weekly Law Firm Performance Report"
    message = f"""
    Dear Management,

    Here is the summary of the firm's performance for the last week:

    Total Billable Hours: {billable_hours}
    Active Cases: {open_cases}

    Best regards,
    Law Firm Management System
    """
    
    # Replace with actual recipient emails
    # frappe.sendmail(recipients=["manager1@example.com", "manager2@example.com"], subject=subject, message=message)
    
    frappe.log_error(title="Weekly Reports", message="Weekly reports generated and sent.")