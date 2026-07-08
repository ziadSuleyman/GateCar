import frappe
from frappe import _
from frappe.model.document import Document

from gatecar.maintenance_status import (
	DATE_EXPENSE_TYPES,
	DATE_FIELD_BY_TYPE,
	release_car,
	set_car_under_maintenance,
)


class CarExpense(Document):
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		car: DF.Link
		expense_type: DF.Literal["عام", "تأمين إلزامي", "تأمين شامل", "تسجيل"]
		new_due_date: DF.Date | None
		التاريخ: DF.Date
		التوصيف: DF.Data | None
		التكلفة: DF.Currency
		الفاتورة: DF.Attach | None

	_DOCTYPE_NAME = "Car Expense"

	def _is_date_type(self) -> bool:
		"""Insurance/registration renewals lock the car; a plain (عام) expense does not."""
		return self.expense_type in DATE_EXPENSE_TYPES

	def validate(self) -> None:
		# Invoice is mandatory to approve any expense.
		if self.docstatus == 1:
			if not self.الفاتورة:
				frappe.throw(_("يجب إرفاق الفاتورة قبل اعتماد المصروف"))
			if self._is_date_type() and not self.new_due_date:
				frappe.throw(
					_("يجب إدخال تاريخ الانتهاء الجديد قبل اعتماد ({0})").format(self.expense_type)
				)

	def after_insert(self) -> None:
		# A date-renewal expense (expired insurance/registration) locks the car.
		if self._is_date_type() and not self.flags.get("skip_car_lock"):
			set_car_under_maintenance(self.car)

	def on_submit(self) -> None:
		if self._is_date_type():
			self._renew_car_due()
			release_car(self.car, exclude=self.name)

	def on_cancel(self) -> None:
		if self._is_date_type():
			release_car(self.car, exclude=self.name)

	def _renew_car_due(self) -> None:
		"""Push the matching expiry date on the Car forward once the renewal is approved."""
		field = DATE_FIELD_BY_TYPE.get(self.expense_type)
		if field and self.new_due_date:
			frappe.db.set_value("Car", self.car, field, self.new_due_date)
