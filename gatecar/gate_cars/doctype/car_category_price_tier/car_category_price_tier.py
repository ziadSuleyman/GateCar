# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CarCategoryPriceTier(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from_day: DF.Int
		label: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		rate_per_day: DF.Currency
		to_day: DF.Int
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Category Price Tier"
