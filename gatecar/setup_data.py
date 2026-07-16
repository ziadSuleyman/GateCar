import frappe
from frappe import _


def after_install():
	create_server_scripts()
	create_client_scripts()
	create_print_formats()
	set_branding()
	create_role_workspaces()
	frappe.db.commit()


def set_branding():
	logo = "/assets/gatecar/logo.png"
	frappe.db.set_value("Website Settings", "Website Settings", "favicon", logo)
	frappe.db.set_value("Navbar Settings", "Navbar Settings", "app_logo", logo)


ROLE_WORKSPACES = {
	"المبيعات": {
		"icon": "file",
		"role": "موظف مبيعات",
		"shortcuts": [
			("حجز جديد", "Car Booking", "DocType", "file"),
			("استلام سيارة", "Car Receipt", "DocType", "check"),
			("عميل جديد", "Customer Car", "DocType", "users"),
			("السيارات", "Car", "DocType", "tool"),
		],
		"cards": [
			("الحجوزات", [("Car Booking", "Car Booking", "DocType")]),
			("استلام السيارات", [("Car Receipt", "Car Receipt", "DocType")]),
			(
				"العملاء والسيارات",
				[
					("Customer Car", "Customer Car", "DocType"),
					("Car", "Car", "DocType"),
					("Car Category", "Car Category", "DocType"),
				],
			),
		],
		"sidebar_items": [
			("المبيعات", "المبيعات", "Workspace", "home"),
			("حجز جديد", "Car Booking", "DocType", "file"),
			("استلام سيارة", "Car Receipt", "DocType", "check"),
			("العملاء", "Customer Car", "DocType", "users"),
			("السيارات", "Car", "DocType", "tool"),
			("تصنيف السيارات", "Car Category", "DocType", None),
			("القيود المالية", "Revenue", "DocType", "accounting"),
		],
	},
	"الأسطول": {
		"icon": "tool",
		"role": "مشرف أسطول",
		"shortcuts": [
			("السيارات", "Car", "DocType", "tool"),
			("الأساطيل", "Vehicle Fleet", "DocType", None),
		],
		"cards": [
			("السيارات", [("Car", "Car", "DocType"), ("Car Category", "Car Category", "DocType")]),
			(
				"الأساطيل والفروع",
				[("Vehicle Fleet", "Vehicle Fleet", "DocType"), ("Car Branch", "Car Branch", "DocType")],
			),
		],
		"sidebar_items": [
			("الأسطول", "الأسطول", "Workspace", "home"),
			("السيارات", "Car", "DocType", "tool"),
			("تصنيف السيارات", "Car Category", "DocType", None),
			("الصيانة الدورية", "Periodic Maintenance", "DocType", None),
			("الأساطيل", "Vehicle Fleet", "DocType", None),
			("الفروع", "Car Branch", "DocType", None),
		],
	},
	"إدارة الفرع": {
		"icon": "building",
		"role": "مدير فرع",
		"shortcuts": [
			("لوحة تحكم الفرع", "branch-dashboard", "Page", "dashboard"),
			("الحجوزات", "Car Booking", "DocType", "file"),
			("الفروع", "Car Branch", "DocType", None),
			("الأساطيل", "Vehicle Fleet", "DocType", None),
		],
		"cards": [
			(
				"العمليات",
				[
					("Car Booking", "Car Booking", "DocType"),
					("Car Receipt", "Car Receipt", "DocType"),
					("Customer Car", "Customer Car", "DocType"),
				],
			),
			(
				"السيارات",
				[
					("Car", "Car", "DocType"),
					("Car Category", "Car Category", "DocType"),
				],
			),
			(
				"الهيكل التنظيمي",
				[
					("Car Branch", "Car Branch", "DocType"),
					("Vehicle Fleet", "Vehicle Fleet", "DocType"),
					("cities", "cities", "DocType"),
					("Employee", "Employee", "DocType"),
				],
			),
		],
		"sidebar_items": [
			("إدارة الفرع", "إدارة الفرع", "Workspace", "home"),
			("لوحة تحكم الفرع", "branch-dashboard", "Page", "dashboard"),
			("الحجوزات", "Car Booking", "DocType", "file"),
			("استلام السيارات", "Car Receipt", "DocType", "check"),
			("العملاء", "Customer Car", "DocType", "users"),
			("السيارات", "Car", "DocType", "tool"),
			("تصنيف السيارات", "Car Category", "DocType", None),
			("الفروع", "Car Branch", "DocType", None),
			("الأساطيل", "Vehicle Fleet", "DocType", None),
			("المدن", "cities", "DocType", None),
			("الموظفين", "Employee", "DocType", "users"),
		],
	},
}


