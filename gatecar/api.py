import os
from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import (
	add_days,
	format_date,
	flt,
	getdate,
	get_first_day,
	get_last_day,
	now_datetime,
)


@frappe.whitelist()
def get_share_url(
	doctype: str,
	name: str,
	print_format: str,
	no_letterhead: int = 0,
	valid_days: int = 30,
) -> str:
	"""Return a PUBLIC (no-login) PDF link for ANY document + print format.

	Uses Frappe's native Document Share Key: only THIS document becomes viewable
	via an unguessable key — nothing else is exposed. Anyone with the link can open
	the PDF without a session (download_pdf is allow_guest and honours the key).
	The link expires after `valid_days` so a leaked or forwarded link does not stay valid forever.

	Works for the contract, receipt invoice, inspection checklists, financial
	receipts, etc. — the caller passes the target doctype/name/print_format.
	"""
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")  # the employee generating the link must have access
	expires_on = add_days(now_datetime(), valid_days)
	key = doc.get_document_share_key(expires_on=expires_on)

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
	name: str,
	print_format: str = "عقد إيجار سيارة",
	no_letterhead: int = 0,
	valid_days: int = 30,
) -> str:
	"""Backward-compatible wrapper: PUBLIC PDF link for a Car Booking contract."""
	return get_share_url("Car Booking", name, print_format, no_letterhead, valid_days)


@frappe.whitelist()
def get_price_tier_rate(category: str, days: int) -> float:
	"""Daily rate for a Car Category's price tier that covers `days`.

	Thin wrapper around gatecar.utils.get_tier_rate — the Car Booking form
	(find_price Client Script) calls this instead of querying the "Car
	Category Price Tier" child table directly: child tables aren't meant to
	be listed standalone, and doing so trips Frappe's field-permission check
	even on the built-in `parent` column (no amount of read/select
	permission on the child doctype satisfies it). Routing through one
	server-side function also keeps the tier-matching rule in a single place
	instead of a second, driftable copy in JS.
	"""
	from gatecar.utils import get_tier_rate

	return get_tier_rate(category, int(days))


ARABIC_ORDINALS = {
	1: "الأول", 2: "الثاني", 3: "الثالث", 4: "الرابع",
	5: "الخامس", 6: "السادس", 7: "السابع", 8: "الثامن",
	9: "التاسع", 10: "العاشر", 11: "الحادي عشر", 12: "الثاني عشر",
}


