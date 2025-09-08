// file: law_firm/law_firm/doctype/client/client.js

frappe.ui.form.on('Client', {
    onload: function(frm) {
        // Set the default status to 'Active' for new documents
        if (frm.is_new()) {
            frm.set_value('status', 'Active');
        }
    },

    refresh: function(frm) {
        // Automatically set the date_joined field for new documents
        if (frm.is_new()) {
            frm.set_value('date_joined', frappe.datetime.now_date());
        }

        // Add a "View Cases" button to the form toolbar if the client is not new
        if (!frm.is_new() && frm.doc.name) {
            frm.add_custom_button(__('View Cases'), function() {
                frappe.set_route('List', 'Legal Case', {'client': frm.doc.name});
            });
            frm.add_custom_button(__('View Invoices'), function() {
                frappe.set_route('List', 'Legal Invoice', {'client': frm.doc.name});
            });
        }
    },

    client_type: function(frm) {
        // Conditionally show or hide fields based on client type
        if (frm.doc.client_type === 'Corporation' || frm.doc.client_type === 'Partnership') {
            frm.toggle_reqd('legal_entity_type', true);
            frm.toggle_reqd('business_registration', true);
            frm.toggle_reqd('date_of_incorporation', true);
            frm.set_df_property('legal_info_section', 'hidden', false);
        } else {
            frm.toggle_reqd('legal_entity_type', false);
            frm.toggle_reqd('business_registration', false);
            frm.toggle_reqd('date_of_incorporation', false);
            frm.set_df_property('legal_info_section', 'hidden', true);
        }
    },

    billing_address_same: function(frm) {
        // Copy address to billing address fields when checkbox is checked
        if (frm.doc.billing_address_same) {
            frm.set_value('billing_address_line_1', frm.doc.address_line_1);
            frm.set_value('billing_address_line_2', frm.doc.address_line_2);
            frm.set_value('billing_city', frm.doc.city);
            frm.set_value('billing_state', frm.doc.state);
            frm.set_value('billing_postal_code', frm.doc.postal_code);
            frm.set_value('billing_country', frm.doc.country);
        } else {
            // Clear billing address fields when checkbox is unchecked
            frm.set_value('billing_address_line_1', null);
            frm.set_value('billing_address_line_2', null);
            frm.set_value('billing_city', null);
            frm.set_value('billing_state', null);
            frm.set_value('billing_postal_code', null);
            frm.set_value('billing_country', null);
        }
    },

    // Example of custom validation before saving
    validate: function(frm) {
        // Ensure email is a valid format if provided
        if (frm.doc.email && !frappe.utils.validate_email(frm.doc.email)) {
            frappe.throw(__('Please enter a valid email address.'));
        }

        // Custom validation for corporations
        if (frm.doc.client_type === 'Corporation' && !frm.doc.date_of_incorporation) {
            frappe.throw(__('Date of Incorporation is required for a Corporation.'));
        }
    }
});