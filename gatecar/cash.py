"""Single company-wide cash box balance.

Two sources feed it: Revenue vouchers (قبض/دفع, tied to a booking, never
submittable — every row always counts) and Cash Transaction entries (سحوبات
خارجية فقط, not tied to any booking, submittable — only docstatus=1 rows
count, and every row is a withdrawal). Kept in one function so every caller
(the Cash Transaction form's live balance display, its own over-withdrawal
check, and any future report/dashboard) reads the same number.
"""

import frappe
from frappe.utils import flt


def get_cash_balance() -> float:
	revenue_net = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(CASE WHEN payment_type = 'قبض' THEN amount ELSE -amount END), 0)
		FROM `tabRevenue`
		"""
	)[0][0]

	withdrawals = frappe.db.sql(
		"SELECT COALESCE(SUM(amount), 0) FROM `tabCash Transaction` WHERE docstatus = 1"
	)[0][0]

	return flt(revenue_net) - flt(withdrawals)


@frappe.whitelist()
def get_cash_balance_api() -> float:
	frappe.has_permission("Cash Transaction", "read", throw=True)
	return get_cash_balance()