@frappe.whitelist()
def get_car_activity_html(car: str, from_date: str, to_date: str) -> str:
	car_doc = frappe.get_doc("Car", car)
	car_doc.check_permission("read")

	owner_name = ""
	if car_doc.owner_car:
		owner_name = frappe.db.get_value("Owners", car_doc.owner_car, "full_name") or car_doc.owner_car

	fd = getdate(from_date)
	date_label = "الشهر " + ARABIC_ORDINALS.get(fd.month, str(fd.month)) + " " + str(fd.year)

	car_image = getattr(car_doc, "صورة_السيارة", None) or ""

	# استحقاقي من Car Accrual Entry — نفس مصدر car_activity_report.py، وليس
	# الكاش الفعلي من Revenue. راجع gatecar/accrual.py لمنطق التوليد الكامل.
	period_start = get_first_day(from_date)
	period_end = get_last_day(to_date)

	bookings = frappe.db.sql("""
		SELECT
			cb.name,
			cb.customer_name_fetched AS customer_name,
			cb.start_date,
			cb.end_date,
			cb.rate_per_day,
			SUM(ae.days) AS duration_days,
			SUM(ae.total_amount) AS total_cost
		FROM `tabCar Booking` cb
		JOIN `tabCar Accrual Entry` ae
			ON ae.booking = cb.name AND ae.docstatus = 1
			AND ae.period BETWEEN %(period_start)s AND %(period_end)s
		WHERE cb.car = %(car)s
		  AND cb.docstatus = 1
		GROUP BY cb.name
		ORDER BY cb.start_date
	""", {"car": car, "period_start": period_start, "period_end": period_end}, as_dict=True)

	maintenance_rows = []

	for m in frappe.db.sql("""
		SELECT `التاريخ` AS date, oil_name AS description, cost, odometer_at_alert AS odometer
		FROM `tabPeriodic Maintenance`
		WHERE car = %(car)s AND docstatus = 1
		  AND `التاريخ` BETWEEN %(period_start)s AND %(period_end)s
		ORDER BY `التاريخ`
	""", {"car": car, "period_start": period_start, "period_end": period_end}, as_dict=True):
		maintenance_rows.append({
			"type": "صيانة دورية", "date": m.date,
			"odometer": m.odometer or "", "desc": m.description or "", "cost": flt(m.cost),
		})

	for m in frappe.db.sql("""
		SELECT `التاريخ` AS date, `التوصيف` AS description, `التكلفة` AS cost, 0 AS odometer
		FROM `tabCar Expense`
		WHERE car = %(car)s AND docstatus = 1
		  AND `التاريخ` BETWEEN %(period_start)s AND %(period_end)s
		ORDER BY `التاريخ`
	""", {"car": car, "period_start": period_start, "period_end": period_end}, as_dict=True):
		maintenance_rows.append({
			"type": "مصروف", "date": m.date,
			"odometer": "", "desc": m.description or "", "cost": flt(m.cost),
		})

	# Taxes from the same Car Accrual Entry rows behind `bookings` above — keeps
	# them landing in whichever month they actually accrued/settled in.
	for m in frappe.db.sql("""
		SELECT ae.period AS date, (COALESCE(ae.spending_tax,0) + COALESCE(ae.local_tax,0)) AS cost
		FROM `tabCar Accrual Entry` ae
		WHERE ae.car = %(car)s AND ae.docstatus = 1
		  AND ae.period BETWEEN %(period_start)s AND %(period_end)s
		  AND (COALESCE(ae.spending_tax,0) + COALESCE(ae.local_tax,0)) != 0
		ORDER BY ae.period
	""", {"car": car, "period_start": period_start, "period_end": period_end}, as_dict=True):
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


@frappe.whitelist()
def export_monthly_accrual_csv(period: str) -> None:
	"""CSV export of every Car Accrual Entry for one calendar month across all
	cars — the file handed manually to the external accounting system each
	month. `period` is any date within the target month.
	"""
	import csv
	import io

	period_start = get_first_day(period)
	period_end = get_last_day(period)

	rows = frappe.db.sql(
		"""
		SELECT
			ae.car, c.plate_no, c.brand, c.model, o.full_name AS owner_name,
			ae.booking, ae.period, ae.entry_type, ae.days,
			ae.base_amount, ae.spending_tax, ae.local_tax, ae.total_amount,
			ae.source_car_receipt
		FROM `tabCar Accrual Entry` ae
		LEFT JOIN `tabCar` c ON c.name = ae.car
		LEFT JOIN `tabOwners` o ON o.name = c.owner_car
		WHERE ae.docstatus = 1 AND ae.period BETWEEN %(period_start)s AND %(period_end)s
		ORDER BY ae.car, ae.booking, ae.creation
		""",
		{"period_start": period_start, "period_end": period_end},
		as_dict=True,
	)

	buf = io.StringIO()
	writer = csv.writer(buf)
	writer.writerow([
		"السيارة", "رقم اللوحة", "الماركة", "الموديل", "المالك",
		"العقد", "الشهر", "نوع القيد", "الأيام",
		"الإيجار قبل الضريبة", "ضريبة الإنفاق", "ضريبة المحلية", "الإجمالي",
		"الفاتورة المصدر",
	])
	for r in rows:
		writer.writerow([
			r.car, r.plate_no, r.brand, r.model, r.owner_name or "",
			r.booking, r.period, r.entry_type, r.days,
			r.base_amount, r.spending_tax, r.local_tax, r.total_amount,
			r.source_car_receipt or "",
		])

	frappe.response["type"] = "download"
	frappe.response["filecontent"] = "﻿" + buf.getvalue()
	frappe.response["filename"] = f"car-accrual-{period_start}.csv"
