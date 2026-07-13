"""One-time backfill: give every historical, already-closed Car Receipt a
'تسوية إغلاق' Car Accrual Entry in the month it was originally issued.

No monthly 'تقدير' estimates are created retroactively for these — only the
settlement, landing the full grand_total in the receipt's own month, exactly
as agreed for contracts that were never tracked month-by-month before this
feature existed. Since no prior accrual entries exist yet for these bookings,
create_closing_entry() naturally produces settlement == full grand_total.
"""

import frappe

from gatecar.accrual import create_closing_entry


def execute():
	if not frappe.db.table_exists("Car Accrual Entry"):
		return

	receipts = frappe.get_all("Car Receipt", filters={"docstatus": 1}, pluck="name")
	for receipt_name in receipts:
		try:
			create_closing_entry(receipt_name)
		except Exception:
			frappe.log_error(title=f"Accrual backfill failed for Car Receipt {receipt_name}")
