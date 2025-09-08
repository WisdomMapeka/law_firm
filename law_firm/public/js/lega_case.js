// file: law_firm/law_firm/doctype/legal_case/legal_case.js
frappe.ui.form.on('Legal Case', {
    onload: function(frm) {
        // Set 'Date Opened' to today's date for new cases
        if (frm.is_new()) {
            frm.set_value('date_opened', frappe.datetime.now_date());
            frm.set_value('status', 'Open');
            frm.set_value('priority', 'Medium');
        }
    },

    refresh: function(frm) {
        // Hide all billing-specific fields initially
        frm.toggle_display(['hourly_rate', 'flat_fee_amount', 'contingency_percentage', 'retainer_amount'], false);
        
        // Show fields based on the current 'billing_method'
        frm.trigger('billing_method');

        // Add custom buttons to the toolbar for quick actions
        if (!frm.is_new() && frm.doc.name) {
            // Button to create a new Time Entry linked to this case
            frm.add_custom_button(__('Log Time'), function() {
                frappe.new_doc('Time Entry', {
                    'legal_case': frm.doc.name,
                    'client': frm.doc.client
                });
            });

            // Button to create a new Legal Invoice
            frm.add_custom_button(__('Create Invoice'), function() {
                frappe.new_doc('Legal Invoice', {
                    'legal_case': frm.doc.name,
                    'client': frm.doc.client,
                    'billing_method': frm.doc.billing_method
                });
            });
        }
    },
    
    status: function(frm) {
        // Automatically set or clear the 'Date Closed' based on case status.
        if (frm.doc.status === 'Closed' || frm.doc.status === 'Settled' || frm.doc.status === 'Dismissed') {
            if (!frm.doc.date_closed) {
                frm.set_value('date_closed', frappe.datetime.now_date());
            }
        } else {
            frm.set_value('date_closed', null);
        }
    },

    billing_method: function(frm) {
        // Conditionally show/hide fields based on the selected billing method.
        const method = frm.doc.billing_method;
        
        // First, hide all specific billing fields
        frm.toggle_display('hourly_rate', false);
        frm.toggle_display('flat_fee_amount', false);
        frm.toggle_display('contingency_percentage', false);
        frm.toggle_display('retainer_amount', false);
        
        // Then, show the relevant field and make it required
        if (method === 'Hourly') {
            frm.toggle_display('hourly_rate', true);
        } else if (method === 'Flat Fee') {
            frm.toggle_display('flat_fee_amount', true);
        } else if (method === 'Contingency') {
            frm.toggle_display('contingency_percentage', true);
        } else if (method === 'Retainer') {
            frm.toggle_display('retainer_amount', true);
        }
    },

    client: function(frm) {
        // When a client is selected, fetch their standard billing rate if it exists
        if (frm.doc.client) {
            frappe.db.get_value('Client', frm.doc.client, 'billing_rate')
                .then(r => {
                    if (r.message && r.message.billing_rate) {
                        frm.set_value('hourly_rate', r.message.billing_rate);
                    }
                });
        }
    }
});