def create_role_workspaces():
	for title, config in ROLE_WORKSPACES.items():
		if not frappe.db.exists("Workspace", title):
			create_workspace(title, config)
		if not frappe.db.exists("Workspace Sidebar", title):
			create_workspace_sidebar(title, config)
		if not frappe.db.exists("Desktop Icon", {"label": title}):
			create_workspace_icon(title)

	frappe.db.sql("DELETE FROM `tabDesktop Layout`")
	frappe.cache.delete_key("bootinfo")


def create_workspace(title, config):
	import json

	workspace = frappe.new_doc("Workspace")
	workspace.update({"title": title, "label": title, "public": 1, "icon": config["icon"]})
	workspace.content = json.dumps(build_workspace_content(config), ensure_ascii=False)
	workspace.append("custom_blocks", {"custom_block_name": "gate-car-banner", "label": "gate-car-banner"})
	append_workspace_links(workspace, config)
	workspace.insert(ignore_permissions=True)
	print(f"  Created Workspace: {title}")


def build_workspace_content(config):
	content = [{
		"id": "banner",
		"type": "custom_block",
		"data": {"custom_block_name": "gate-car-banner", "col": 12},
	}]
	for index, (label, *_rest) in enumerate(config["shortcuts"], 1):
		content.append({"id": f"sc{index}", "type": "shortcut", "data": {"shortcut_name": label, "col": 3}})
	spacer_id = len(config["shortcuts"]) + 1
	content.append({"id": f"sp{spacer_id}", "type": "spacer", "data": {"col": 12}})
	for index, (label, _links) in enumerate(config["cards"], spacer_id + 1):
		content.append({"id": f"c{index}", "type": "card", "data": {"card_name": label, "col": 4}})
	return content


def append_workspace_links(workspace, config):
	for label, link_to, link_type, icon in config["shortcuts"]:
		workspace.append("shortcuts", {
			"label": label, "link_to": link_to, "type": link_type, "color": "Green", "icon": icon,
		})
	for label, links in config["cards"]:
		workspace.append("links", {"label": label, "type": "Card Break", "link_type": "DocType"})
		for link_label, link_to, link_type in links:
			workspace.append("links", {
				"label": link_label, "link_to": link_to, "link_type": link_type, "type": "Link",
			})


def create_workspace_sidebar(title, config):
	sidebar = frappe.new_doc("Workspace Sidebar")
	sidebar.update({"title": title, "header_icon": config["icon"]})
	for label, link_to, link_type, icon in config["sidebar_items"]:
		sidebar.append("items", {
			"label": label, "link_to": link_to, "link_type": link_type, "type": "Link", "icon": icon,
		})
	sidebar.insert(ignore_permissions=True)
	frappe.db.set_value("Workspace Sidebar", sidebar.name, "for_user", None)
	print(f"  Created Workspace Sidebar: {title}")


def create_workspace_icon(title):
	icon = frappe.new_doc("Desktop Icon")
	icon.update({
		"label": title,
		"link_type": "Workspace Sidebar",
		"link_to": title,
		"standard": 1,
		"icon_type": "Link",
		"logo_url": "/assets/gatecar/logo.png",
	})
	icon.insert(ignore_permissions=True)
	print(f"  Created Desktop Icon: {title}")


