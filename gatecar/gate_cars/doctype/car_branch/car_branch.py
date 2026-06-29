# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CarBranch(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		branch_manager: DF.Link
		branch_name: DF.Data
		city: DF.Link
		total_car: DF.Data
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Branch"
