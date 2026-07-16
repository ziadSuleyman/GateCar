# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class CarInspection(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		ac_heating: DF.Literal["سليم", "متضرر", "غير متاح"]
		amended_from: DF.Link | None
		audio_system: DF.Literal["سليم", "متضرر", "غير متاح"]
		booking: DF.Link
		car: DF.Data | None
		car_jack: DF.Literal["سليم", "متضرر", "غير متاح"]
		car_sanitized: DF.Check
		charger_cable: DF.Literal["سليم", "متضرر", "غير متاح"]
		customer_name: DF.Data | None
		customer_signature: DF.Signature | None
		dashboard_check: DF.Literal["سليم", "متضرر", "غير متاح"]
		documents_present: DF.Check
		doors_locks: DF.Literal["سليم", "متضرر", "غير متاح"]
		electric_windows: DF.Literal["سليم", "متضرر", "غير متاح"]
		employee_signature: DF.Signature | None
		engine_oil: DF.Literal["سليم", "متضرر", "غير متاح"]
		engine_warning: DF.Literal["سليم", "متضرر", "غير متاح"]
		external_notes: DF.SmallText | None
		first_aid_kit: DF.Literal["سليم", "متضرر", "غير متاح"]
		floor_carpet: DF.Literal["سليم", "متضرر", "غير متاح"]
		front_bumper: DF.Literal["سليم", "متضرر", "غير متاح"]
		front_glass: DF.Literal["سليم", "متضرر", "غير متاح"]
		fuel_level: DF.Literal["فارغ", "1/4", "1/2", "3/4", "ممتلئ"]
		fuel_level_agreed: DF.Check
		fuel_type: DF.Literal["", "بنزين", "ديزل"]
		inspection_date: DF.Datetime
		inspection_type: DF.Literal["عند التسليم", "عند الاستلام"]
		interior_lighting: DF.Literal["سليم", "متضرر", "غير متاح"]
		internal_notes: DF.SmallText | None
		left_side: DF.Literal["سليم", "متضرر", "غير متاح"]
		license_plate_check: DF.Literal["سليم", "متضرر", "غير متاح"]
		lights: DF.Literal["سليم", "متضرر", "غير متاح"]
		mechanical_notes: DF.SmallText | None
		no_odors: DF.Literal["سليم", "متضرر", "غير متاح"]
		no_smoking: DF.Literal["سليم", "متضرر", "غير متاح"]
		odometer: DF.Int
		phone: DF.Data | None
		plate_no: DF.Data | None
		pre_existing_damage: DF.SmallText | None
		rear_bumper: DF.Literal["سليم", "متضرر", "غير متاح"]
		right_side: DF.Literal["سليم", "متضرر", "غير متاح"]
		roof: DF.Literal["سليم", "متضرر", "غير متاح"]
		safety_triangle: DF.Literal["سليم", "متضرر", "غير متاح"]
		seats: DF.Literal["سليم", "متضرر", "غير متاح"]
		signals: DF.Literal["سليم", "متضرر", "غير متاح"]
		spare_tire_tools: DF.Literal["سليم", "متضرر", "غير متاح"]
		tires: DF.Literal["سليم", "متضرر", "غير متاح"]
		water_bottles_present: DF.Check
		windows_mirrors: DF.Literal["سليم", "متضرر", "غير متاح"]
	# end: auto-generated types

	def before_insert(self) -> None:
		if not self.inspection_date:
			self.inspection_date = now_datetime()
		if self.booking:
			self._populate_from_booking()

	def _populate_from_booking(self) -> None:
		booking = frappe.get_doc("Car Booking", self.booking)
		self.customer_name = booking.customer_name_fetched or ""
		self.car = booking.car or ""
		self.plate_no = booking.plate_no_fetched or ""
		if not self.odometer and booking.car:
			self.odometer = frappe.db.get_value("Car", booking.car, "current_odometer") or 0
