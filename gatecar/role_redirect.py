import frappe
from frappe.website.utils import get_home_page


def resolve_website_path(path: str) -> str:
	if path:
		return path

	if frappe.session.user == "Administrator":
		home_page = "desk/gate-cars"
	else:
		home_page = get_home_page().strip("/") or "desk"
	frappe.flags.redirect_location = f"/{home_page}"
	raise frappe.Redirect(302)
