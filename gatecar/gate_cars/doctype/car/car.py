# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Car(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		brand: DF.Data
		categorize: DF.Link
		chassis_no: DF.Data | None
		current_odometer: DF.Int
		custom_id: DF.Data | None
		finish_date: DF.Date | None
		fleet: DF.Link
		mandatory_insurance_date: DF.Date | None
		model: DF.Data
		next_oil_change: DF.Int
		owner_car: DF.Link | None
		plate_no: DF.Data
		status: DF.Literal["\u0645\u062a\u0648\u0641\u0631", "\u0645\u062d\u062c\u0648\u0632", "\u0645\u0624\u062c\u0631", "\u062f\u0627\u062e\u0644 \u0627\u0644\u0635\u064a\u0627\u0646\u0629", "\u062c\u0627\u0647\u0632 \u0644\u0644\u062a\u0633\u0644\u064a\u0645", "\u0645\u062c\u0645\u062f\u0629"]
		تاريخ_التأمين_الشامل: DF.Date | None
		سنة_الصنع: DF.Data | None
		صورة_السيارة: DF.Attach | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Car"

	def after_insert(self) -> None:
		if not self.custom_id:
			self.custom_id = self.name
			frappe.db.set_value("Car", self.name, "custom_id", self.name)
		self.update_fleet_and_branch_count(self.fleet)

	def on_update(self) -> None:
		old_doc = self.get_doc_before_save()
		if old_doc and old_doc.fleet != self.fleet:
			self.update_fleet_and_branch_count(old_doc.fleet)
		self.update_fleet_and_branch_count(self.fleet)

	def on_trash(self) -> None:
		self.update_fleet_and_branch_count(self.fleet)

	@staticmethod
	def update_fleet_and_branch_count(fleet_name: str) -> None:
		car_count = frappe.db.count("Car", {"fleet": fleet_name})
		fleet = frappe.get_doc("Vehicle Fleet", fleet_name)
		fleet.عدد_سيارات_الاسطول = car_count
		fleet.save(ignore_permissions=True)

		branch_name = fleet.branch
		branch_car_count = frappe.db.sql(
			"""
			SELECT COUNT(c.name)
			FROM `tabCar` c
			JOIN `tabVehicle Fleet` f ON c.fleet = f.name
			WHERE f.branch = %s
			""",
			branch_name,
		)[0][0]
		frappe.db.set_value("Car Branch", branch_name, "total_car", branch_car_count)
