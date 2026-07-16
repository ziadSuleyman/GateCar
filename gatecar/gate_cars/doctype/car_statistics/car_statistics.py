import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime


class CarStatistics(Document):
	_DOCTYPE_NAME = "Car Statistics"


@frappe.whitelist()
def get_statistics(branch=None):
	condition = "AND f.branch = %s" if branch else ""
	params = [branch] if branch else []
	rows = frappe.db.sql(
		f"""SELECT c.status, COUNT(*) AS count
		FROM `tabCar` c LEFT JOIN `tabVehicle Fleet` f ON f.name = c.fleet
		WHERE 1=1 {condition} GROUP BY c.status""",
		params,
		as_dict=True,
	)
	counts = {row.status: row.count for row in rows}
	today = getdate()
	month_start = today.replace(day=1)
	revenue = frappe.db.sql(
		"""SELECT
		COALESCE(SUM(CASE WHEN date = %s THEN CASE WHEN payment_type = 'دفع' THEN -amount ELSE amount END ELSE 0 END), 0) AS today_total,
		COALESCE(SUM(CASE WHEN date >= %s THEN CASE WHEN payment_type = 'دفع' THEN -amount ELSE amount END ELSE 0 END), 0) AS month_total
		FROM `tabRevenue`""",
		(today, month_start),
		as_dict=True,
	)[0]
	total = sum(counts.values())
	rented = counts.get("مؤجر", 0)
	return {
		"total_cars": total,
		"available_cars": counts.get("متوفر", 0),
		"ready_cars": counts.get("جاهز للتسليم", 0),
		"rented_cars": rented,
		"reserved_cars": counts.get("محجوز", 0),
		"maintenance_cars": counts.get("داخل الصيانة", 0),
		"frozen_cars": counts.get("مجمدة", 0),
		"utilization_rate": rented / total * 100 if total else 0,
		"availability_rate": counts.get("متوفر", 0) / total * 100 if total else 0,
		"active_bookings": frappe.db.count("Car Booking", {"docstatus": 1}),
		"overdue_returns": frappe.db.count("Car Booking", {"docstatus": 1, "end_date": ["<", today]}),
		"bookings_today": frappe.db.count("Car Booking", {"creation": [">=", today]}),
		"bookings_this_month": frappe.db.count("Car Booking", {"creation": [">=", month_start]}),
		"revenue_today": revenue.today_total or 0,
		"revenue_this_month": revenue.month_total or 0,
		"last_updated": now_datetime(),
	}
