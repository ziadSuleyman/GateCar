# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CarStatistics(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		active_bookings: DF.Int
		availability_rate: DF.Percent
		available_cars: DF.Int
		bookings_this_month: DF.Int
		bookings_today: DF.Int
		branch: DF.Link | None
		frozen_cars: DF.Int
		last_updated: DF.Datetime | None
		maintenance_cars: DF.Int
		overdue_returns: DF.Int
		ready_cars: DF.Int
		rented_cars: DF.Int
		reserved_cars: DF.Int
		revenue_this_month: DF.Currency
		revenue_today: DF.Currency
		total_cars: DF.Int
		utilization_rate: DF.Percent
	# end: auto-generated types

	_DOCTYPE_NAME = "Car Statistics"
