# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from gatecar.maintenance_status import guard_not_under_maintenance
from gatecar.utils import compute_rental_tax


class CarBooking(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		address_fetched: DF.Data | None
		amended_from: DF.Link | None
		booking_id: DF.Data | None
		brand_fetched: DF.Data | None
		car: DF.Link | None
		category_car: DF.Link
		chassis_no_fetched: DF.Data | None
		chosen_address: DF.Data | None
		cost: DF.Int
		current_odometer_fetched: DF.Int
		customer: DF.Link
		customer_name_fetched: DF.Data | None
		date: DF.Date
		dob_fetched: DF.Data | None
		duration_days: DF.Int
		end_date: DF.Date
		grand_total: DF.Currency
		international_phone: DF.Data | None
		local_tax: DF.Currency
		license_expiry_date_fetched: DF.Date | None
		license_issue_date_fetched: DF.Date | None
		license_issue_place_fetched: DF.Data | None
		license_no_fetched: DF.Data | None
		model_fetched: DF.Data | None
		mother_name_fetched: DF.Data | None
		national_id_fetched: DF.Data | None
		nationality_fetched: DF.Data | None
		passport_no_fetched: DF.Data | None
		phone_fetched: DF.Data | None
		plate_no_fetched: DF.Data | None
		rate_per_day: DF.Currency
		sales_employee: DF.Link | None
		sales_employee_name: DF.Data | None
		spending_tax: DF.Currency
		start_date: DF.Date
		text_viwt: DF.TextEditor | None
		year_fetched: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Booking"

	def before_insert(self) -> None:
		if not self.sales_employee:
			self.sales_employee = frappe.db.get_value(
				"Employee", {"user_id": frappe.session.user}, "name"
			)

	def before_save(self) -> None:
		if self.car and self.docstatus == 0:
			# Block reserving a car that is currently under maintenance.
			guard_not_under_maintenance(self.car)
			self.set_car_status("محجوز")

	def validate(self) -> None:
		self.compute_taxes()
		if self.docstatus == 1:
			if not self.car:
				frappe.throw("يجب اختيار السيارة قبل اعتماد العقد")
			# Re-check on submit in case a maintenance opened after the draft was saved.
			guard_not_under_maintenance(self.car)
			if not self.customer:
				frappe.throw("يجب اختيار العميل قبل اعتماد العقد")
			if not self.start_date or not self.end_date:
				frappe.throw("يجب تحديد تاريخ بدء وانتهاء الإيجار قبل اعتماد العقد")

	def compute_taxes(self) -> None:
		"""Contract taxes for print (mirrors Car Receipt, same settings/rates).

		Tax base is the rental only (cost = daily rate × days):
			ضريبة الإنفاق = الإيجار × نسبة الإنفاق
			ضريبة المحلية = ضريبة الإنفاق × نسبة المحلية
			الإجمالي شامل الضرائب = الإيجار + ضريبة الإنفاق + ضريبة المحلية

		NOTE: display-only for the contract. Financial reports/dashboards keep
		sourcing taxes from Car Receipt to avoid double-counting.
		"""
		rental = self.cost or 0
		self.spending_tax, self.local_tax = compute_rental_tax(rental)
		self.grand_total = round(rental + self.spending_tax + self.local_tax, 2)

	def on_submit(self) -> None:
		if self.car:
			self.set_car_status("مؤجر")
		self.update_revenue_from_booking()

		from gatecar.accrual import ensure_accrual_entries
		ensure_accrual_entries(self.name)

	def on_cancel(self) -> None:
		if self.car:
			self.set_car_status("متوفر")

		from gatecar.accrual import reverse_booking_entries
		reverse_booking_entries(self.name)

		# Its accrual entries keep pointing at this booking even after
		# cancellation — that back-reference is the audit trail, not a
		# dangling link, so skip Frappe's generic back-link check for it.
		self.flags.ignore_links = True

	def update_revenue_from_booking(self) -> None:
		revenues = frappe.get_all(
			"Revenue",
			filters={"booking_reference": self.name},
			pluck="name",
		)
		if not revenues:
			return

		updates = {}
		if self.car:
			updates["car"] = self.car
		if self.customer_name_fetched:
			updates["customer_name"] = self.customer_name_fetched
		if self.sales_employee:
			updates["receiver"] = self.sales_employee

		if updates:
			for rev_name in revenues:
				for field, value in updates.items():
					frappe.db.set_value("Revenue", rev_name, field, value)
			frappe.msgprint(
				f"تم تحديث {len(revenues)} قيد مالي ببيانات العقد",
				indicator="green",
				alert=True,
			)

	def set_car_status(self, status: str) -> None:
		frappe.db.set_value("Car", self.car, "status", status)
		frappe.msgprint(
			f"تم تغيير حالة السيارة {self.car} إلى [{status}]",
			indicator="green" if status == "متوفر" else "orange" if status == "محجوز" else "blue",
			alert=True,
		)


@frappe.whitelist()
def make_car_receipt(source_name: str, target_doc=None) -> Document:
	from frappe.model.mapper import get_mapped_doc

	return get_mapped_doc(
		"Car Booking",
		source_name,
		{
			"Car Booking": {
				"doctype": "Car Receipt",
				"field_map": {
					"name": "booking",
					"car": "car",
					"start_date": "pickup_date",
					"duration_days": "duration_days",
					"customer_name_fetched": "customer_name",
					"down_payment": "down_payment",
					"sales_employee": "sales_employee",
					"cost": "mainly_cost",
				},
			},
		},
		target_doc,
	)
