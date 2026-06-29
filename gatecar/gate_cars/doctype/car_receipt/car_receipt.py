# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CarReceipt(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		allowed_limit: DF.Int
		amended_from: DF.Link | None
		booking: DF.Link
		car: DF.Link
		current_odometer: DF.Int
		customer_name: DF.Data | None
		damage: DF.Currency
		down_payment: DF.Currency
		duration_days: DF.Int
		extra_cost: DF.Currency
		extra_distance: DF.Int
		mainly_cost: DF.Int
		pickup_date: DF.Date
		previous_odometer: DF.Int
		real_days: DF.Data | None
		receiving_date: DF.Date
		sales_employee: DF.Link
		total_cost: DF.Currency
		total_distance: DF.Int
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Receipt"

	def before_insert(self) -> None:
		if not self.sales_employee:
			self.sales_employee = frappe.db.get_value(
				"Employee", {"user_id": frappe.session.user}, "name"
			)

	def on_submit(self) -> None:
		if self.car:
			frappe.db.set_value("Car", self.car, "status", "متوفر")
			if self.current_odometer:
				frappe.db.set_value("Car", self.car, "current_odometer", self.current_odometer)
				self.check_oil_change()
		if self.booking and self.notes:
			revenues = frappe.get_all("Revenue", filters={"booking_reference": self.booking}, pluck="name")
			for rev in revenues:
				frappe.db.set_value("Revenue", rev, "notes", self.notes)

	def check_oil_change(self) -> None:
		next_oil = frappe.db.get_value("Car", self.car, "next_oil_change") or 0
		if not next_oil or self.current_odometer < next_oil:
			return

		has_open = frappe.db.exists(
			"Oil Change", {"car": self.car, "docstatus": 0}
		)
		if has_open:
			return

		car = frappe.get_doc("Car", self.car)
		car_label = f"{car.brand} {car.model} ({car.plate_no})"

		oil_change = frappe.get_doc({
			"doctype": "Oil Change",
			"car": self.car,
			"odometer_at_alert": self.current_odometer,
		})
		oil_change.insert(ignore_permissions=True)

		subject = f"تنبيه: السيارة {car_label} تحتاج تغيير زيت"
		message = f"السيارة {car_label} وصل عدادها إلى {self.current_odometer} كم وتجاوزت موعد تغيير الزيت ({next_oil} كم)"

		from gatecar.tasks import get_notification_recipients
		recipients = get_notification_recipients(
			frappe.db.get_value("Vehicle Fleet", car.fleet, "owner") if car.fleet else None
		)
		for user in recipients:
			frappe.publish_realtime(
				"msgprint",
				{"message": message, "title": subject, "indicator": "Orange"},
				user=user,
			)

		frappe.get_doc({
			"doctype": "Notification Log",
			"subject": subject,
			"email_content": message,
			"type": "Alert",
			"document_type": "Oil Change",
			"document_name": oil_change.name,
			"for_user": recipients[0] if recipients else "Administrator",
		}).insert(ignore_permissions=True)
