// file: law_firm/law_firm/doctype/time_entry/time_entry.js

frappe.ui.form.on('Time Entry', {
    onload: function(frm) {
        // Set 'Activity Date' to today's date when a new Time Entry form is loaded.
        if (frm.is_new()) {
            frm.set_value('activity_date', frappe.datetime.now_date());
            // Set current user as employee for new entries if not already set
            if (!frm.doc.employee) {
                frm.set_value('employee', frappe.session.user);
            }
        }
    },

    refresh: function(frm) {
        // Initial visibility of billing fields based on 'Billable' checkbox
        frm.trigger('billable');

        // Add a "View Legal Case" button to the form toolbar if a case is linked.
        if (!frm.is_new() && frm.doc.legal_case) {
            frm.add_custom_button(__('View Legal Case'), function() {
                frappe.set_route('Form', 'Legal Case', frm.doc.legal_case);
            });
        }
        
        // Disable editing of 'Invoiced' and 'Invoice Reference' fields unless approved/invoiced status
        frm.set_df_property('invoiced', 'read_only', frm.doc.billing_status !== 'Invoiced');
        frm.set_df_property('invoice_reference', 'read_only', frm.doc.billing_status !== 'Invoiced');

        // If the document is submitted, make all key fields read-only
        if (frm.doc.docstatus === 1) { // 1 means submitted
            frm.set_read_only(true);
            // Re-enable fields that should still be editable (e.g., approval details) if applicable
            // For example, if you want 'approved_by' and 'approval_date' to be editable after submission by a manager:
            // frm.set_df_property('approved_by', 'read_only', false);
            // frm.set_df_property('approval_date', 'read_only', false);
        } else {
            frm.set_read_only(false); // Enable editing for non-submitted docs
        }
    },

    legal_case: function(frm) {
        // When 'Legal Case' changes, fetch and set the 'Client' field.
        if (frm.doc.legal_case) {
            frappe.db.get_value('Legal Case', frm.doc.legal_case, 'client')
                .then(r => {
                    if (r.message && r.message.client) {
                        frm.set_value('client', r.message.client);
                    } else {
                        frm.set_value('client', null); // Clear if client not found
                        frappe.msgprint(__('Client not found for the selected Legal Case.'), __('Info'));
                    }
                });
        } else {
            frm.set_value('client', null); // Clear client if no legal case selected
        }
    },

    from_time: function(frm) {
        // Recalculate hours when 'From Time' changes.
        frm.trigger('calculate_hours');
    },

    to_time: function(frm) {
        // Recalculate hours when 'To Time' changes.
        frm.trigger('calculate_hours');
    },

    calculate_hours: function(frm) {
        // Client-side calculation of hours, similar to the backend logic.
        if (frm.doc.from_time && frm.doc.to_time && frm.doc.activity_date) {
            try {
                // Combine date and time for robust comparison, including overnight
                let from_dt = frappe.datetime.str_to_obj(`${frm.doc.activity_date} ${frm.doc.from_time}`);
                let to_dt = frappe.datetime.str_to_obj(`${frm.doc.activity_date} ${frm.doc.to_time}`);

                // If 'To Time' is earlier than 'From Time', assume it's on the next day
                if (to_dt < from_dt) {
                    to_dt = frappe.datetime.add_days(to_dt, 1);
                }

                const diff_milliseconds = to_dt.getTime() - from_dt.getTime();
                const hours = diff_milliseconds / (1000 * 60 * 60); // Convert milliseconds to hours
                frm.set_value('hours', round(hours, 2));

                // If billable, also trigger recalculation of billable amount
                if (frm.doc.billable) {
                    frm.set_value('billable_hours', round(hours, 2)); // Default billable hours to total hours
                    frm.trigger('calculate_billable_amount');
                }
            } catch (e) {
                console.error("Error calculating hours:", e);
                frappe.msgprint(__('Please enter valid times for From Time and To Time.'), __('Error'));
                frm.set_value('hours', 0.0);
                frm.set_value('billable_hours', 0.0);
                frm.set_value('billable_amount', 0.0);
            }
        } else {
            frm.set_value('hours', 0.0);
            frm.set_value('billable_hours', 0.0);
            frm.set_value('billable_amount', 0.0);
        }
    },

    billable: function(frm) {
        // Show/hide and make fields required based on 'Billable' checkbox.
        frm.toggle_display(['billing_rate', 'billable_hours', 'billable_amount'], frm.doc.billable);
        frm.toggle_reqd('billing_rate', frm.doc.billable);
        frm.toggle_reqd('billable_hours', frm.doc.billable);

        if (frm.doc.billable) {
            // Set default billable hours to total hours if billable is checked
            if (!frm.doc.billable_hours) {
                frm.set_value('billable_hours', frm.doc.hours || 0);
            }
            frm.trigger('calculate_billable_amount'); // Recalculate when billable status changes
        } else {
            // Clear values if not billable
            frm.set_value('billing_rate', 0.0);
            frm.set_value('billable_hours', 0.0);
            frm.set_value('billable_amount', 0.0);
        }
    },

    billing_rate: function(frm) {
        // Recalculate billable amount when 'Billing Rate' changes.
        frm.trigger('calculate_billable_amount');
    },

    billable_hours: function(frm) {
        // Recalculate billable amount when 'Billable Hours' changes.
        frm.trigger('calculate_billable_amount');
    },

    calculate_billable_amount: function(frm) {
        // Client-side calculation for billable amount.
        if (frm.doc.billable && frm.doc.billing_rate && frm.doc.billable_hours !== undefined && frm.doc.billable_hours >= 0) {
            frm.set_value('billable_amount', round(frm.doc.billing_rate * frm.doc.billable_hours, 2));
        } else if (!frm.doc.billable) {
            frm.set_value('billable_amount', 0.0);
        }
    },

    // Example of client-side validation
    validate: function(frm) {
        if (!frm.doc.description || frm.doc.description.length < 5) {
            frappe.throw(__('Please provide a more detailed description of the activity (at least 5 characters).'));
        }
        if (frm.doc.hours === 0 && (frm.doc.from_time && frm.doc.to_time)) {
             frappe.throw(__('Time entry must be for a duration greater than zero.'));
        }
    }
});

// Helper function to round numbers
function round(value, decimals) {
    return Number(Math.round(value + 'e' + decimals) + 'e-' + decimals);
}