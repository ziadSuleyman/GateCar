# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, date_diff, flt

from gatecar.utils import compute_rental_tax


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
		self.calculate_mainly_cost()
		self.calculate_distance_charges()
		self.compute_totals()

	def calculate_distance_charges(self) -> None:
		"""Authoritative excess-mileage total_distance/extra_distance/extra_cost.

		Previously computed only by browser client scripts (calc distance,
		calc_extra_distance_real, calc_extra_cost_real) — a Car Receipt created
		or submitted any other way (console, API, import) silently kept these
		fields at zero even with real odometer readings entered, quietly
		dropping excess-mileage charges. Mirrors the client scripts' formulas
		exactly; those stay enabled for live preview while editing.

		يعتمد على allowed_limit الذي حسبته calculate_mainly_cost بالفعل.
		"""
		self.total_distance = max(0, cint(self.current_odometer or 0) - cint(self.previous_odometer or 0))
		self.extra_distance = max(0, self.total_distance - cint(self.allowed_limit or 0))
		self.extra_cost = round(self.extra_distance * 0.20, 2)

	def calculate_mainly_cost(self) -> None:
		"""Authoritative real-days + tiered base rental.

		Single source of truth: two client scripts (calc_extra_cost,
		find_mainly_price) used to race to set mainly_cost differently on the
		same fields, and a third (calc_real_days) computed real_days without
		the +1 that Car Booking.duration_days uses — so an on-time return
		invoiced one day short of the contract. Both are now disabled in
		favor of this method.

		عدد الأيام الفعلي شامل يوم الاستلام ويوم التسليم (+1)، مطابقاً لحساب
		duration_days في العقد الأصلي. تمديد مدة الإيجار عند الإغلاق ينقل
		السيارة تلقائياً إلى شريحة سعر أعلى (متوسطة/كبرى) من Car Category —
		سلوك مقصود في نموذج العمل، وليس خطأ.
		"""
		self.real_days = 0
		self.mainly_cost = 0
		self.allowed_limit = 0

		if not (self.pickup_date and self.receiving_date and self.booking):
			return

		real_days = date_diff(self.receiving_date, self.pickup_date) + 1
		if real_days < 1:
			return

		if self.docstatus == 0 and real_days < 3:
			frappe.throw(
				"ممنوع تأجير السيارات لأقل من 3 أيام كحد أدنى."
				f"<br>عدد الأيام الفعلي بالتواريخ الحالية هو: {real_days} أيام فقط."
			)

		self.real_days = real_days
		self.allowed_limit = real_days * 200 if real_days < 30 else 4000

		category = frappe.db.get_value("Car Booking", self.booking, "category_car")
		if not category:
			return

		if real_days <= 7:
			tier_field = "small_term"
		elif real_days <= 20:
			tier_field = "med_term"
		else:
			tier_field = "long_term"

		package = frappe.db.get_value("Car Category", category, tier_field)
		daily_rate = flt(package) if package else 0
		self.mainly_cost = round(real_days * daily_rate)

	def compute_totals(self) -> None:
		"""Authoritative invoice totals (mirrors the client script).

		Tax base is the rental only (base cost + extra distance) — the damage
		compensation is added afterwards, untaxed.
			ضريبة الإنفاق = الإيجار × نسبة الإنفاق
			ضريبة المحلية = ضريبة الإنفاق × نسبة المحلية
			الإجمالي النهائي = الإيجار + الأضرار + ضريبة الإنفاق + ضريبة المحلية
		"""
		rental = (self.mainly_cost or 0) + (self.extra_cost or 0)
		self.spending_tax, self.local_tax = compute_rental_tax(rental)
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

		from gatecar.accrual import create_closing_entry
		create_closing_entry(self.name)

	def on_cancel(self) -> None:
		from gatecar.accrual import reverse_closing_entry
		reverse_closing_entry(self.name)

		# The settlement's Car Accrual Entry keeps pointing at this receipt even
		# after cancellation — that back-reference is the audit trail, not a
		# dangling link, so skip Frappe's generic back-link check for it.
		self.flags.ignore_links = True

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
