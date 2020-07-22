# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
# m=

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint

from erpnext.accounts.report.financial_statements import (get_period_list, get_columns,get_accounts,filter_accounts,
														  get_appropriate_currency,set_gl_entries_by_account,
														  accumulate_values_into_parents,accumulate_values_into_parents,
														  prepare_data,add_total_row,filter_out_zero_value_rows)
from datetime import datetime

from six import itervalues


def execute(filters=None):

	def get_accounts_matched_account_number(company, accounts):
		accounts_codes = str(accounts).split(" ")
		account_matches = dict(debit=[], credit=[])

		for account_match in accounts_codes:
			if account_match.startswith("+"):
				account_matches.get('debit').extend(get_accounts_with_account_number(company, account_match[1:]))
			elif account_match.startswith("-"):
				account_matches.get('credit').extend(get_accounts_with_account_number(company, account_match[1:]))

		return account_matches

	def get_accounts_with_account_number(company, match):
		accounts = frappe.db.sql("""
				select name from `tabAccount` where company=%s and is_group = 0 and account_number LIKE %s order by lft""",
								 (company, match + "%"), as_dict=True)

		return accounts

	def remove_group_accounts(grouper):
		grouper = {key: value for (key, value) in grouper.items() if value.is_group == 0}


	def compute_from_grouper(grouper,accounts,period_list):
		value_current_year = 0
		value_previous_year = 0
		for	account in accounts.get("debit"):
			acc = grouper.get(account.get("name"))
			if acc is not None:
				value_previous_year += acc.get("%s_debit" % period_list[0].get('key'),0.0)
				value_current_year += acc.get("%s_debit" % period_list[1].get('key'),0.0)

		for	account in accounts.get("credit"):
			acc = grouper.get(account.get("name"))
			if acc is not None:
				value_previous_year += acc.get("%s_credit" % period_list[0].get('key'), 0.0)
				value_current_year += acc.get("%s_credit" % period_list[1].get('key'), 0.0)

		return (value_previous_year,value_current_year)




	# get previous fiscal year from filter
	period_list = get_period_list(int(filters.to_fiscal_year) - 1, filters.to_fiscal_year,filters.periodicity, company=filters.company)


	currency = filters.presentation_currency or frappe.get_cached_value('Company',  filters.company,  "default_currency")

	if period_list:
		current_year_from_date = period_list[len(period_list) - 1]
		current_year_from_date.from_date =datetime.strptime(filters.period_start_date, '%Y-%m-%d').date()
		current_year_from_date.to_date = datetime.strptime(filters.period_end_date, '%Y-%m-%d').date()
		period_list[len(period_list) - 1] = current_year_from_date

	grouper = {}

	asset = get_data(filters.company, "Asset", "Debit", period_list, grouper,
		only_current_fiscal_year=False, filters=filters,
		accumulated_values=filters.accumulated_values)


	liability = get_data(filters.company, "Liability", "Credit", period_list,grouper,
		only_current_fiscal_year=False, filters=filters,
		accumulated_values=filters.accumulated_values)

	equity = get_data(filters.company, "Equity", "Credit", period_list,grouper,
		only_current_fiscal_year=False, filters=filters,
		accumulated_values=filters.accumulated_values)

	# grouper now hold leaf accounts that have credit and debit balance for current date and last fiscal year
	# at a little cost

	# Asset get debit balance of all specified accounts
	# Liability get the credit balance of all specified accounts
	remove_group_accounts(grouper)
	configuration = frappe.get_doc('Financial Report Configuration', "BSH002")
	grouping, group = dict(), None

	indexes = 0
	for (index, config) in enumerate(configuration.get("financial_report_configuration_item")):
		# to be sorted by serial number

		group = config.get('label') if config.get('type') == 'H1' or group is None else group

		if config.get('type') == 'H1':
			grouped_index = 0
			indexes = 0
			grouping[group] = {}

		if config.get('accounts') is None:
			grouping[group].update({
				config.get('label'): dict(
					tag=config.get('type'),
					title=config.get('label'),
					index = grouped_index
				)
			})
			grouped_index = grouped_index + 1

		elif str(config.get('accounts')).find("L") is not -1:

			total_previous_year = 0
			total_current_year = 0

			codes = str(config.get('accounts')).split(" ")
			for code in codes:
				index_ = int(str(code[2:]))
				account_at_index = grouping[group].get("L%s" % index_)
				if account_at_index:
					total_previous_year = total_previous_year + account_at_index.get('value')[0]
					total_current_year = total_current_year +  account_at_index.get('value')[1]

			account_ = dict(
				tag=config.get('type'),
				title=config.get('label'),
				value=(total_previous_year,total_current_year),
				index=3.5,
			)
			grouped_index = grouped_index + 1
			grouping[group].update({config.get('label'): account_})

		else:
			account_ = dict(
				tag=config.get('type'),
				title=config.get('label'),
				index=3.5,
				value = compute_from_grouper(grouper, get_accounts_matched_account_number(filters.company,
												 config.get('accounts')),period_list)
			)
			grouped_index = grouped_index + 1
			grouping[group].update({ "L%s" % indexes : account_})
			indexes = indexes + 1


	provisional_profit_loss, total_credit = get_provisional_profit_loss(asset, liability, equity,
		period_list, filters.company, currency)

	message, opening_balance = check_opening_balance(asset, liability, equity)

	data = []
	data.extend(asset or [])
	data.extend(liability or [])
	data.extend(equity or [])

	if opening_balance and round(opening_balance,2) !=0:
		unclosed ={
			"account_name": "'" + _("Unclosed Fiscal Years Profit / Loss (Credit)") + "'",
			"account": "'" + _("Unclosed Fiscal Years Profit / Loss (Credit)") + "'",
			"warn_if_negative": True,
			"currency": currency
		}
		for period in period_list:
			unclosed[period.key] = opening_balance
			if provisional_profit_loss:
				provisional_profit_loss[period.key] = provisional_profit_loss[period.key] - opening_balance

		unclosed["total"]=opening_balance
		data.append(unclosed)

	if provisional_profit_loss:
		data.append(provisional_profit_loss)
	if total_credit:
		data.append(total_credit)

	columns = get_columns(filters.periodicity, period_list, filters.accumulated_values, company=filters.company)

	report_summary = get_report_summary(period_list, asset, liability, equity, provisional_profit_loss,
		total_credit, currency, filters)

	print_data = []
	for group in itervalues(grouping):
		for item in itervalues(group):
			print_data.append(item)

	data.append({ "print_data" : print_data})

	return columns, data, message, None, report_summary