def create_server_scripts():
	scripts = [
		{
			"name": "dashboard_stats",
			"api_method": "dashboard_stats",
			"script": """
total_cars = frappe.db.count("Car", {"status": ["!=", "مجمدة"]})
frozen_cars = frappe.db.count("Car", {"status": "مجمدة"})

statuses = frappe.db.sql("SELECT status, COUNT(*) as count FROM `tabCar` GROUP BY status", as_dict=True)
status_map = {s.status: s["count"] for s in statuses}

branches = frappe.db.sql(\"\"\"
    SELECT b.name as branch_name, b.city,
        COUNT(c.name) as car_count,
        SUM(CASE WHEN c.status = 'متوفر' THEN 1 ELSE 0 END) as available,
        SUM(CASE WHEN c.status = 'محجوز' THEN 1 ELSE 0 END) as reserved,
        SUM(CASE WHEN c.status = 'مؤجر' THEN 1 ELSE 0 END) as rented,
        SUM(CASE WHEN c.status = 'داخل الصيانة' THEN 1 ELSE 0 END) as in_maintenance,
        SUM(CASE WHEN c.status = 'جاهز للتسليم' THEN 1 ELSE 0 END) as ready,
        SUM(CASE WHEN c.status = 'مجمدة' THEN 1 ELSE 0 END) as frozen
    FROM `tabCar Branch` b
    LEFT JOIN `tabVehicle Fleet` f ON f.branch = b.name
    LEFT JOIN `tabCar` c ON c.fleet = f.name
    GROUP BY b.name
\"\"\", as_dict=True)

fleets = frappe.db.sql(\"\"\"
    SELECT f.name as fleet_name, f.branch,
        COUNT(c.name) as car_count,
        SUM(CASE WHEN c.status = 'متوفر' THEN 1 ELSE 0 END) as available,
        SUM(CASE WHEN c.status = 'مؤجر' THEN 1 ELSE 0 END) as rented
    FROM `tabVehicle Fleet` f
    LEFT JOIN `tabCar` c ON c.fleet = f.name
    GROUP BY f.name
\"\"\", as_dict=True)

frappe.response["message"] = {
    "total_cars": total_cars,
    "frozen_cars": frozen_cars,
    "status_map": status_map,
    "branches": branches,
    "fleets": fleets,
}
""",
		},
		{
			"name": "car_profitability",
			"api_method": "car_profitability",
			"script": """
month = frappe.form_dict.get("month")
year = frappe.form_dict.get("year")

date_filter_rev = ""
date_filter_oil = ""

if month and year:
    date_filter_rev = f"AND MONTH(r.date) = {int(month)} AND YEAR(r.date) = {int(year)}"
    date_filter_oil = f"AND MONTH(o.التاريخ) = {int(month)} AND YEAR(o.التاريخ) = {int(year)}"

cars = frappe.db.sql(f\"\"\"
    SELECT
        c.name, c.brand, c.model, c.plate_no, c.status,
        IFNULL(rev.total_revenue, 0) as total_revenue,
        IFNULL(oil.total_cost, 0) as total_oil_change,
        IFNULL(rev.total_revenue, 0) - IFNULL(oil.total_cost, 0) as net_profit
    FROM `tabCar` c
    LEFT JOIN (
        SELECT cb.car, SUM(r.amount) as total_revenue
        FROM `tabRevenue` r
        JOIN `tabCar Booking` cb ON r.booking_reference = cb.name
        WHERE 1=1 {date_filter_rev}
        GROUP BY cb.car
    ) rev ON rev.car = c.name
    LEFT JOIN (
        SELECT o.car, SUM(o.cost) as total_cost
        FROM `tabPeriodic Maintenance` o
        WHERE o.docstatus = 1 {date_filter_oil}
        GROUP BY o.car
    ) oil ON oil.car = c.name
    ORDER BY net_profit DESC
\"\"\", as_dict=True)

frappe.response["message"] = cars
""",
		},
		{
			"name": "profit_summary",
			"api_method": "profit_summary",
			"script": """
date_from = frappe.form_dict.get("date_from")
date_to = frappe.form_dict.get("date_to")

total_revenue = frappe.db.sql("SELECT IFNULL(SUM(amount),0) FROM `tabRevenue`")[0][0]
total_oil_change = frappe.db.sql("SELECT IFNULL(SUM(cost),0) FROM `tabPeriodic Maintenance` WHERE docstatus=1")[0][0]
total_profit = total_revenue - total_oil_change

period_profit = None
period_revenue = 0
period_oil_change = 0
if date_from and date_to:
    period_revenue = frappe.db.sql("SELECT IFNULL(SUM(amount),0) FROM `tabRevenue` WHERE date BETWEEN %s AND %s", (date_from, date_to))[0][0]
    period_oil_change = frappe.db.sql("SELECT IFNULL(SUM(cost),0) FROM `tabPeriodic Maintenance` WHERE docstatus=1 AND التاريخ BETWEEN %s AND %s", (date_from, date_to))[0][0]
    period_profit = period_revenue - period_oil_change

frappe.response["message"] = {
    "total_revenue": total_revenue,
    "total_oil_change": total_oil_change,
    "total_profit": total_profit,
    "period_revenue": period_revenue,
    "period_oil_change": period_oil_change,
    "period_profit": period_profit,
}
""",
		},
		{
			"name": "branch_dashboard_stats",
			"api_method": "branch_dashboard_stats",
			"script": """
user = frappe.session.user

user_branch = frappe.db.get_value("Car Branch", {"branch_manager": user}, "name")
if not user_branch and frappe.session.user == "Administrator":
    user_branch = frappe.db.get_value("Car Branch", {}, "name")

if not user_branch:
    frappe.response["message"] = {"error": "لا يوجد فرع مرتبط بحسابك", "branches": [], "fleets": [], "status_map": {}, "total_cars": 0, "frozen_cars": 0}
else:
    statuses = frappe.db.sql("SELECT c.status, COUNT(*) as count FROM `tabCar` c JOIN `tabVehicle Fleet` f ON c.fleet = f.name WHERE f.branch = %s GROUP BY c.status", user_branch, as_dict=True)
    status_map = {s.status: s["count"] for s in statuses}
    total_cars = sum(v for k, v in status_map.items() if k != "مجمدة")
    frozen_cars = status_map.get("مجمدة", 0)

    fleets = frappe.db.sql("SELECT f.name as fleet_name, f.branch, COUNT(c.name) as car_count, SUM(CASE WHEN c.status = 'متوفر' THEN 1 ELSE 0 END) as available, SUM(CASE WHEN c.status = 'مؤجر' THEN 1 ELSE 0 END) as rented FROM `tabVehicle Fleet` f LEFT JOIN `tabCar` c ON c.fleet = f.name WHERE f.branch = %s GROUP BY f.name", user_branch, as_dict=True)

    frappe.response["message"] = {
        "branch_name": user_branch,
        "total_cars": total_cars,
        "frozen_cars": frozen_cars,
        "status_map": status_map,
        "branches": [],
        "fleets": fleets,
    }
""",
		},
		{
			"name": "branch_car_profitability",
			"api_method": "branch_car_profitability",
			"script": """
user = frappe.session.user
user_branch = frappe.db.get_value("Car Branch", {"branch_manager": user}, "name")
if not user_branch and frappe.session.user == "Administrator":
    user_branch = frappe.db.get_value("Car Branch", {}, "name")

if not user_branch:
    frappe.response["message"] = []
else:
    cars = frappe.db.sql("SELECT c.name, c.brand, c.model, c.plate_no, c.status, IFNULL(oil.total_cost, 0) as total_oil_change FROM `tabCar` c JOIN `tabVehicle Fleet` f ON c.fleet = f.name LEFT JOIN (SELECT o.car, SUM(o.cost) as total_cost FROM `tabPeriodic Maintenance` o WHERE o.docstatus = 1 GROUP BY o.car) oil ON oil.car = c.name WHERE f.branch = %s ORDER BY c.name", user_branch, as_dict=True)
    frappe.response["message"] = cars
""",
		},
		{
			"name": "get_user_branch",
			"api_method": "get_user_branch",
			"script": """
user = frappe.session.user
branch = None
employee = frappe.db.get_value("Employee", {"user_id": user}, "custom_our_branch")
if employee:
    branch = employee
if not branch:
    branch = frappe.db.get_value("Car Branch", {"branch_manager": user}, "name")
fleets = []
if branch:
    fleets = frappe.get_all("Vehicle Fleet", filters={"branch": branch}, pluck="name")
frappe.response["message"] = {"branch": branch, "fleets": fleets}
""",
		},
	]

	for s in scripts:
		if not frappe.db.exists("Server Script", s["name"]):
			doc = frappe.get_doc({
				"doctype": "Server Script",
				"name": s["name"],
				"script_type": "API",
				"api_method": s["api_method"],
				"allow_guest": 0,
				"script": s["script"],
			})
			doc.insert(ignore_permissions=True)
			print(f"  Created Server Script: {s['name']}")


