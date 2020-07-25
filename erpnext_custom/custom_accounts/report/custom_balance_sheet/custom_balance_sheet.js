// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.require("assets/erpnext/js/financial_statements.js", function() {

	frappe.query_reports["Custom Balance Sheet"] = $.extend({}, erpnext.financial_statements);

	erpnext.utils.add_dimensions('Custom Balance Sheet', 10);


	frappe.query_reports["Custom Balance Sheet"].onload =  function(report) {
		// dropdown for links to other financial statements
		erpnext.financial_statements.filters = get_filters()

		let fiscal_year = frappe.defaults.get_user_default("fiscal_year")

		frappe.model.with_doc("Fiscal Year", fiscal_year, function (r) {
			var fy = frappe.model.get_doc("Fiscal Year", fiscal_year);
			frappe.query_report.set_filter_value({
				period_start_date: fy.year_start_date,
				period_end_date: fy.year_end_date
			});
		});

		console.log(report.page)
		report.page.add_inner_button(__("Print"), function() {
			frappe.ui.get_print_settings(false,
                        print_settings => frappe.query_report.print_report(print_settings),
                        frappe.query_report.report_doc.letter_head,
                        frappe.query_report.get_visible_columns())
		});
	};


	frappe.query_reports["Custom Balance Sheet"]["filters"].push({
		"fieldname":"period_start_date",
		"label": __("Start Date"),
		"fieldtype": "Date",
		"hidden":0 ,
		"reqd": 1,
		default: frappe.defaults.get_user_default("year_start_date")
	});


	frappe.query_reports["Custom Balance Sheet"]["filters"].push({
		"fieldname":"period_end_date",
		"label": __("End Date"),
		"fieldtype": "Date",
		"hidden": 0,
		"reqd": 0,
		default: frappe.datetime.get_today()
	});


	let filters = frappe.query_reports["Custom Balance Sheet"]["filters"];
	frappe.query_reports["Custom Balance Sheet"]["filters"] = toggle(filters, ["filter_based_on","from_fiscal_year","to_fiscal_year","finance_book","periodicity","presentation_currency","cost_center"],true);


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


