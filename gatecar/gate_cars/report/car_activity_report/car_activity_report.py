import frappe
from frappe import _
from frappe.utils import fmt_money, format_date, flt, get_first_day, get_last_day


def execute(filters=None):
	filters = filters or {}
	car_name = filters.get("car")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	if not car_name:
		frappe.throw(_("يجب اختيار سيارة"))

	car = frappe.get_doc("Car", car_name)
	owner_name = ""
	owner_share = 80.0
	company_share = 20.0
	if car.owner_car:
		owner_name = frappe.db.get_value("Owners", car.owner_car, "full_name") or car.owner_car

	columns = get_columns()
	data = []

	# ── Section: car info header ──────────────────────────────────
	data.append(_section_header("معلومات السيارة"))
	data.append(_info_row("السيارة", f"{car.brand} {car.model}"))
	data.append(_info_row("سنة الصنع", getattr(car, "سنة_الصنع", "") or ""))
	data.append(_info_row("اللون", car.color or "—"))
	data.append(_info_row("رقم اللوحة", car.plate_no or ""))
	data.append(_info_row("رقم الشاسيه", car.chassis_no or ""))
	data.append(_info_row("المالك", owner_name))
	data.append(_info_row("التأمين الإلزامي", format_date(car.mandatory_insurance_date) if car.mandatory_insurance_date else "—"))
	data.append(_info_row("التأمين الشامل", format_date(getattr(car, "تاريخ_التأمين_الشامل", None)) if getattr(car, "تاريخ_التأمين_الشامل", None) else "—"))
	data.append(_spacer())

	# ── Section: bookings ─────────────────────────────────────────
	data.append(_section_header("سجل الحركة"))
	data.append(_table_header(["#", "المستأجر", "تاريخ التسليم", "تاريخ الاستلام", "الأيام", "القيمة اليومية", "المجموع", "ملاحظات"]))

	# القيمة المعروضة هنا استحقاقية (Accrual) من Car Accrual Entry — قيمة العقد
	# موزّعة على شهرها التقويمي، وليست الكاش الفعلي المُحصَّل (Revenue). أي حجز
	# لم يُغلق بعد يظهر بتقدير تناسبي حسب أيامه في هذا الشهر؛ شهر إغلاق العقد
	# (Car Receipt) يحمل كامل الفرق المتبقي (تأخير، مسافة زائدة، أضرار).
	period_start = get_first_day(from_date)
	period_end = get_last_day(to_date)

	bookings = frappe.db.sql("""
		SELECT
			cb.name,
			cb.customer_name_fetched AS customer_name,
			cb.start_date AS delivery_date,
			cb.end_date AS return_date,
			cb.rate_per_day,
			SUM(ae.days) AS accrued_days,
			SUM(ae.total_amount) AS total_cost
		FROM `tabCar Booking` cb
		JOIN `tabCar Accrual Entry` ae
			ON ae.booking = cb.name AND ae.docstatus = 1
			AND ae.period BETWEEN %(period_start)s AND %(period_end)s
		WHERE cb.car = %(car)s
		  AND cb.docstatus = 1
		GROUP BY cb.name
		ORDER BY cb.start_date
	""", {"car": car_name, "period_start": period_start, "period_end": period_end}, as_dict=True)

	total_rental = 0
	for i, b in enumerate(bookings, 1):
		total_rental += flt(b.total_cost)
		data.append({
			"section": str(i),
			"label": b.customer_name or "—",
			"date1": format_date(b.delivery_date),
			"date2": format_date(b.return_date),
			"qty": b.accrued_days or 0,
			"unit_cost": fmt_money(b.rate_per_day or 0),
			"amount": fmt_money(b.total_cost or 0),
			"notes": "",
			"indent": 1,
		})

	data.append(_total_row("إجمالي الإيرادات", total_rental))
	data.append(_spacer())

	# ── Section: maintenance ──────────────────────────────────────
	data.append(_section_header("سجل الصيانة والمدفوعات"))
	data.append(_table_header(["#", "النوع", "التاريخ", "الكيلومتراج", "التوصيف", "التكلفة", "", ""]))

	maintenance_rows = []

	# Periodic Maintenance — same expanded month range as the accrual sections
	# above (period_start/period_end), so every part of the report describes
	# the same calendar-month window instead of drifting apart.
	for m in frappe.db.sql("""
		SELECT name, `التاريخ` AS date, oil_name AS desc_text, cost, odometer_at_alert AS odometer
		FROM `tabPeriodic Maintenance`
		WHERE car = %(car)s AND docstatus = 1
		  AND `التاريخ` BETWEEN %(period_start)s AND %(period_end)s
		ORDER BY `التاريخ`
	""", {"car": car_name, "period_start": period_start, "period_end": period_end}, as_dict=True):
		maintenance_rows.append({"type": "صيانة دورية", "date": m.date, "odometer": m.odometer, "desc": m.desc_text, "cost": m.cost})

	# Car Expense
	for m in frappe.db.sql("""
		SELECT name, `التاريخ` AS date, `التوصيف` AS desc_text, `التكلفة` AS cost, 0 AS odometer
		FROM `tabCar Expense`
		WHERE car = %(car)s AND docstatus = 1
		  AND `التاريخ` BETWEEN %(period_start)s AND %(period_end)s
		ORDER BY `التاريخ`
	""", {"car": car_name, "period_start": period_start, "period_end": period_end}, as_dict=True):
		maintenance_rows.append({"type": "مصروف", "date": m.date, "odometer": m.odometer, "desc": m.desc_text, "cost": m.cost})

	# Taxes (spending + local) from the same Car Accrual Entry rows behind
	# total_rental above — so they land in whichever month they actually
	# accrued/settled in, and never double-count against the accrual figure.
	for m in frappe.db.sql("""
		SELECT ae.booking AS name, ae.period AS date,
		       (COALESCE(ae.spending_tax,0) + COALESCE(ae.local_tax,0)) AS cost
		FROM `tabCar Accrual Entry` ae
		WHERE ae.car = %(car)s AND ae.docstatus = 1
		  AND ae.period BETWEEN %(period_start)s AND %(period_end)s
		  AND (COALESCE(ae.spending_tax,0) + COALESCE(ae.local_tax,0)) != 0
		ORDER BY ae.period
	""", {"car": car_name, "period_start": period_start, "period_end": period_end}, as_dict=True):
		maintenance_rows.append({"type": "ضريبة", "date": m.date, "odometer": 0, "desc": "ضريبة إنفاق + محلية (استحقاق)", "cost": m.cost})

	# Sort all by date
	maintenance_rows.sort(key=lambda x: x["date"] or "")

	total_costs = 0
	for i, m in enumerate(maintenance_rows, 1):
		total_costs += flt(m["cost"])
		data.append({
			"section": str(i),
			"label": m["type"],
			"date1": format_date(m["date"]),
			"date2": str(m["odometer"] or "—"),
			"qty": None,
			"unit_cost": m["desc"] or "—",
			"amount": fmt_money(m["cost"] or 0),
			"notes": "",
			"indent": 1,
		})

	data.append(_total_row("إجمالي التكاليف", total_costs))
	data.append(_spacer())

	# ── Section: summary ─────────────────────────────────────────
	data.append(_section_header("الخلاصة"))
	total_taxes = sum(flt(m["cost"]) for m in maintenance_rows if m["type"] == "ضريبة")
	operating_costs = total_costs - total_taxes  # صيانة + مصاريف فقط
	# الضريبة تُزال من القِدر أولاً، ثم يقتسم الطرفان الباقي — فلا الشركة ولا المالك
	# يأخذ نسبته من قيمة الضريبة (مطابق للوحة التحكم وتقرير المالك).
	revenue_ex_tax = total_rental - total_taxes
	company_amount = revenue_ex_tax * (company_share / 100)
	owner_gross = revenue_ex_tax * (owner_share / 100)
	owner_net = owner_gross - operating_costs

	data.append(_summary_row("إجمالي الإيرادات", total_rental, "green"))
	data.append(_summary_row("إجمالي الضرائب", total_taxes, "orange"))
	data.append(_summary_row(f"حصة الشركة ({company_share:.0f}%) بعد الضريبة", company_amount, "blue"))
	data.append(_summary_row(f"حصة المالك ({owner_share:.0f}%) بعد الضريبة", owner_gross, "purple"))
	data.append(_summary_row("إجمالي التكاليف (بدون الضرائب)", operating_costs, "red"))
	data.append(_summary_row("صافي حصة المالك", owner_net, "green" if owner_net >= 0 else "red"))

	return columns, data


