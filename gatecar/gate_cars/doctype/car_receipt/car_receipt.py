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
		grand_total: DF.Currency
		local_tax: DF.Currency
		mainly_cost: DF.Int
		pickup_date: DF.Date
		previous_odometer: DF.Int
		real_days: DF.Data | None
		receiving_date: DF.Date
		sales_employee: DF.Link
		spending_tax: DF.Currency
		total_cost: DF.Currency
		total_distance: DF.Int
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Receipt"

	def before_insert(self) -> None:
		if not self.sales_employee:
			self.sales_employee = frappe.db.get_value(
				"Employee", {"user_id": frappe.session.user}, "name"
			)

	def validate(self) -> None:
		self.compute_totals()

	def compute_totals(self) -> None:
		"""Authoritative invoice totals (mirrors the client script).

		Tax base is the rental only (base cost + extra distance) — the damage
		compensation is added afterwards, untaxed.
			ضريبة الإنفاق = الإيجار × نسبة الإنفاق
			ضريبة المحلية = ضريبة الإنفاق × نسبة المحلية
			الإجمالي النهائي = الإيجار + الأضرار + ضريبة الإنفاق + ضريبة المحلية
		"""
		rental = (self.mainly_cost or 0) + (self.extra_cost or 0)

		settings = frappe.get_cached_doc("Gate Cars Settings")
		spend_rate = settings.spending_tax_rate or 0
		local_rate = settings.local_tax_rate or 0

		self.spending_tax = round(rental * spend_rate / 100.0, 2)
		self.local_tax = round(self.spending_tax * local_rate / 100.0, 2)
		self.total_cost = round(rental + (self.damage or 0), 2)
		self.grand_total = round(self.total_cost + self.spending_tax + self.local_tax, 2)

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
		from gatecar.maintenance_status import TYPE_KM, has_open_of_type

		next_oil = frappe.db.get_value("Car", self.car, "next_oil_change") or 0
		if not next_oil or self.current_odometer < next_oil:
			return

		if has_open_of_type(self.car, TYPE_KM):
			return

		car = frappe.get_doc("Car", self.car)
		car_label = f"{car.brand} {car.model} ({car.plate_no})"

		maintenance = frappe.get_doc({
			"doctype": "Periodic Maintenance",
			"car": self.car,
			"maintenance_type": TYPE_KM,
			"odometer_at_alert": self.current_odometer,
		})
		maintenance.insert(ignore_permissions=True)

		subject = f"تنبيه: السيارة {car_label} تحتاج صيانة دورية"
		message = f"السيارة {car_label} وصل عدادها إلى {self.current_odometer} كم وتجاوزت موعد الصيانة الدورية ({next_oil} كم)"

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
			"document_type": "Periodic Maintenance",
			"document_name": maintenance.name,
			"for_user": recipients[0] if recipients else "Administrator",
		}).insert(ignore_permissions=True)
