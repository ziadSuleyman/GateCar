# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CashTransaction(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		amount: DF.Currency
		balance_after: DF.Currency
		beneficiary: DF.Data
		branch: DF.Link | None
		branch_manager_name: DF.Data | None
		date: DF.Date
		notes: DF.SmallText | None
		other_payment_method: DF.Data | None
		payment_method: DF.Literal["كاش", "شام كاش", "أخرى"]
		recipient_name: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Cash Transaction"

	def before_insert(self) -> None:
		if not self.branch:
			user = frappe.session.user
			branch = frappe.db.get_value("Car Branch", {"branch_manager": user}, "name")
			if not branch and user == "Administrator":
				branch = frappe.db.get_value("Car Branch", {}, "name")
			self.branch = branch

		if self.branch and not self.branch_manager_name:
			manager = frappe.db.get_value("Car Branch", self.branch, "branch_manager")
			self.branch_manager_name = frappe.db.get_value("User", manager, "full_name") if manager else ""

	def validate(self) -> None:
		if flt(self.amount) <= 0:
			frappe.throw(_("المبلغ يجب أن يكون أكبر من صفر"))

		# mandatory_depends_on is a client-side-only concept in Frappe (never
		# enforced server-side — see base_document.py::_get_missing_mandatory_fields,
		# which only ever looks at reqd=1), so this must be checked explicitly here.
		if self.payment_method == "أخرى" and not self.other_payment_method:
			frappe.throw(_("يجب تحديد طريقة الدفع عند اختيار (أخرى)"))

		from gatecar.cash import get_cash_balance

		available = get_cash_balance()
		if flt(self.amount) > available:
			frappe.throw(
				_("المبلغ المطلوب سحبه ({0}) يتجاوز الرصيد المتاح حالياً في الصندوق ({1}).").format(
					flt(self.amount), available
				)
			)

	def on_submit(self) -> None:
		from gatecar.cash import get_cash_balance

		self.db_set("balance_after", get_cash_balance())

	def on_cancel(self) -> None:
		# Checked as "does anything *newer* than me still exist", not "am I the
		# latest" — by the time on_cancel fires, Frappe has already written this
		# row's own docstatus=2 to the DB (db_update happens before
		# run_post_save_methods), so a plain "latest submitted == self.name"
		# comparison would always fail once self drops out of the docstatus=1
		# pool, wrongly rejecting cancellation of the true latest entry.
		# Compared by `name`, not `creation` — the autoname series (CTX-#####) is
		# a strictly increasing, collision-free sequence, whereas `creation` can
		# tie at the same timestamp for documents inserted in quick succession
		# (e.g. scripted/console-driven creation).
		newer_exists = frappe.db.exists("Cash Transaction", {"docstatus": 1, "name": (">", self.name)})
		if newer_exists:
			frappe.throw(
				_(
					"لا يمكن إلغاء هذه العملية لأنها ليست آخر عملية في سجل الصندوق —"
					" سيؤدي إلغاؤها إلى عدم تطابق رصيد العمليات اللاحقة."
					" سجّل عملية جديدة معاكسة بدلاً من ذلك."
				)
			)
