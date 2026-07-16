frappe.ui.form.on("Car Statistics", {
	refresh(frm) {
		load_statistics(frm);
	},

	branch(frm) {
		load_statistics(frm);
	},
});

function load_statistics(frm) {
	frappe.call({
		method: "gatecar.gate_cars.doctype.car_statistics.car_statistics.get_statistics",
		args: { branch: frm.doc.branch || null },
		callback({ message }) {
			if (!message) return;
			Object.entries(message).forEach(([field, value]) => {
				frm.doc[field] = value;
				frm.refresh_field(field);
			});
			frm.doc.__unsaved = 0;
		},
	});
}
