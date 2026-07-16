frappe.ui.form.on("Cash Transaction", {
	refresh: function (frm) {
		show_current_balance(frm);
	},
});

function show_current_balance(frm) {
	frappe.xcall("gatecar.cash.get_cash_balance_api").then((balance) => {
		frm.dashboard.set_headline(
			__("الرصيد الحالي في الصندوق: {0}", [format_currency(flt(balance) || 0)]),
		);
	});
}