def get_columns():
	return [
		{"fieldname": "section",    "label": "#",           "fieldtype": "Data",     "width": 60},
		{"fieldname": "label",      "label": "البيان",      "fieldtype": "Data",     "width": 200},
		{"fieldname": "date1",      "label": "تاريخ 1",     "fieldtype": "Data",     "width": 120},
		{"fieldname": "date2",      "label": "تاريخ 2",     "fieldtype": "Data",     "width": 120},
		{"fieldname": "qty",        "label": "الأيام",      "fieldtype": "Int",      "width": 70},
		{"fieldname": "unit_cost",  "label": "القيمة / التوصيف", "fieldtype": "Data", "width": 160},
		{"fieldname": "amount",     "label": "المجموع",     "fieldtype": "Data",     "width": 120},
		{"fieldname": "notes",      "label": "ملاحظات",     "fieldtype": "Data",     "width": 180},
	]


# ── Helpers ───────────────────────────────────────────────────────

def _section_header(title):
	return {
		"section": "", "label": f"── {title} ──",
		"date1": "", "date2": "", "qty": None,
		"unit_cost": "", "amount": "", "notes": "",
		"_style": "font-weight:700; font-size:13px; color:#1b5e20;",
	}


def _table_header(cols):
	return {
		"section": cols[0], "label": cols[1],
		"date1": cols[2],   "date2": cols[3],
		"qty": None,        "unit_cost": cols[5],
		"amount": cols[6],  "notes": cols[7],
		"_style": "font-weight:600; background:#e8f5e9; color:#1b5e20;",
	}


def _info_row(label, value):
	return {
		"section": "", "label": label,
		"date1": str(value), "date2": "", "qty": None,
		"unit_cost": "", "amount": "", "notes": "",
	}


def _total_row(label, amount):
	return {
		"section": "", "label": label,
		"date1": "", "date2": "", "qty": None,
		"unit_cost": "", "amount": f"$ {fmt_money(amount)}",
		"notes": "",
		"_style": "font-weight:700; background:#f1f8e9;",
	}


def _summary_row(label, amount, color="black"):
	colors = {
		"green": "#2e7d32", "red": "#c62828",
		"blue": "#1565c0",  "purple": "#6a1b9a",
		"orange": "#e65100",
	}
	c = colors.get(color, "#333")
	return {
		"section": "", "label": label,
		"date1": "", "date2": "", "qty": None,
		"unit_cost": "", "amount": f"$ {fmt_money(amount)}",
		"notes": "",
		"_style": f"font-weight:700; color:{c};",
	}


def _spacer():
	return {
		"section": "", "label": "",
		"date1": "", "date2": "", "qty": None,
		"unit_cost": "", "amount": "", "notes": "",
	}
