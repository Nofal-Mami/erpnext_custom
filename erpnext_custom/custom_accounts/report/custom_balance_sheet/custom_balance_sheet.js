// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.require("assets/erpnext/js/financial_statements.js", function() {
	frappe.query_reports["Custom Balance Sheet"] = $.extend({}, erpnext.financial_statements);

	erpnext.utils.add_dimensions('Custom Balance Sheet', 10);

	frappe.query_reports["Custom Balance Sheet"]["filters"].push({
		"fieldname": "accumulated_values",
		"label": __("Accumulated Values"),
		"fieldtype": "Check",
		"default": 1
	});

	frappe.query_reports["Custom Balance Sheet"]["filters"].push({
		"fieldname": "include_default_book_entries",
		"label": __("Include Default Book Entries"),
		"fieldtype": "Check",
		"default": 1
	});

	let filters = frappe.query_reports["Custom Balance Sheet"]["filters"];
	filters = toggle(filters, ["filter_based_on","from_fiscal_year","to_fiscal_year"],true)
	frappe.query_reports["Custom Balance Sheet"]["filters"] = toggle(filters, ["period_start_date","period_end_date"],false)


});


function toggle(filters, fields, value) {
	return filters.map((element)=>{
		if(fields instanceof Array){
			if(fields.includes(element.fieldname)){
				element.hidden = value;
			}
		}else{
			if(fields === element.fieldname){
				element.hidden = value;
			}
		}

		return element;
	})
}


