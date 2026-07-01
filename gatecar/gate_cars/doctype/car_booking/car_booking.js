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
				const today = frappe.datetime.get_today();
				const defaults = {
					booking_reference: frm.doc.name,
					car: frm.doc.car,
					customer_name: frm.doc.customer_name_fetched,
					date: today,
				};
				frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name")
					.then(r => {
						const employee = r.message && r.message.name;
						if (employee) defaults.receiver = employee;
						if (!employee) {
							frappe.new_doc("Revenue", defaults);
							return;
						}
						frappe.db.get_value("Shift Assignment", {
							employee: employee,
							status: "Active",
							docstatus: 1,
							start_date: ["<=", today],
							end_date: [">=", today],
						}, "shift_type").then(sr => {
							const shift = sr.message && sr.message.shift_type;
							if (shift) defaults.shift = shift;
							frappe.new_doc("Revenue", defaults);
						});
					});
			}, __("Create"));

			frm.page.set_inner_btn_group_as_primary(__("Create"));
		}
	},
});
