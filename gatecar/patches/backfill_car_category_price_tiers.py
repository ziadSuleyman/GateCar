"""One-time backfill: convert every Car Category's old fixed small_term/
med_term/long_term Links (each just a Link whose target document name is the
daily rate — e.g. a "Price Package" named "20") into three rows in the new
price_tiers child table, preserving the exact same day ranges and rates the
app already enforced (1-7 / 8-20 / 21+):

    small_term -> 1..7
    med_term   -> 8..20
    long_term  -> 21..(open-ended), only if set (it was never required)

Runs before the old fields are removed from car_category.json, so the source
values are still readable. Idempotent — skips any category that already has
price_tiers rows (e.g. a re-run, or a category created after the migration).
"""

import frappe
from frappe.utils import flt


def execute():
	if not frappe.db.table_exists("Car Category") or not frappe.db.table_exists("Car Category Price Tier"):
		return

	categories = frappe.get_all(
		"Car Category", fields=["name", "small_term", "med_term", "long_term"]
	)

	for cat in categories:
		if frappe.db.exists("Car Category Price Tier", {"parent": cat.name}):
			continue  # already migrated

		doc = frappe.get_doc("Car Category", cat.name)
		rows = []

		if cat.small_term:
			rows.append({"label": "الباقة الصغرى", "from_day": 1, "to_day": 7, "rate_per_day": flt(cat.small_term)})
		if cat.med_term:
			rows.append({"label": "الباقة الوسطى", "from_day": 8, "to_day": 20, "rate_per_day": flt(cat.med_term)})
		if cat.long_term:
			rows.append({"label": "الباقة الكبرى", "from_day": 21, "to_day": None, "rate_per_day": flt(cat.long_term)})

		if not rows:
			continue

		doc.set("price_tiers", [])
		for row in rows:
			doc.append("price_tiers", row)
		doc.save(ignore_permissions=True)

	frappe.db.commit()
