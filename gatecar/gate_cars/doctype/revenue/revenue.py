# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Revenue(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		booking_reference: DF.Link
		car: DF.Data | None
		customer_name: DF.Data | None
		date: DF.Date
		notes: DF.Data | None
		payment_method: DF.Data | None
		receiver: DF.Link
		shift: DF.Link | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Revenue"
