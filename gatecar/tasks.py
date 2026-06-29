import frappe
from frappe import _
from frappe.utils import today, date_diff, getdate


def check_upcoming_maintenance() -> None:
	cars = frappe.get_all(
		"Car",
		filters={
			"تاريخ_الصيانة_القادمة": ["is", "set"],
			"status": ["!=", "داخل الصيانة"],
		},
		fields=["name", "brand", "model", "plate_no", "تاريخ_الصيانة_القادمة", "fleet"],
	)

	for car in cars:
		days_remaining = date_diff(car.تاريخ_الصيانة_القادمة, today())
		car_label = f"{car.brand} {car.model} ({car.plate_no})"

		if days_remaining < 0:
			send_maintenance_alert(car, car_label, days_remaining, "Red")
		elif days_remaining <= 3:
			send_maintenance_alert(car, car_label, days_remaining, "Orange")


def send_maintenance_alert(
	car: dict, car_label: str, days_remaining: int, indicator: str
) -> None:
	if days_remaining < 0:
		subject = _("تنبيه: تجاوز موعد صيانة السيارة {0}").format(car_label)
		message = _("السيارة {0} تجاوزت موعد الصيانة بـ {1} يوم. التاريخ المحدد: {2}").format(
			car_label, abs(days_remaining), car.تاريخ_الصيانة_القادمة
		)
	elif days_remaining == 0:
		subject = _("تنبيه: موعد صيانة السيارة {0} اليوم").format(car_label)
		message = _("السيارة {0} موعد صيانتها اليوم {1}").format(
			car_label, car.تاريخ_الصيانة_القادمة
		)
	else:
		subject = _("تذكير: اقتراب موعد صيانة السيارة {0}").format(car_label)
		message = _("السيارة {0} موعد صيانتها بعد {1} أيام. التاريخ: {2}").format(
			car_label, days_remaining, car.تاريخ_الصيانة_القادمة
		)

	fleet_owner = None
	if car.fleet:
		fleet_owner = frappe.db.get_value("Vehicle Fleet", car.fleet, "owner")

	recipients = get_notification_recipients(fleet_owner)

	for user in recipients:
		frappe.publish_realtime(
			"msgprint",
			{"message": message, "title": subject, "indicator": indicator},
			user=user,
		)

	doc = frappe.get_doc(
		{
			"doctype": "Notification Log",
			"subject": subject,
			"email_content": message,
			"type": "Alert",
			"document_type": "Car",
			"document_name": car.name,
			"for_user": recipients[0] if recipients else "Administrator",
		}
	)
	doc.insert(ignore_permissions=True)


def get_notification_recipients(fleet_owner: str | None = None) -> list[str]:
	recipients = set()

	if fleet_owner:
		recipients.add(fleet_owner)

	managers = frappe.get_all(
		"Has Role",
		filters={"role": ["in", ["System Manager", "مشرف أسطول"]], "parenttype": "User"},
		fields=["parent"],
	)
	for m in managers:
		if frappe.utils.cint(frappe.db.get_value("User", m.parent, "enabled")):
			recipients.add(m.parent)

	if not recipients:
		recipients.add("Administrator")

	return list(recipients)
