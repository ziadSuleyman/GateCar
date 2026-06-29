# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class VehicleFleet(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		branch: DF.Link
		fleet_manager: DF.Link
		fleet_name: DF.Data
		عدد_سيارات_الاسطول: DF.Data
	# end: auto-generated types

	_DOCTYPE_NAME = "Vehicle Fleet"
