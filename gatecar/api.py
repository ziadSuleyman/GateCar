import os
from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import format_date, flt, getdate


@frappe.whitelist()
def get_share_url(
	doctype: str, name: str, print_format: str, no_letterhead: int = 0
) -> str:
	"""Return a PUBLIC (no-login) PDF link for ANY document + print format.

	Uses Frappe's native Document Share Key: only THIS document becomes viewable
	via an unguessable key — nothing else is exposed. Anyone with the link can open
	the PDF without a session (download_pdf is allow_guest and honours the key).

	Works for the contract, receipt invoice, inspection checklists, financial
	receipts, etc. — the caller passes the target doctype/name/print_format.
	"""
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")  # the employee generating the link must have access
	key = doc.get_document_share_key(no_expiry=True)

	return frappe.utils.get_url(
		"/api/method/frappe.utils.print_format.download_pdf"
		f"?doctype={quote(doctype)}"
		f"&name={quote(name)}"
		f"&format={quote(print_format)}"
		f"&no_letterhead={int(no_letterhead)}"
		f"&key={key}"
	)


@frappe.whitelist()
def get_booking_share_url(
	name: str, print_format: str = "عقد إيجار سيارة", no_letterhead: int = 0
) -> str:
	"""Backward-compatible wrapper: PUBLIC PDF link for a Car Booking contract."""
	return get_share_url("Car Booking", name, print_format, no_letterhead)


ARABIC_ORDINALS = {
	1: "الأول", 2: "الثاني", 3: "الثالث", 4: "الرابع",
	5: "الخامس", 6: "السادس", 7: "السابع", 8: "الثامن",
	9: "التاسع", 10: "العاشر", 11: "الحادي عشر", 12: "الثاني عشر",
}


@frappe.whitelist()
def get_car_activity_html(car: str, from_date: str, to_date: str) -> str:
	car_doc = frappe.get_doc("Car", car)

	owner_name = ""
	if car_doc.owner_car:
		owner_name = frappe.db.get_value("Owners", car_doc.owner_car, "full_name") or car_doc.owner_car

	fd = getdate(from_date)
	date_label = "الشهر " + ARABIC_ORDINALS.get(fd.month, str(fd.month)) + " " + str(fd.year)

	car_image = getattr(car_doc, "صورة_السيارة", None) or ""

	bookings = frappe.db.sql("""
		SELECT
			cb.name,
			cb.customer_name_fetched AS customer_name,
			cb.start_date,
			cb.end_date,
			cb.duration_days,
			cb.rate_per_day,
			COALESCE(SUM(
				CASE WHEN r.payment_type = 'قبض' THEN r.amount
				     WHEN r.payment_type = 'دفع' THEN -r.amount
				     ELSE 0 END
			), 0) AS total_cost
		FROM `tabCar Booking` cb
		LEFT JOIN `tabRevenue` r
			ON r.booking_reference = cb.name
		WHERE cb.car = %(car)s
		  AND cb.start_date BETWEEN %(from_date)s AND %(to_date)s
		  AND cb.docstatus = 1
		GROUP BY cb.name
		ORDER BY cb.start_date
	""", {"car": car, "from_date": from_date, "to_date": to_date}, as_dict=True)

	maintenance_rows = []

	for m in frappe.db.sql("""
		SELECT `التاريخ` AS date, oil_name AS description, cost, odometer_at_alert AS odometer
		FROM `tabPeriodic Maintenance`
		WHERE car = %(car)s AND docstatus = 1
		  AND `التاريخ` BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY `التاريخ`
	""", {"car": car, "from_date": from_date, "to_date": to_date}, as_dict=True):
		maintenance_rows.append({
			"type": "صيانة دورية", "date": m.date,
			"odometer": m.odometer or "", "desc": m.description or "", "cost": flt(m.cost),
		})

	for m in frappe.db.sql("""
		SELECT `التاريخ` AS date, `التوصيف` AS description, `التكلفة` AS cost, 0 AS odometer
		FROM `tabCar Expense`
		WHERE car = %(car)s AND docstatus = 1
		  AND `التاريخ` BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY `التاريخ`
	""", {"car": car, "from_date": from_date, "to_date": to_date}, as_dict=True):
		maintenance_rows.append({
			"type": "مصروف", "date": m.date,
			"odometer": "", "desc": m.description or "", "cost": flt(m.cost),
		})

	# Taxes from the Car Receipt invoices — matched to the rental start (pickup_date).
	for m in frappe.db.sql("""
		SELECT pickup_date AS date, (COALESCE(spending_tax,0) + COALESCE(local_tax,0)) AS cost
		FROM `tabCar Receipt`
		WHERE car = %(car)s AND docstatus = 1
		  AND pickup_date BETWEEN %(from_date)s AND %(to_date)s
		  AND (COALESCE(spending_tax,0) + COALESCE(local_tax,0)) > 0
		ORDER BY pickup_date
	""", {"car": car, "from_date": from_date, "to_date": to_date}, as_dict=True):
		maintenance_rows.append({
			"type": "ضريبة", "date": m.date,
			"odometer": "", "desc": "ضريبة إنفاق + محلية", "cost": flt(m.cost),
		})

	maintenance_rows.sort(key=lambda x: str(x["date"] or ""))

	total_rental = sum(flt(b.total_cost) for b in bookings)
	total_costs = sum(m["cost"] for m in maintenance_rows)
	total_taxes = sum(m["cost"] for m in maintenance_rows if m["type"] == "ضريبة")
	company_pct = 20.0
	# الشركة تأخذ نسبتها من الإيراد بعد طرح الضريبة (لا تأخذ من قيمة الضريبة) —
	# مطابقة للوحة التحكم وتقرير المالك.
	company_amount = (total_rental - total_taxes) * company_pct / 100
	owner_net = total_rental - company_amount - total_costs

	def money(val):
		v = flt(val)
		return "{:,.2f}".format(v)

	context = {
		"car": car_doc,
		"car_image": car_image,
		"owner_name": owner_name,
		"date_label": date_label,
		"bookings": bookings,
		"maintenance_rows": maintenance_rows,
		"total_rental": total_rental,
		"total_costs": total_costs,
		"company_pct": int(company_pct),
		"company_amount": company_amount,
		"owner_net": owner_net,
		"fmt_date": format_date,
		"money": money,
	}

	tpl_path = os.path.join(frappe.get_app_path("gatecar"), "templates", "print", "car_activity_print.html")
	with open(tpl_path) as f:
		template_str = f.read()

	return frappe.render_template(template_str, context)
