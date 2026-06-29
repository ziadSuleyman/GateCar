# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Price_pacage_monthly(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		تكلفة_الاجار_الشهري: DF.Int
	# end: auto-generated types

	_DOCTYPE_NAME = "Price_pacage_monthly"
