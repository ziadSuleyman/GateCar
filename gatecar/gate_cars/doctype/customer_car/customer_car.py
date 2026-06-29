# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CustomerCar(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		customer_name: DF.Data
		emergency_number: DF.Phone | None
		international_phone: DF.Phone | None
		nationality: DF.Data | None
		phone: DF.Phone | None
		صورة_الهوية_او_جواز_السفر: DF.Attach | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Customer Car"