def create_client_scripts():
	scripts = [
		{
			"name": "Car Booking Branch Filter",
			"dt": "Car Booking",
			"script": """
frappe.ui.form.on('Car Booking', {
    setup(frm) {
        frappe.xcall('get_user_branch').then(r => {
            if (r && r.fleets && r.fleets.length > 0) {
                frm.set_query('car', () => {
                    return { filters: { fleet: ['in', r.fleets], status: 'متوفر' } };
                });
            }
        });
    }
});
""",
		},
		{
			"name": "Car Receipt Branch Filter",
			"dt": "Car Receipt",
			"script": """
frappe.ui.form.on('Car Receipt', {
    setup(frm) {
        frappe.xcall('get_user_branch').then(r => {
            if (r && r.fleets && r.fleets.length > 0) {
                frm.set_query('car', () => {
                    return { filters: { fleet: ['in', r.fleets], status: 'مؤجر' } };
                });
            }
        });
    }
});
""",
		},
		{
			"name": "Car Branch Filter",
			"dt": "Car",
			"script": """
frappe.ui.form.on('Car', {
    setup(frm) {
        frappe.xcall('get_user_branch').then(r => {
            if (r && r.branch) {
                frm.set_query('fleet', () => {
                    return { filters: { branch: r.branch } };
                });
            }
        });
    }
});
""",
		},
	]

	for s in scripts:
		if not frappe.db.exists("Client Script", s["name"]):
			doc = frappe.get_doc({
				"doctype": "Client Script",
				"__newname": s["name"],
				"dt": s["dt"],
				"script_type": "Client",
				"enabled": 1,
				"script": s["script"],
			})
			doc.insert(ignore_permissions=True)
			print(f"  Created Client Script: {s['name']}")


