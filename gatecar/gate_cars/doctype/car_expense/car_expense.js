frappe.ui.form.on("Car Expense", {
	refresh(frm) {
		frm.set_df_property("car", "read_only", !frm.is_new());
	},
});
