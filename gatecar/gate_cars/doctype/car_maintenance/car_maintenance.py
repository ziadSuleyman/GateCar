# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

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
		التاريخ: DF.Date
		الفاتورة: DF.Attach | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Maintenance"
