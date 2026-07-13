"""Monthly revenue-accrual generation for the owner-facing Car Activity Report.

Business rule (agreed with the app owner): the owner's report must reflect the
rental *contract* value, prorated by calendar day across the months a booking
spans, decoupled from when the customer actually pays (that risk is Gate Car's
alone). A booking that is still open at month-end gets an ESTIMATE for that
month based on the contractual rate/end_date; the month a Car Receipt actually
closes the contract gets a SETTLEMENT entry = the final invoice grand_total
minus everything already accrued for that booking in prior months. This is how
late-return days, excess mileage, and damage — all only known at closing — land
entirely in the closing month without ever revising a past month's figure.

Entries are Car Accrual Entry documents, submitted (docstatus=1) and never
edited or deleted after creation — corrections are posted as new "عكسي"
(reversal) entries, mirroring standard accounting practice. This matters
because these reports feed an external accounting system: once a month's
number has been read out, it must stay stable.
"""

import frappe
from frappe.utils import add_months, cint, date_diff, flt, get_first_day, get_last_day, getdate, today

from gatecar.utils import compute_rental_tax


def ensure_accrual_entries(booking_name: str) -> None:
	"""Idempotently create 'تقدير' entries for every open calendar month of an
	active booking, from its start_date up to the current month (capped at the
	contractual end_date). No-ops once the booking has a submitted Car Receipt —
	from then on its remaining balance is handled by create_closing_entry.

	Safe to call repeatedly (on submit, and daily from the scheduler): each
	period is checked via accrual_key before insert, and the field's DB-level
	uniqueness is the final backstop against duplicate creation.
	"""
	booking = frappe.get_doc("Car Booking", booking_name)
	if booking.docstatus != 1:
		return
	if not booking.car or not booking.start_date or not booking.end_date:
		return
	if frappe.db.exists("Car Receipt", {"booking": booking_name, "docstatus": 1}):
		return

	start = getdate(booking.start_date)
	contract_end = getdate(booking.end_date)
	horizon = min(contract_end, getdate(today()))
	if horizon < start:
		return

	period = get_first_day(start)
	while period <= horizon:
		period_start = max(start, period)
		period_end = min(horizon, get_last_day(period))
		if period_start <= period_end:
			_create_estimate_entry(booking, period, period_start, period_end)
		period = add_months(period, 1)


def _create_estimate_entry(booking, period, period_start, period_end) -> None:
	key = f"{booking.name}|{period}|تقدير"
	if frappe.db.exists("Car Accrual Entry", {"accrual_key": key}):
		return

	days = date_diff(period_end, period_start) + 1
	base_amount = round(flt(booking.rate_per_day) * days, 2)
	spending_tax, local_tax = compute_rental_tax(base_amount)

	entry = frappe.get_doc({
		"doctype": "Car Accrual Entry",
		"car": booking.car,
		"booking": booking.name,
		"period": period,
		"entry_type": "تقدير",
		"days": days,
		"base_amount": base_amount,
		"spending_tax": spending_tax,
		"local_tax": local_tax,
		"total_amount": round(base_amount + spending_tax + local_tax, 2),
	})
	entry.insert(ignore_permissions=True)
	entry.submit()


