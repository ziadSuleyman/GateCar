import frappe
from frappe import _
from frappe.model.document import Document

from gatecar.maintenance_status import (
	MAINTENANCE_INTERVAL_KM,
	release_car,
	set_car_under_maintenance,
)


class PeriodicMaintenance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		car: DF.Link
		cost: DF.Currency
		maintenance_type: DF.Literal["\u0635\u064a\u0627\u0646\u0629 \u062f\u0648\u0631\u064a\u0629 (\u0643\u0645)"]
		odometer_at_alert: DF.Int
		oil_name: DF.Data | None
		التاريخ: DF.Date | None
		الفاتورة: DF.Attach | None
	# end: auto-generated types

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		car: DF.Link
		cost: DF.Currency
		maintenance_type: DF.Literal["صيانة دورية (كم)"]
		odometer_at_alert: DF.Int
		oil_name: DF.Data | None
		التاريخ: DF.Date | None
		الفاتورة: DF.Attach | None

	_DOCTYPE_NAME = "Periodic Maintenance"

	def validate(self) -> None:
		# Block approval until the paperwork is complete.
		if self.docstatus == 1:
			if not self.التاريخ:
				frappe.throw(_("يجب إدخال تاريخ الصيانة قبل الاعتماد"))
			if not self.oil_name:
				frappe.throw(_("يجب إدخال ما تم إصلاحه قبل الاعتماد"))
			if not self.الفاتورة:
				frappe.throw(_("يجب إرفاق الفاتورة قبل اعتماد الصيانة"))

	def after_insert(self) -> None:
		# Opening a maintenance request puts the car into maintenance.
		set_car_under_maintenance(self.car)

	def on_submit(self) -> None:
		# km service done -> schedule the next one and free the car if nothing else holds it.
		current = frappe.db.get_value("Car", self.car, "current_odometer") or 0
		frappe.db.set_value("Car", self.car, "next_oil_change", current + MAINTENANCE_INTERVAL_KM)
		release_car(self.car, exclude=self.name)

	def on_cancel(self) -> None:
		release_car(self.car, exclude=self.name)
