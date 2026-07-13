import frappe
from frappe import _
from frappe.utils import get_first_day, get_last_day


def execute(filters: dict | None = None) -> tuple:
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	return columns, data, None, chart


def get_columns() -> list[dict]:
	return [
		{
			"fieldname": "car",
			"label": _("السيارة"),
			"fieldtype": "Link",
			"options": "Car",
			"width": 100,
		},
		{
			"fieldname": "brand",
			"label": _("الماركة"),
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"fieldname": "plate_no",
			"label": _("رقم اللوحة"),
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"fieldname": "owner_name",
			"label": _("المالك"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "total_revenue",
			"label": _("الإيرادات"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "gate_car_share",
			"label": _("حصة Gate Car"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "owner_gross_share",
			"label": _("حصة المالك"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "taxes",
			"label": _("الضرائب"),
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"fieldname": "total_costs",
			"label": _("التكاليف"),
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"fieldname": "owner_net",
			"label": _("صافي المالك"),
			"fieldtype": "Currency",
			"width": 120,
		},
	]


def get_data(filters: dict) -> list[dict]:
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	gate_percent = float(filters.get("gate_car_percent") or 20)
	owner_percent = 100 - gate_percent

	car_filters = {}
	if filters.get("car"):
		car_filters["name"] = filters["car"]
	if filters.get("owner"):
		car_filters["owner_car"] = filters["owner"]

	cars = frappe.get_all(
		"Car",
		filters=car_filters,
		fields=["name", "brand", "model", "plate_no", "owner_car"],
	)

	# استحقاقي من Car Accrual Entry — نفس مصدر Car Activity Report، وليس الكاش
	# الفعلي من Revenue. راجع gatecar/accrual.py لمنطق التوليد الكامل.
	period_start = get_first_day(from_date)
	period_end = get_last_day(to_date)

	data = []
	for car in cars:
		owner_name = ""
		if car.owner_car:
			owner_name = frappe.db.get_value("Owners", car.owner_car, "full_name") or ""

		total_revenue = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(total_amount), 0)
			FROM `tabCar Accrual Entry`
			WHERE car = %s AND docstatus = 1 AND period BETWEEN %s AND %s
			""",
			(car.name, period_start, period_end),
		)[0][0] or 0

		oil_cost = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(cost), 0)
			FROM `tabPeriodic Maintenance`
			WHERE car = %s AND `التاريخ` BETWEEN %s AND %s AND docstatus = 1
			""",
			(car.name, period_start, period_end),
		)[0][0] or 0

		expense_cost = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(`التكلفة`), 0)
			FROM `tabCar Expense`
			WHERE car = %s AND `التاريخ` BETWEEN %s AND %s AND docstatus = 1
			""",
			(car.name, period_start, period_end),
		)[0][0] or 0

		# نفس صفوف Car Accrual Entry المستخدَمة أعلاه في total_revenue — الضريبة
		# مضمّنة فيها أصلاً، تُستخرَج هنا فقط لعرضها في عمودها المخصص.
		taxes = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(COALESCE(spending_tax, 0) + COALESCE(local_tax, 0)), 0)
			FROM `tabCar Accrual Entry`
			WHERE car = %s AND docstatus = 1 AND period BETWEEN %s AND %s
			""",
			(car.name, period_start, period_end),
		)[0][0] or 0

		# التكاليف = صيانة + مصاريف فقط (الضرائب لها عمودها المخصص)
		total_costs = oil_cost + expense_cost
		# الضريبة تُزال من القِدر أولاً، ثم تُقسَّم الحصص على الباقي — فلا الشركة
		# ولا المالك يأخذ نسبته من قيمة الضريبة (مطابقة لقاعدة لوحة التحكم).
		revenue_ex_tax = total_revenue - taxes
		gate_car_share = revenue_ex_tax * gate_percent / 100
		owner_gross_share = revenue_ex_tax * owner_percent / 100
		owner_net = owner_gross_share - total_costs

		if total_revenue or total_costs:
			data.append({
				"car": car.name,
				"brand": f"{car.brand} {car.model}",
				"plate_no": str(car.plate_no),
				"owner_name": owner_name,
				"total_revenue": total_revenue,
				"gate_car_share": gate_car_share,
				"owner_gross_share": owner_gross_share,
				"taxes": taxes,
				"total_costs": total_costs,
				"owner_net": owner_net,
			})

	data.sort(key=lambda x: x["total_revenue"], reverse=True)
	return data


def get_chart(data: list[dict]) -> dict | None:
	if not data:
		return None

	labels = [d["car"] for d in data[:10]]
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("حصة Gate Car"),
					"values": [d["gate_car_share"] for d in data[:10]],
				},
				{
					"name": _("صافي المالك"),
					"values": [d["owner_net"] for d in data[:10]],
				},
			],
		},
		"type": "bar",
		"colors": ["#4caf50", "#2196f3"],
	}
