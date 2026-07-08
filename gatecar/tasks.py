import frappe
from frappe import _
from frappe.utils import today, date_diff

from gatecar.maintenance_status import DATE_FIELD_BY_TYPE, has_open_expense_of_type

# Open an expense request when a due date is within this many days (or overdue).
LEAD_DAYS = 2

# Readable labels for each date-driven trigger.
TRIGGER_LABELS = {
	"تأمين إلزامي": "التأمين الإلزامي",
	"تأمين شامل": "التأمين الشامل",
	"تسجيل": "التسجيل",
}


def check_upcoming_maintenance() -> None:
	"""Daily job: open a general-expense request for any car whose insurance/registration
	is due within LEAD_DAYS (or overdue). Opening the request locks the car so it
	cannot be rented until the paperwork is renewed and the request is approved.
	"""
	date_fields = list(DATE_FIELD_BY_TYPE.values())
	cars = frappe.get_all(
		"Car",
		fields=["name", "brand", "model", "plate_no", "fleet", *date_fields],
	)

	for car in cars:
		car_label = f"{car.brand} {car.model} ({car.plate_no})"
		for etype, field in DATE_FIELD_BY_TYPE.items():
			due = car.get(field)
			if not due:
				continue
			days_remaining = date_diff(due, today())
			if days_remaining <= LEAD_DAYS:
				open_date_expense(car, car_label, etype, due, days_remaining)


def open_date_expense(car, car_label: str, etype: str, due, days_remaining: int) -> None:
	if has_open_expense_of_type(car.name, etype):
		return  # already flagged — don't create a duplicate every day

	frappe.get_doc(
		{
			"doctype": "Car Expense",
			"car": car.name,
			"expense_type": etype,
			"التوصيف": f"تجديد {TRIGGER_LABELS.get(etype, etype)}",
		}
	).insert(ignore_permissions=True, ignore_mandatory=True)  # after_insert() locks the car

	indicator = "Red" if days_remaining < 0 else "Orange"
	send_maintenance_alert(car, car_label, etype, due, days_remaining, indicator)


def send_maintenance_alert(
	car: dict, car_label: str, mtype: str, due, days_remaining: int, indicator: str
) -> None:
	label = TRIGGER_LABELS.get(mtype, mtype)
	if days_remaining < 0:
		subject = _("تنبيه: انتهى {0} للسيارة {1}").format(label, car_label)
		message = _(
			"السيارة {0}: انتهى {1} منذ {2} يوم (بتاريخ {3}). تم فتح طلب صيانة ومنع تأجيرها."
		).format(car_label, label, abs(days_remaining), due)
	elif days_remaining == 0:
		subject = _("تنبيه: ينتهي {0} للسيارة {1} اليوم").format(label, car_label)
		message = _(
			"السيارة {0}: ينتهي {1} اليوم ({2}). تم فتح طلب صيانة ومنع تأجيرها."
		).format(car_label, label, due)
	else:
		subject = _("تنبيه: يقترب انتهاء {0} للسيارة {1}").format(label, car_label)
		message = _(
			"السيارة {0}: ينتهي {1} بعد {2} يوم ({3}). تم فتح طلب صيانة ومنع تأجيرها."
		).format(car_label, label, days_remaining, due)

	fleet_owner = frappe.db.get_value("Vehicle Fleet", car.fleet, "owner") if car.fleet else None
	recipients = get_notification_recipients(fleet_owner)

	for user in recipients:
		frappe.publish_realtime(
			"msgprint",
			{"message": message, "title": subject, "indicator": indicator},
			user=user,
		)

	frappe.get_doc(
		{
			"doctype": "Notification Log",
			"subject": subject,
			"email_content": message,
			"type": "Alert",
			"document_type": "Car",
			"document_name": car.name,
			"for_user": recipients[0] if recipients else "Administrator",
		}
	).insert(ignore_permissions=True)


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
