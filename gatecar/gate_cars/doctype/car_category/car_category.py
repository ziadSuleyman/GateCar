# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CarCategory(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.Data | None
		long_term: DF.Link | None
		med_term: DF.Link
		name_category: DF.Data | None
		small_term: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Category"