def create_print_formats():
	if not frappe.db.exists("Print Format", "عقد إيجار سيارة"):
		pf = frappe.get_doc({
			"doctype": "Print Format",
			"name": "عقد إيجار سيارة",
			"print_format_name": "عقد إيجار سيارة",
			"doc_type": "Car Booking",
			"print_format_type": "Jinja",
			"standard": "No",
			"custom_format": 1,
			"html": BOOKING_PRINT_FORMAT,
		})
		pf.insert(ignore_permissions=True)
		print("  Created Print Format: عقد إيجار سيارة")

	if not frappe.db.exists("Print Format", "فاتورة استلام سيارة"):
		pf = frappe.get_doc({
			"doctype": "Print Format",
			"name": "فاتورة استلام سيارة",
			"print_format_name": "فاتورة استلام سيارة",
			"doc_type": "Car Receipt",
			"print_format_type": "Jinja",
			"standard": "No",
			"custom_format": 1,
			"html": RECEIPT_PRINT_FORMAT,
		})
		pf.insert(ignore_permissions=True)
		print("  Created Print Format: فاتورة استلام سيارة")


BOOKING_PRINT_FORMAT = """<style>
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, sans-serif; direction: rtl; color: #222; font-size: 13px; line-height: 1.6; }
.contract { max-width: 750px; margin: 0 auto; }
.header { text-align: center; border-bottom: 3px solid #2e7d32; padding-bottom: 15px; margin-bottom: 20px; }
.header h1 { font-size: 22px; font-weight: 700; color: #2e7d32; margin: 0; }
.header .sub { font-size: 12px; color: #666; margin-top: 4px; }
.contract-no { display: flex; justify-content: space-between; background: #f5f5f5; padding: 8px 15px; border-radius: 6px; margin-bottom: 18px; font-size: 13px; }
.contract-no strong { color: #2e7d32; }
.section { margin-bottom: 18px; }
.section-title { font-size: 14px; font-weight: 700; color: #2e7d32; border-bottom: 2px solid #e8f5e9; padding-bottom: 5px; margin-bottom: 10px; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 20px; }
.info-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #ddd; }
.info-row .label { color: #666; font-weight: 500; }
.info-row .value { font-weight: 600; color: #222; }
.cost-box { background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 8px; padding: 15px; text-align: center; margin-top: 15px; }
.cost-box .amount { font-size: 28px; font-weight: 700; color: #2e7d32; }
.cost-box .currency { font-size: 14px; color: #666; }
.signatures { display: flex; justify-content: space-between; margin-top: 40px; }
.sig-box { text-align: center; width: 45%; }
.sig-line { border-bottom: 1px solid #222; margin-bottom: 5px; height: 40px; }
.sig-label { font-size: 12px; color: #666; }
.terms { font-size: 11px; color: #888; margin-top: 15px; padding: 10px; background: #fafafa; border-radius: 5px; }
</style>
<div class="contract">
    <div class="header">
        <h1>عقد إيجار سيارة</h1>
        <div class="sub">Car Rental Agreement</div>
    </div>
    <div class="contract-no">
        <span><strong>رقم العقد:</strong> {{ doc.name }}</span>
        <span><strong>التاريخ:</strong> {{ frappe.utils.format_date(doc.date) }}</span>
        <span><strong>الموظف:</strong> {{ doc.sales_employee_name or '-' }}</span>
    </div>
    <div class="section">
        <div class="section-title">بيانات العميل</div>
        <div class="info-grid">
            <div class="info-row"><span class="label">رمز العميل</span><span class="value">{{ doc.customer }}</span></div>
            <div class="info-row"><span class="label">الاسم الثلاثي</span><span class="value">{{ doc.customer_name_fetched or '-' }}</span></div>
            <div class="info-row"><span class="label">رقم الهاتف</span><span class="value">{{ doc.phone_fetched or '-' }}</span></div>
            <div class="info-row"><span class="label">الهاتف الدولي</span><span class="value">{{ doc.international_phone or '-' }}</span></div>
        </div>
    </div>
    <div class="section">
        <div class="section-title">بيانات السيارة</div>
        <div class="info-grid">
            <div class="info-row"><span class="label">رمز السيارة</span><span class="value">{{ doc.car or '-' }}</span></div>
            <div class="info-row"><span class="label">التصنيف</span><span class="value">{{ doc.category_car or '-' }}</span></div>
            <div class="info-row"><span class="label">الماركة / الموديل</span><span class="value">{{ doc.brand_fetched or '' }} {{ doc.model_fetched or '' }}</span></div>
            <div class="info-row"><span class="label">رقم اللوحة</span><span class="value">{{ doc.plate_no_fetched or '-' }}</span></div>
            <div class="info-row"><span class="label">عداد السيارة</span><span class="value">{{ doc.current_odometer_fetched or 0 }} كم</span></div>
        </div>
    </div>
    <div class="section">
        <div class="section-title">تفاصيل الإيجار</div>
        <div class="info-grid">
            <div class="info-row"><span class="label">تاريخ البدء</span><span class="value">{{ frappe.utils.format_date(doc.start_date) }}</span></div>
            <div class="info-row"><span class="label">تاريخ الانتهاء</span><span class="value">{{ frappe.utils.format_date(doc.end_date) }}</span></div>
            <div class="info-row"><span class="label">عدد الأيام</span><span class="value">{{ doc.duration_days }} يوم</span></div>
            <div class="info-row"><span class="label">التكلفة اليومية</span><span class="value">{{ frappe.utils.fmt_money(doc.rate_per_day) }}</span></div>
            <div class="info-row"><span class="label">الدفعة الأولى</span><span class="value">{{ doc.down_payment or '0' }}</span></div>
        </div>
    </div>
    <div class="cost-box"><div class="currency">التكلفة الإجمالية</div><div class="amount">{{ frappe.utils.fmt_money(doc.cost) }}</div></div>
    <div style="margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px;">
        <div class="signatures">
            <div class="sig-box"><div class="sig-line"></div><div class="sig-label">توقيع المستأجر</div></div>
            <div class="sig-box"><div class="sig-line"></div><div class="sig-label">توقيع الموظف</div></div>
        </div>
        <div class="terms">يقر المستأجر بتسلم السيارة بحالة جيدة ويتعهد بإعادتها بنفس الحالة في التاريخ المحدد.</div>
    </div>
</div>"""

