import frappe
from frappe.model.document import Document


class GateCarsSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		local_tax_rate: DF.Percent
		spending_tax_rate: DF.Percent
	# end: auto-generated types

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		spending_tax_rate: DF.Percent
		local_tax_rate: DF.Percent

	_DOCTYPE_NAME = "Gate Cars Settings"