def get_provisional_profit_loss(asset, liability, equity, period_list, company, currency=None, consolidated=False):
	provisional_profit_loss = {}
	total_row = {}
	if asset and (liability or equity):
		total = total_row_total=0
		currency = currency or frappe.get_cached_value('Company',  company,  "default_currency")
		total_row = {
			"account_name": "'" + _("Total (Credit)") + "'",
			"account": "'" + _("Total (Credit)") + "'",
			"warn_if_negative": True,
			"currency": currency
		}
		has_value = False

		for period in period_list:
			key = period if consolidated else period.key
			effective_liability = 0.0
			if liability:
				effective_liability += flt(liability[-2].get(key))
			if equity:
				effective_liability += flt(equity[-2].get(key))

			provisional_profit_loss[key] = flt(asset[-2].get(key)) - effective_liability
			total_row[key] = effective_liability + provisional_profit_loss[key]

			if provisional_profit_loss[key]:
				has_value = True

			total += flt(provisional_profit_loss[key])
			provisional_profit_loss["total"] = total

			total_row_total += flt(total_row[key])
			total_row["total"] = total_row_total

		if has_value:
			provisional_profit_loss.update({
				"account_name": "'" + _("Provisional Profit / Loss (Credit)") + "'",
				"account": "'" + _("Provisional Profit / Loss (Credit)") + "'",
				"warn_if_negative": True,
				"currency": currency
			})

	return provisional_profit_loss, total_row