RECEIPT_PRINT_FORMAT = """<style>
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, sans-serif; direction: rtl; color: #222; font-size: 13px; line-height: 1.6; }
.invoice { max-width: 750px; margin: 0 auto; }
.header { text-align: center; border-bottom: 3px solid #2e7d32; padding-bottom: 15px; margin-bottom: 20px; }
.header h1 { font-size: 22px; font-weight: 700; color: #2e7d32; margin: 0; }
.header .sub { font-size: 12px; color: #666; margin-top: 4px; }
.invoice-no { display: flex; justify-content: space-between; background: #f5f5f5; padding: 8px 15px; border-radius: 6px; margin-bottom: 18px; font-size: 13px; }
.invoice-no strong { color: #2e7d32; }
.section { margin-bottom: 18px; }
.section-title { font-size: 14px; font-weight: 700; color: #2e7d32; border-bottom: 2px solid #e8f5e9; padding-bottom: 5px; margin-bottom: 10px; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 20px; }
.info-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #ddd; }
.info-row .label { color: #666; font-weight: 500; }
.info-row .value { font-weight: 600; color: #222; }
.cost-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
.cost-table th { background: #2e7d32; color: #fff; padding: 8px 12px; text-align: center; }
.cost-table td { padding: 7px 12px; border: 1px solid #e0e0e0; text-align: center; }
.cost-table tr:last-child { background: #e8f5e9; font-weight: 700; font-size: 15px; }
.total-box { background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 8px; padding: 15px; text-align: center; margin-top: 15px; }
.total-box .amount { font-size: 28px; font-weight: 700; color: #2e7d32; }
.total-box .currency { font-size: 14px; color: #666; }
.signatures { display: flex; justify-content: space-between; margin-top: 40px; }
.sig-box { text-align: center; width: 45%; }
.sig-line { border-bottom: 1px solid #222; margin-bottom: 5px; height: 40px; }
.sig-label { font-size: 12px; color: #666; }
</style>
<div class="invoice">
    <div class="header">
        <h1>فاتورة استلام سيارة</h1>
        <div class="sub">Car Receipt Invoice</div>
    </div>
    <div class="invoice-no">
        <span><strong>رقم الفاتورة:</strong> {{ doc.name }}</span>
        <span><strong>رقم العقد:</strong> {{ doc.booking }}</span>
        <span><strong>تاريخ الاستلام:</strong> {{ frappe.utils.format_date(doc.receiving_date) }}</span>
    </div>
    <div class="section">
        <div class="section-title">بيانات العميل والسيارة</div>
        <div class="info-grid">
            <div class="info-row"><span class="label">اسم العميل</span><span class="value">{{ doc.customer_name or '-' }}</span></div>
            <div class="info-row"><span class="label">الموظف</span><span class="value">{{ doc.sales_employee_name or '-' }}</span></div>
            <div class="info-row"><span class="label">السيارة</span><span class="value">{{ doc.car }}</span></div>
        </div>
    </div>
    <div class="section">
        <div class="section-title">عداد المسافة (كم)</div>
        <div class="info-grid">
            <div class="info-row"><span class="label">العداد عند التسليم</span><span class="value">{{ doc.previous_odometer or 0 }} كم</span></div>
            <div class="info-row"><span class="label">العداد عند الاستلام</span><span class="value">{{ doc.current_odometer or 0 }} كم</span></div>
            <div class="info-row"><span class="label">المسافة المقطوعة</span><span class="value">{{ doc.total_distance or 0 }} كم</span></div>
        </div>
    </div>
    <div class="section">
        <div class="section-title">تفاصيل التكلفة</div>
        <table class="cost-table">
            <thead><tr><th>البند</th><th>المبلغ</th></tr></thead>
            <tbody>
                <tr><td>التكلفة الأساسية</td><td>{{ frappe.utils.fmt_money(doc.mainly_cost) }}</td></tr>
                {% if doc.extra_distance %}<tr><td>المسافة الزائدة ({{ doc.extra_distance }} كم)</td><td>{{ frappe.utils.fmt_money(doc.extra_cost) }}</td></tr>{% endif %}
                {% if doc.damage %}<tr><td>أضرار</td><td style="color:#c62828;">{{ frappe.utils.fmt_money(doc.damage) }}</td></tr>{% endif %}
                {% if doc.down_payment %}<tr><td>المدفوع مسبقاً</td><td style="color:#2e7d32;">- {{ frappe.utils.fmt_money(doc.down_payment) }}</td></tr>{% endif %}
                <tr><td>المبلغ الإجمالي المستحق</td><td>{{ frappe.utils.fmt_money(doc.total_cost) }}</td></tr>
            </tbody>
        </table>
    </div>
    <div class="total-box"><div class="currency">المبلغ الإجمالي المستحق</div><div class="amount">{{ frappe.utils.fmt_money(doc.total_cost) }}</div></div>
    {% if doc.notes %}<div class="section" style="margin-top:15px;"><div class="section-title">ملاحظات</div><p>{{ doc.notes }}</p></div>{% endif %}
    <div style="margin-top:30px;border-top:1px solid #ddd;padding-top:15px;">
        <div class="signatures">
            <div class="sig-box"><div class="sig-line"></div><div class="sig-label">توقيع المستأجر</div></div>
            <div class="sig-box"><div class="sig-line"></div><div class="sig-label">توقيع الموظف</div></div>
        </div>
    </div>
</div>"""
