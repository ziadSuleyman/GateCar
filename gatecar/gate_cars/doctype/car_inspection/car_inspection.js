frappe.ui.form.on("Car Inspection", {
	booking(frm) {
		if (!frm.doc.booking) return;
		frappe.call({
			method: "frappe.client.get",
			args: { doctype: "Car Booking", name: frm.doc.booking },
			callback(r) {
				if (!r.message) return;
				const b = r.message;
				frm.set_value("customer_name", b.customer_name_fetched || "");
				frm.set_value("car",           b.car || "");
				frm.set_value("plate_no",      b.plate_no_fetched || "");
				frm.set_value("phone",         b.phone_fetched || "");
				if (b.car) {
					frappe.call({
						method: "frappe.client.get",
						args: { doctype: "Car", name: b.car },
						callback(rc) {
							if (rc.message) {
								frm.set_value("odometer", rc.message.current_odometer || 0);
								frm.set_value("fuel_type", rc.message.fuel_type || "");
							}
						},
					});
				}
			},
		});
	},

	refresh(frm) {
		color_status_fields(frm);
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("طباعة نموذج الفحص"), () => {
				// Green "تسليم" form on handover, navy "استلام" form on return
				const pf = frm.doc.inspection_type === "عند الاستلام"
					? "نموذج استلام مركبة"
					: "نموذج تسليم مركبة";
				frappe.utils.print(frm.doctype, frm.docname, pf);
			});
		}
	},
});

// Colour the Select fields: green=سليم, red=متضرر, grey=غير متاح
function color_status_fields(frm) {
	const STATUS_FIELDS = [
		"front_bumper","rear_bumper","left_side","right_side","roof","license_plate_check",
		"front_glass","windows_mirrors","lights","signals",
		"seats","dashboard_check","doors_locks","floor_carpet","ac_heating","no_smoking",
		"electric_windows","audio_system","interior_lighting","no_odors",
		"engine_warning","engine_oil","tires","spare_tire_tools",
		"first_aid_kit","car_jack","charger_cable","safety_triangle",
	];
	const COLOR = { "سليم": "#e8f5e9", "متضرر": "#fbe9e7", "غير متاح": "#f5f5f5" };
	const TEXT  = { "سليم": "#2e7d32", "متضرر": "#c62828", "غير متاح": "#757575" };

	STATUS_FIELDS.forEach(fn => {
		const val = frm.doc[fn];
		const $wrap = frm.fields_dict[fn] && frm.fields_dict[fn].$wrapper;
		if ($wrap) {
			$wrap.find("select").css({
				"background-color": COLOR[val] || "",
				"color": TEXT[val] || "",
				"font-weight": "600",
				"border-radius": "6px",
			});
		}
	});
}

// Re-colour on each select change
frappe.ui.form.on("Car Inspection", {
	front_bumper:       frm => color_status_fields(frm),
	rear_bumper:        frm => color_status_fields(frm),
	left_side:          frm => color_status_fields(frm),
	right_side:         frm => color_status_fields(frm),
	roof:               frm => color_status_fields(frm),
	license_plate_check:frm => color_status_fields(frm),
	front_glass:        frm => color_status_fields(frm),
	windows_mirrors:    frm => color_status_fields(frm),
	lights:             frm => color_status_fields(frm),
	signals:            frm => color_status_fields(frm),
	seats:              frm => color_status_fields(frm),
	dashboard_check:    frm => color_status_fields(frm),
	doors_locks:        frm => color_status_fields(frm),
	floor_carpet:       frm => color_status_fields(frm),
	ac_heating:         frm => color_status_fields(frm),
	no_smoking:         frm => color_status_fields(frm),
	electric_windows:   frm => color_status_fields(frm),
	audio_system:       frm => color_status_fields(frm),
	interior_lighting:  frm => color_status_fields(frm),
	no_odors:           frm => color_status_fields(frm),
	engine_warning:     frm => color_status_fields(frm),
	engine_oil:         frm => color_status_fields(frm),
	tires:              frm => color_status_fields(frm),
	spare_tire_tools:   frm => color_status_fields(frm),
	first_aid_kit:      frm => color_status_fields(frm),
	car_jack:           frm => color_status_fields(frm),
	charger_cable:      frm => color_status_fields(frm),
	safety_triangle:    frm => color_status_fields(frm),
});
