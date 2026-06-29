# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CarBooking(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		booking_id: DF.Data | None
		brand_fetched: DF.Data | None
		car: DF.Link | None
		category_car: DF.Link
		cost: DF.Int
		current_odometer_fetched: DF.Int
		customer: DF.Link
		customer_name_fetched: DF.Data | None
		date: DF.Date
		down_payment: DF.Data | None
		duration_days: DF.Int
		end_date: DF.Date
		international_phone: DF.Data | None
		model_fetched: DF.Data | None
		phone_fetched: DF.Data | None
		plate_no_fetched: DF.Int
		rate_per_day: DF.Currency
		sales_employee: DF.Link | None
		sales_employee_name: DF.Data | None
		start_date: DF.Date
		status_fetched: DF.Literal["\u0645\u062a\u0648\u0641\u0631", "\u0645\u062d\u062c\u0648\u0632", "\u0645\u0624\u062c\u0631", "\u062f\u0627\u062e\u0644\u0627\u0644\u0635\u064a\u0627\u0646\u0629", "\u062c\u0627\u0647\u0632 \u0644\u0644\u062a\u0623\u062c\u064a\u0631", "\u0645\u062c\u0645\u062f\u0629"]
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Booking"

	def before_insert(self) -> None:
		if not self.sales_employee:
			self.sales_employee = frappe.db.get_value(
				"Employee", {"user_id": frappe.session.user}, "name"
			)

	def before_save(self) -> None:
		if self.car and self.docstatus == 0:
			self.set_car_status("محجوز")

	def validate(self) -> None:
		if self.docstatus == 1:
			if not self.car:
				frappe.throw("يجب اختيار السيارة قبل اعتماد العقد")
			if not self.customer:
				frappe.throw("يجب اختيار العميل قبل اعتماد العقد")
			if not self.start_date or not self.end_date:
				frappe.throw("يجب تحديد تاريخ بدء وانتهاء الإيجار قبل اعتماد العقد")

	def on_submit(self) -> None:
		if self.car:
			self.set_car_status("مؤجر")
		self.update_revenue_from_booking()

	def on_cancel(self) -> None:
		if self.car:
			self.set_car_status("متوفر")

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