def create_closing_entry(car_receipt_name: str) -> None:
	"""Fired from Car Receipt.on_submit — settles the booking's remaining
	balance: the final invoice grand_total minus everything already accrued
	for it (estimates, and any prior reversals), broken down by
	base/spending_tax/local_tax so the components stay traceable.
	"""
	receipt = frappe.get_doc("Car Receipt", car_receipt_name)
	if not receipt.booking:
		return

	period = get_first_day(getdate(receipt.receiving_date or receipt.pickup_date))
	key = f"{receipt.booking}|{period}|تسوية إغلاق"
	if frappe.db.exists("Car Accrual Entry", {"accrual_key": key}):
		return

	prior_days, prior_base, prior_spend, prior_local = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(days), 0), COALESCE(SUM(base_amount), 0), COALESCE(SUM(spending_tax), 0), COALESCE(SUM(local_tax), 0)
		FROM `tabCar Accrual Entry`
		WHERE booking = %s AND docstatus = 1
		""",
		receipt.booking,
	)[0]

	# `days` here is what's left to attribute to the closing month specifically
	# (real_days minus days already counted in earlier periods' entries) — not
	# the contract's total real_days — so summing days per period stays meaningful.
	# real_days is a Data (string) field on Car Receipt, not Int — must cast.
	days = cint(receipt.real_days) - prior_days
	base_amount = round(flt(receipt.total_cost) - flt(prior_base), 2)
	spending_tax = round(flt(receipt.spending_tax) - flt(prior_spend), 2)
	local_tax = round(flt(receipt.local_tax) - flt(prior_local), 2)
	total_amount = round(base_amount + spending_tax + local_tax, 2)

	booking = frappe.get_doc("Car Booking", receipt.booking)
	entry = frappe.get_doc({
		"doctype": "Car Accrual Entry",
		"car": booking.car,
		"booking": booking.name,
		"period": period,
		"entry_type": "تسوية إغلاق",
		"days": days,
		"base_amount": base_amount,
		"spending_tax": spending_tax,
		"local_tax": local_tax,
		"total_amount": total_amount,
		"source_car_receipt": receipt.name,
	})
	entry.insert(ignore_permissions=True)
	entry.submit()


def reverse_booking_entries(booking_name: str) -> None:
	"""Fired from Car Booking.on_cancel — posts a reversal for every
	non-reversal entry this booking has (estimates and/or a settlement), each
	one linked back via `reverses` so at most one reversal per original entry
	can ever be created.
	"""
	entries = frappe.get_all(
		"Car Accrual Entry",
		filters={"booking": booking_name, "docstatus": 1, "entry_type": ["!=", "عكسي"]},
		fields=["name", "car", "booking", "period", "days", "base_amount", "spending_tax", "local_tax", "total_amount"],
	)
	for e in entries:
		_reverse_entry(e)


def reverse_closing_entry(car_receipt_name: str) -> None:
	"""Fired from Car Receipt.on_cancel — reverses only that receipt's own
	settlement entry, leaving the booking's earlier monthly estimates intact
	(the booking itself is still real; only its closing figure is being
	corrected, typically followed by a new amended Car Receipt).
	"""
	entry = frappe.db.get_value(
		"Car Accrual Entry",
		{"source_car_receipt": car_receipt_name, "docstatus": 1, "entry_type": "تسوية إغلاق"},
		["name", "car", "booking", "period", "days", "base_amount", "spending_tax", "local_tax", "total_amount"],
		as_dict=True,
	)
	if entry:
		_reverse_entry(entry)


def _reverse_entry(e) -> None:
	if frappe.db.exists("Car Accrual Entry", {"reverses": e.name}):
		return
	rev = frappe.get_doc({
		"doctype": "Car Accrual Entry",
		"car": e.car,
		"booking": e.booking,
		"period": e.period,
		"entry_type": "عكسي",
		"days": -cint(e.days),
		"base_amount": -flt(e.base_amount),
		"spending_tax": -flt(e.spending_tax),
		"local_tax": -flt(e.local_tax),
		"total_amount": -flt(e.total_amount),
		"reverses": e.name,
	})
	# Fired from the parent Car Booking/Car Receipt's own on_cancel, whose
	# docstatus is already 2 by this point — Frappe's generic link validation
	# would otherwise refuse to link a new document to an already-cancelled
	# one. Linking to it here is the whole point (the reversal's audit trail),
	# not an oversight.
	rev.flags.ignore_links = True
	rev.insert(ignore_permissions=True)
	rev.submit()


def monthly_accrual_job() -> None:
	"""Scheduled daily — idempotently rolls every still-open booking's accrual
	forward as calendar months pass. Safe to run more than once a day.
	"""
	for booking_name in frappe.get_all("Car Booking", filters={"docstatus": 1}, pluck="name"):
		try:
			ensure_accrual_entries(booking_name)
		except Exception:
			frappe.log_error(title=f"Car accrual generation failed for {booking_name}")


@frappe.whitelist()
def reconcile_accrual_entries() -> list[dict]:
	"""Integrity check: for every closed booking, the sum of its Car Accrual
	Entry rows (estimates + settlement + any reversals) must equal exactly the
	Car Receipt's grand_total — that equality is the whole point of the
	settlement formula. Any mismatch here means generation drifted from the
	invoice and must be investigated before the numbers are trusted downstream
	(the external accounting system has no way to catch this on its own).

	Returns a list of mismatches (empty means everything reconciles).
	"""
	rows = frappe.db.sql(
		"""
		SELECT
			r.name AS car_receipt, r.booking, r.grand_total,
			COALESCE(SUM(ae.total_amount), 0) AS accrued_total
		FROM `tabCar Receipt` r
		LEFT JOIN `tabCar Accrual Entry` ae ON ae.booking = r.booking AND ae.docstatus = 1
		WHERE r.docstatus = 1
		GROUP BY r.name
		""",
		as_dict=True,
	)

	mismatches = []
	for r in rows:
		diff = round(flt(r.accrued_total) - flt(r.grand_total), 2)
		if abs(diff) > 0.01:
			mismatches.append({
				"booking": r.booking,
				"car_receipt": r.car_receipt,
				"grand_total": r.grand_total,
				"accrued_total": r.accrued_total,
				"difference": diff,
			})

	if mismatches:
		frappe.log_error(
			title="Car accrual reconciliation mismatch",
			message=frappe.as_json(mismatches),
		)
	return mismatches
