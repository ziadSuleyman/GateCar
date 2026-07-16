# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CarCategory(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.Data | None
		name_category: DF.Data | None
		price_tiers: DF.Table[CarCategoryPriceTier]
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Category"

	def validate(self) -> None:
		self.validate_price_tiers()

	def validate_price_tiers(self) -> None:
		"""Tiers must cover 1..N days with no gap and no overlap. Only the last
		tier (by from_day) may be open-ended (blank to_day = "and above").
		"""
		if not self.price_tiers:
			return

		tiers = sorted(self.price_tiers, key=lambda t: t.from_day or 0)

		for i, tier in enumerate(tiers):
			is_last = i == len(tiers) - 1

			if not is_last and not tier.to_day:
				frappe.throw(
					_("الباقة '{0}' (من يوم {1}) يجب أن يكون لها حد أعلى — فقط الباقة الأخيرة يمكن أن تبقى مفتوحة.").format(
						tier.label or tier.from_day, tier.from_day
					)
				)

			if tier.to_day and tier.to_day < tier.from_day:
				frappe.throw(
					_("الباقة '{0}': اليوم الأعلى ({1}) لا يمكن أن يكون أقل من اليوم الأدنى ({2}).").format(
						tier.label or tier.from_day, tier.to_day, tier.from_day
					)
				)

			if i > 0:
				prev = tiers[i - 1]
				expected_start = (prev.to_day or 0) + 1
				if tier.from_day != expected_start:
					frappe.throw(
						_("فجوة أو تداخل بين الباقات: الباقة '{0}' تبدأ من يوم {1}، لكن الباقة السابقة تنتهي عند يوم {2} (يجب أن تبدأ من يوم {3}).").format(
							tier.label or tier.from_day, tier.from_day, prev.to_day, expected_start
						)
					)