def check_opening_balance(asset, liability, equity):
	# Check if previous year balance sheet closed
	opening_balance = 0
	float_precision = cint(frappe.db.get_default("float_precision")) or 2
	if asset:
		opening_balance = flt(asset[0].get("opening_balance", 0), float_precision)
	if liability:
		opening_balance -= flt(liability[0].get("opening_balance", 0), float_precision)
	if equity:
		opening_balance -= flt(equity[0].get("opening_balance", 0), float_precision)

	opening_balance = flt(opening_balance, float_precision)
	if opening_balance:
		return _("Previous Financial Year is not closed"),opening_balance
	return None,None

def get_report_summary(period_list, asset, liability, equity, provisional_profit_loss, total_credit, currency,
	filters, consolidated=False):

	net_asset, net_liability, net_equity, net_provisional_profit_loss = 0.0, 0.0, 0.0, 0.0

	if filters.get('accumulated_values'):
		period_list = [period_list[-1]]

	for period in period_list:
		key = period if consolidated else period.key
		if asset:
			net_asset += asset[-2].get(key)
		if liability:
			net_liability += liability[-2].get(key)
		if equity:
			net_equity += equity[-2].get(key)
		if provisional_profit_loss:
			net_provisional_profit_loss += provisional_profit_loss.get(key)

	return [
		{
			"value": net_asset,
			"label": "Total Asset",
			"indicator": "Green",
			"datatype": "Currency",
			"currency": currency
		},
		{
			"value": net_liability,
			"label": "Total Liability",
			"datatype": "Currency",
			"indicator": "Red",
			"currency": currency
		},
		{
			"value": net_equity,
			"label": "Total Equity",
			"datatype": "Currency",
			"indicator": "Blue",
			"currency": currency
		},
		{
			"value": net_provisional_profit_loss,
			"label": "Provisional Profit / Loss (Credit)",
			"indicator": "Green" if net_provisional_profit_loss > 0 else "Red",
			"datatype": "Currency",
			"currency": currency
		}
	]




def get_data(
		company, root_type, balance_must_be, period_list, grouper, filters=None,
		accumulated_values=1, only_current_fiscal_year=True, ignore_closing_entries=False,
		ignore_accumulated_values_for_fy=False , total = True):


	accounts = get_accounts(company, root_type)

	if not accounts:
		return None

	accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)

	company_currency = get_appropriate_currency(company, filters)

	gl_entries_by_account = {}

	for root in frappe.db.sql("""select lft, rgt from tabAccount
			where root_type=%s and ifnull(parent_account, '') = ''""", root_type, as_dict=1):

		set_gl_entries_by_account(
			company,
			period_list[0]["year_start_date"] if only_current_fiscal_year else None,
			period_list[-1]["to_date"],
			root.lft, root.rgt, filters,
			gl_entries_by_account, ignore_closing_entries=ignore_closing_entries
		)
	calculate_values(
		accounts_by_name, gl_entries_by_account, period_list, accumulated_values, ignore_accumulated_values_for_fy)

	grouper.update(accounts_by_name)

	accumulate_values_into_parents(accounts, accounts_by_name, period_list, accumulated_values)

	out = prepare_data(accounts, balance_must_be, period_list, company_currency)

	out = filter_out_zero_value_rows(out, parent_children_map)

	if out and total:
		add_total_row(out, root_type, balance_must_be, period_list, company_currency)

	return out



def calculate_values(
		accounts_by_name, gl_entries_by_account, period_list, accumulated_values, ignore_accumulated_values_for_fy):

	for entries in itervalues(gl_entries_by_account):
		for entry in entries:
			d = accounts_by_name.get(entry.account)
			if  d:
				for period in period_list:
					# check if posting date is within the period
					if entry.posting_date <= period.to_date:
						if (accumulated_values or entry.posting_date >= period.from_date) and \
							(not ignore_accumulated_values_for_fy or
								entry.fiscal_year == period.to_date_fiscal_year):

							d[period.key] = d.get(period.key, 0.0) + flt(entry.debit) - flt(entry.credit)
							d[period.key+"_debit"] = d.get(period.key+"_debit", 0.0) + flt(entry.debit)
							d[period.key+"_credit"] = d.get(period.key+"_credit", 0.0) + flt(entry.credit)

				if entry.posting_date < period_list[0].year_start_date:
					d["opening_balance"] = d.get("opening_balance", 0.0) + flt(entry.debit) - flt(entry.credit)