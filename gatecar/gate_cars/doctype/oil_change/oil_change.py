import frappe
from frappe import _
from frappe.model.document import Document

OIL_CHANGE_INTERVAL = 5000


class OilChange(Document):
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		car: DF.Link
		cost: DF.Currency
		odometer_at_alert: DF.Int
		oil_name: DF.Data | None
		التاريخ: DF.Date | None
		الفاتورة: DF.Attach | None

	_DOCTYPE_NAME = "Oil Change"

	def validate(self) -> None:
		if self.docstatus == 1:
			if not self.التاريخ:
				frappe.throw(_("يجب إدخال تاريخ التغيير قبل التقديم"))
			if not self.oil_name:
				frappe.throw(_("يجب إدخال اسم الزيت قبل التقديم"))

	def on_submit(self) -> None:
		car = frappe.get_doc("Car", self.car)
		car.next_oil_change = car.current_odometer + OIL_CHANGE_INTERVAL
		car.save(ignore_permissions=True)
