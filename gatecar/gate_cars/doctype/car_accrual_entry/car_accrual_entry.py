# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CarAccrualEntry(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		accrual_key: DF.Data | None
		amended_from: DF.Link | None
		base_amount: DF.Currency
		booking: DF.Link
		car: DF.Link
		days: DF.Int
		entry_type: DF.Literal["تقدير", "تسوية إغلاق", "عكسي"]
		local_tax: DF.Currency
		period: DF.Date
		reverses: DF.Link | None
		source_car_receipt: DF.Link | None
		spending_tax: DF.Currency
		total_amount: DF.Currency
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Accrual Entry"

	def validate(self) -> None:
		if self.entry_type == "عكسي" and self.reverses:
			self.accrual_key = f"reverses:{self.reverses}"
		else:
			self.accrual_key = f"{self.booking}|{self.period}|{self.entry_type}"

		expected_total = flt(self.base_amount) + flt(self.spending_tax) + flt(self.local_tax)
		if abs(flt(self.total_amount) - expected_total) > 0.01:
			frappe.throw(
				_("الإجمالي ({0}) لا يطابق مجموع الإيجار والضريبتين ({1})").format(
					self.total_amount, expected_total
				)
			)

	def on_cancel(self) -> None:
		frappe.throw(_("لا يمكن إلغاء قيد استحقاق مباشرة — يُنشأ قيد عكسي بدلاً من ذلك"))
