# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CarMaintenance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		car: DF.Link
		cost: DF.Currency
		reason: DF.Data
		revenue_entry: DF.Link | None
		التاريخ: DF.Date
		الفاتورة: DF.Attach | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Maintenance"

	def on_submit(self):
		if self.cost and not self.revenue_entry:
			rev = frappe.new_doc("Revenue")
			rev.date = self.التاريخ
			rev.car = self.car
			rev.amount = self.cost
			rev.notes = f"صيانة: {self.reason or ''} — {self.name}"
			rev.insert(ignore_permissions=True)
			self.db_set("revenue_entry", rev.name, notify=True)

	def on_cancel(self):
		if self.revenue_entry and frappe.db.exists("Revenue", self.revenue_entry):
			frappe.delete_doc("Revenue", self.revenue_entry, ignore_permissions=True)
			self.db_set("revenue_entry", None, notify=True)
