# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

"""Shared helpers linking maintenance/expense records to the Car status.

A car is considered "under maintenance" (and blocked from new rentals) while it
has at least one OPEN (draft):
  * `Periodic Maintenance` — km/oil based service, or
  * `Car Expense` of a date-renewal type (تأمين إلزامي / تأمين شامل / تسجيل).

This module keeps the Car.status field in sync and is used by the booking flow
to prevent renting a car whose service or legal paperwork is due.
"""

import frappe
from frappe import _

MAINTENANCE_DOCTYPES = ("Periodic Maintenance",)

STATUS_MAINTENANCE = "داخل الصيانة"
STATUS_AVAILABLE = "متوفر"
# Active-rental states we must not overwrite when a maintenance record opens.
STATUS_LOCKED = ("مؤجر", "محجوز")

# Kilometre interval between periodic (oil) services.
MAINTENANCE_INTERVAL_KM = 5000

# The only Periodic Maintenance type (km/oil service).
TYPE_KM = "صيانة دورية (كم)"

# Date-renewal expense types (now handled by Car Expense) and the Car field each renews.
DATE_FIELD_BY_TYPE = {
	"تأمين إلزامي": "mandatory_insurance_date",
	"تأمين شامل": "تاريخ_التأمين_الشامل",
	"تسجيل": "finish_date",
}
DATE_EXPENSE_TYPES = tuple(DATE_FIELD_BY_TYPE.keys())
EXPENSE_TYPE_GENERAL = "عام"


def _open_names(doctype: str, car: str, extra: dict | None = None) -> list[str]:
	filters = {"car": car, "docstatus": 0}
	if extra:
		filters.update(extra)
	return frappe.get_all(doctype, filters=filters, pluck="name")


def has_open_maintenance(car: str, exclude: str | None = None) -> bool:
	"""True if the car has any open (docstatus=0) record that locks it.

	Covers general repairs, km service, and date-renewal Car Expenses. Plain
	(عام) Car Expenses never lock the car and are ignored here.
	"""
	if not car:
		return False
	sources = (
		("Periodic Maintenance", None),
		("Car Expense", {"expense_type": ["in", list(DATE_EXPENSE_TYPES)]}),
	)
	for doctype, extra in sources:
		if any(name != exclude for name in _open_names(doctype, car, extra)):
			return True
	return False


def has_open_of_type(car: str, maintenance_type: str) -> bool:
	"""True if the car has an open Periodic Maintenance of a specific type (km)."""
	if not car:
		return False
	return bool(
		frappe.get_all(
			"Periodic Maintenance",
			filters={"car": car, "docstatus": 0, "maintenance_type": maintenance_type},
			limit=1,
		)
	)


def has_open_expense_of_type(car: str, expense_type: str) -> bool:
	"""True if the car has an open Car Expense of a specific date-renewal type.

	Used by the daily scheduler so each trigger (insurance/registration) opens at
	most one request at a time.
	"""
	if not car:
		return False
	return bool(
		frappe.get_all(
			"Car Expense",
			filters={"car": car, "docstatus": 0, "expense_type": expense_type},
			limit=1,
		)
	)


def set_car_under_maintenance(car: str) -> None:
	"""Move an available car into the maintenance status.

	Active rentals/bookings are left untouched (the open-maintenance record still
	blocks any *new* booking), so we never corrupt live rental tracking.
	"""
	if not car:
		return
	current = frappe.db.get_value("Car", car, "status")
	if current in STATUS_LOCKED or current == STATUS_MAINTENANCE:
		return
	frappe.db.set_value("Car", car, "status", STATUS_MAINTENANCE)


def release_car(car: str, exclude: str | None = None) -> None:
	"""Return a car to available once no open maintenance remains.

	`exclude` is the record being submitted/cancelled, so it is not counted as
	still-open. Only a car currently *in* maintenance is released, so we never
	override a status set elsewhere.
	"""
	if not car:
		return
	if has_open_maintenance(car, exclude=exclude):
		return
	if frappe.db.get_value("Car", car, "status") == STATUS_MAINTENANCE:
		frappe.db.set_value("Car", car, "status", STATUS_AVAILABLE)


def guard_not_under_maintenance(car: str) -> None:
	"""Raise if the car is under maintenance — used by the booking flow."""
	if not car:
		return
	status = frappe.db.get_value("Car", car, "status")
	if status == STATUS_MAINTENANCE or has_open_maintenance(car):
		frappe.throw(
			_("لا يمكن حجز أو تأجير السيارة {0} لأنها تحت الصيانة حالياً. "
			  "يجب إتمام صيانتها أولاً.").format(car)
		)
