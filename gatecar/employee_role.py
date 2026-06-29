import frappe

DESIGNATION_ROLE_MAP = {
	"مدير فرع": "مدير فرع",
	"مشرف أسطول": "مشرف أسطول",
	"موظف مبيعات": "موظف مبيعات",
}

MANAGED_ROLES = set(DESIGNATION_ROLE_MAP.values())


def on_employee_update(doc, method=None) -> None:
	if not doc.user_id:
		return

	user = frappe.get_doc("User", doc.user_id)
	current_roles = {r.role for r in user.roles}

	old_designation = None
	if doc.get_doc_before_save():
		old_designation = doc.get_doc_before_save().designation

	if old_designation and old_designation != doc.designation:
		old_role = DESIGNATION_ROLE_MAP.get(old_designation)
		if old_role and old_role in current_roles:
			user.remove_roles(old_role)

	new_role = DESIGNATION_ROLE_MAP.get(doc.designation)
	if new_role and new_role not in current_roles:
		user.add_roles(new_role)
		frappe.msgprint(
			f"تم تعيين دور [{new_role}] للمستخدم {doc.user_id} تلقائياً",
			indicator="green",
			alert=True,
		)
