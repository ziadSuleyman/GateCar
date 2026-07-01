frappe.ui.form.on("Car Booking", {
	setup(frm) {
		if (frm.is_new() && !frm.doc.sales_employee) {
			frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name")
				.then((r) => {
					if (r.message && r.message.name) {
						frm.set_value("sales_employee", r.message.name);
					}
				});
		}
	},

	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("استلام سيارة"), () => {
				frappe.new_doc("Car Receipt", {
					booking: frm.doc.name,
					car: frm.doc.car,
					pickup_date: frm.doc.start_date,
					customer_name: frm.doc.customer_name_fetched,
					duration_days: frm.doc.duration_days,
					down_payment: frm.doc.down_payment,
					sales_employee: frm.doc.sales_employee,
					mainly_cost: frm.doc.cost,
				});
			}, __("Create"));

			frm.add_custom_button(__("دفعة"), () => {
				frappe.new_doc("Revenue", {
					booking_reference: frm.doc.name,
					car: frm.doc.car,
					customer_name: frm.doc.customer_name_fetched,
					date: frappe.datetime.get_today(),
				});
			}, __("Create"));

			frm.page.set_inner_btn_group_as_primary(__("Create"));
		}
	},
});
