# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Owners(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		full_name: DF.Data
		identity_card_image: DF.AttachImage | None
		phone: DF.Phone
	# end: auto-generated types

	_DOCTYPE_NAME = "Owners"
