app_name = "gatecar"
app_title = "Gate Cars"
app_publisher = "Ziad Suleyman"
app_description = "app for rental car"
app_email = "riseappsriseapps@gmail.com"
app_license = "mit"

# Apps
# ------------------


# required_apps = []

add_to_apps_screen = [
	{
		"name": "gatecar",
		"logo": "/assets/gatecar/images/logo.svg",
		"title": "Gate Cars",
		"route": "/app/gate-cars",
	}
]

# Navbar / desk brand logo
app_logo_url = "/assets/gatecar/images/logo.svg"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/gatecar/css/gatecar.css"
app_include_js = "/assets/gatecar/js/gatecar.js"

# include js, css files in header of web template
# web_include_css = "/assets/gatecar/css/gatecar.css"
# web_include_js = "/assets/gatecar/js/gatecar.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "gatecar/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "gatecar/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
	"methods": ["gatecar.utils.number_ordered_lists"],
}

# Installation
# ------------

# before_install = "gatecar.install.before_install"
after_install = "gatecar.setup_data.after_install"

# Uninstallation
# ------------

# before_uninstall = "gatecar.uninstall.before_uninstall"
# after_uninstall = "gatecar.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "gatecar.utils.before_app_install"
# after_app_install = "gatecar.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "gatecar.utils.before_app_uninstall"
# after_app_uninstall = "gatecar.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "gatecar.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "gatecar.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Employee": {
		"after_insert": "gatecar.employee_role.on_employee_update",
		"on_update": "gatecar.employee_role.on_employee_update",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"gatecar.tasks.check_upcoming_maintenance",
	],
}

# Testing
# -------

# before_tests = "gatecar.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "gatecar.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "gatecar.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "gatecar.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["gatecar.utils.before_request"]
# after_request = ["gatecar.utils.after_request"]

# Job Events
# ----------
# before_job = ["gatecar.utils.before_job"]
# after_job = ["gatecar.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"gatecar.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

fixtures = [
	{"dt": "Role", "filters": [["name", "in", ["مدير فرع", "مشرف أسطول", "موظف مبيعات"]]]},
	{"dt": "Designation", "filters": [["name", "in", ["مدير فرع", "مشرف أسطول", "موظف مبيعات"]]]},
	# ── DB-stored config that git alone can't carry ──────────────────────────
	{
		"dt": "Client Script",
		"filters": [["dt", "in", ["Car", "Car Booking", "Car Receipt", "Car Branch", "Customer Car", "Revenue"]]],
	},
	{"dt": "Server Script"},
	{
		"dt": "Print Format",
		"filters": [["doc_type", "in", ["Car Booking", "Car Receipt", "Car Inspection", "Revenue", "Car"]]],
	},
	{
		"dt": "Workspace",
		"filters": [["name", "in", ["Gate Cars", "الأسطول", "المبيعات", "إدارة الفرع"]]],
	},
	{"dt": "Gate Cars Settings"},
]

# Require all whitelisted methods to have type annotations
require_type_annotated_api_methods = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

