function fetch_car_details(frm) {
	if (!frm.doc.car) {
		["chassis_no_fetched", "year_fetched", "plate_no_fetched"].forEach(f => frm.set_value(f, ""));
		return;
	}
	frappe.call({
		method: "frappe.client.get",
		args: { doctype: "Car", name: frm.doc.car },
		callback(r) {
			if (!r.message) return;
			const c = r.message;
			frm.set_value("chassis_no_fetched", c.chassis_no || "");
			frm.set_value("year_fetched",        c["سنة_الصنع"] || "");
			frm.set_value("plate_no_fetched",    c.plate_no || "");
		}
	});
}

function fetch_customer_details(frm) {
	if (!frm.doc.customer) {
		["mother_name_fetched","dob_fetched","national_id_fetched","nationality_fetched",
		 "passport_no_fetched","license_no_fetched","license_issue_place_fetched",
		 "license_issue_date_fetched","license_expiry_date_fetched","address_fetched"]
		.forEach(f => frm.set_value(f, ""));
		return;
	}
	frappe.call({
		method: "frappe.client.get",
		args: { doctype: "Customer Car", name: frm.doc.customer },
		callback(r) {
			if (!r.message) return;
			const c = r.message;
			frm.set_value("mother_name_fetched",         c["اسم_الأم"] || "");
			frm.set_value("dob_fetched",                 c["التولد"] || "");
			frm.set_value("national_id_fetched",         c["الرقم_الوطني"] || "");
			frm.set_value("nationality_fetched",         c["nationality"] || "");
			frm.set_value("passport_no_fetched",         c["رقم_جواز_السفر"] || "");
			frm.set_value("license_no_fetched",          c["رقم_رخصة_القيادة"] || "");
			frm.set_value("license_issue_place_fetched", c["مكان_الإصدار"] || "");
			frm.set_value("license_issue_date_fetched",  c["تاريخ_الاصدار"] || "");
			frm.set_value("license_expiry_date_fetched", c["تاريخ_الانتهاء"] || "");
			frm.set_value("address_fetched",             c["العنوان"] || "");

			show_customer_classification_flag(c["التصنيف"], c["سبب_الحظر"]);
		}
	});
}

// تنبيه فقط (لا يمنع المتابعة) — يظهر عند اختيار عميل VIP أو محظور.
function show_customer_classification_flag(classification, blacklist_reason) {
	if (classification === "محظور") {
		frappe.msgprint({
			title: __("تنبيه: عميل محظور"),
			message: __("هذا العميل مُصنَّف كـ [محظور].") +
				(blacklist_reason ? `<br><b>${__("السبب")}:</b> ${frappe.utils.escape_html(blacklist_reason)}` : ""),
			indicator: "red",
		});
	} else if (classification === "VIP") {
		frappe.show_alert({ message: __("⭐ عميل VIP"), indicator: "yellow" }, 7);
	}
}

// ── Inspection checklist viewer ───────────────────────────────────────────
// Each group: [title, rows, notes_field]
const INSPECTION_GROUPS = [
	["1. الفحص الخارجي للمركبة", [
		["front_bumper", "الصدام الأمامي"], ["rear_bumper", "الصدام الخلفي"],
		["left_side", "الجانب الأيسر"], ["right_side", "الجانب الأيمن"],
		["roof", "السقف"], ["front_glass", "الزجاج الأمامي"],
		["windows_mirrors", "النوافذ والمرايا"], ["lights", "الأضواء (الأمامية والخلفية)"],
		["signals", "المصابيح والإشارات"], ["license_plate_check", "لوحة المركبة"],
	], "external_notes"],
	["2. الفحص الداخلي للمركبة", [
		["seats", "المقاعد"], ["dashboard_check", "لوحة القيادة"],
		["doors_locks", "الأبواب والأقفال الداخلية"], ["floor_carpet", "الأرضية والسجاد"],
		["ac_heating", "نظام التكييف والتدفئة"], ["audio_system", "النظام الصوتي والوسائط"],
		["electric_windows", "النوافذ الكهربائية"], ["interior_lighting", "الإضاءة الداخلية"],
		["no_odors", "خلو المركبة من الروائح"], ["no_smoking", "حرق سجائر"],
	], "internal_notes"],
	["3. الفحص الميكانيكي وعناصر السلامة", [
		["engine_warning", "مؤشر أعطال المحرك"], ["engine_oil", "زيت المحرك"],
		["tires", "مستوى الإطارات"], ["spare_tire_tools", "الإطار الاحتياطي وأدواته"],
		["first_aid_kit", "حقيبة الإسعافات الأولية"], ["car_jack", "رافعة السيارة"],
		["charger_cable", "وصلة شحن السيارة"], ["safety_triangle", "مثلث الأمان"],
	], "mechanical_notes"],
];

function status_badge(val) {
	const map = {
		"سليم":     ["#e8f5e9", "#2e7d32"],
		"متضرر":    ["#fbe9e7", "#c62828"],
		"غير متاح": ["#f5f5f5", "#757575"],
	};
	const [bg, fg] = map[val] || ["#f5f5f5", "#999"];
	return `<span style="background:${bg};color:${fg};font-weight:600;padding:2px 10px;border-radius:10px;font-size:12px;white-space:nowrap;">${frappe.utils.escape_html(val || "—")}</span>`;
}

function notes_row(doc, field) {
	if (!doc[field]) return "";
	return `<div style="margin:4px 0 2px;padding:6px 10px;background:#f5f5f5;border-right:3px solid #2e7d32;border-radius:4px;font-size:13px;">
		<b>ملاحظات إضافية:</b> ${frappe.utils.escape_html(doc[field])}</div>`;
}

function build_inspection_html(doc) {
	let html = `<div style="direction:rtl;text-align:right;">`;

	// Header info block
	const info = [
		["نوع الفحص", doc.inspection_type || "—"],
		["التاريخ والوقت", doc.inspection_date ? frappe.datetime.str_to_user(doc.inspection_date) : "—"],
		["اسم العميل", doc.customer_name || "—"],
		["رقم اللوحة", doc.plate_no || "—"],
		["رقم الهاتف", doc.phone || "—"],
	];
	html += `<div style="font-weight:700;color:#fff;background:#455a64;padding:5px 10px;border-radius:5px;margin:0 0 6px;">معلومات الفحص</div>`;
	html += `<table style="width:100%;border-collapse:collapse;">`;
	info.forEach(([lbl, val]) => {
		html += `<tr><td style="padding:4px 8px;border-bottom:1px solid #eee;width:45%;">${lbl}</td>
			<td style="padding:4px 8px;border-bottom:1px solid #eee;text-align:left;font-weight:600;">${frappe.utils.escape_html(String(val))}</td></tr>`;
	});
	html += `</table>`;

	INSPECTION_GROUPS.forEach(([title, rows, notes_field]) => {
		html += `<div style="font-weight:700;color:#fff;background:#2e7d32;padding:5px 10px;border-radius:5px;margin:10px 0 6px;">${title}</div>`;
		html += `<table style="width:100%;border-collapse:collapse;">`;
		rows.forEach(([fn, lbl]) => {
			html += `<tr>
				<td style="padding:4px 8px;border-bottom:1px solid #eee;">${lbl}</td>
				<td style="padding:4px 8px;border-bottom:1px solid #eee;text-align:left;">${status_badge(doc[fn])}</td>
			</tr>`;
		});
		html += `</table>`;
		html += notes_row(doc, notes_field);
	});
	// Fuel + documents + damage
	html += `<div style="font-weight:700;color:#fff;background:#455a64;padding:5px 10px;border-radius:5px;margin:10px 0 6px;">الوقود والمستندات والملاحظات</div>`;
	html += `<table style="width:100%;border-collapse:collapse;">`;
	const extra = [
		["مستوى الوقود", doc.fuel_level || "—"],
		["نوع الوقود", doc.fuel_type || "—"],
		["مستوى الوقود متفق عليه", doc.fuel_level_agreed ? "نعم" : "لا"],
		["وجود المستندات (رخصة/تأمين)", doc.documents_present ? "نعم" : "لا"],
		["عداد الكيلومترات", doc.odometer || "—"],
	];
	extra.forEach(([lbl, val]) => {
		html += `<tr><td style="padding:4px 8px;border-bottom:1px solid #eee;">${lbl}</td>
			<td style="padding:4px 8px;border-bottom:1px solid #eee;text-align:left;font-weight:600;">${frappe.utils.escape_html(String(val))}</td></tr>`;
	});
	html += `</table>`;
	if (doc.pre_existing_damage) {
		html += `<div style="margin-top:10px;padding:8px 10px;background:#fff8e1;border:1px solid #ffe082;border-radius:5px;">
			<b>الأضرار الموجودة مسبقاً:</b><br>${frappe.utils.escape_html(doc.pre_existing_damage)}</div>`;
	}
	html += `</div>`;
	return html;
}

function show_inspection_dialog(name) {
	frappe.db.get_doc("Car Inspection", name).then((doc) => {
		const d = new frappe.ui.Dialog({
			title: __("فحص السيارة ({0}) — {1}", [doc.inspection_type, doc.name]),
			size: "large",
			fields: [{ fieldtype: "HTML", fieldname: "body" }],
			primary_action_label: __("فتح النموذج الكامل"),
			primary_action: () => frappe.set_route("Form", "Car Inspection", name),
		});
		d.fields_dict.body.$wrapper.html(build_inspection_html(doc));
		d.show();
	});
}

function build_invoice_html(doc) {
	const money = (v) => format_currency(v || 0);
	let html = `<div style="font-family:inherit;font-size:13px;">`;

	const info = [
		["رقم الفاتورة", doc.name],
		["السيارة", doc.car || "—"],
		["اسم العميل", doc.customer_name || "—"],
		["تاريخ التسليم", doc.pickup_date ? frappe.datetime.str_to_user(doc.pickup_date) : "—"],
		["تاريخ الاستلام", doc.receiving_date ? frappe.datetime.str_to_user(doc.receiving_date) : "—"],
		["عدد الأيام الفعلي", doc.real_days || doc.duration_days || "—"],
	];
	html += `<table style="width:100%;border-collapse:collapse;">`;
	info.forEach(([lbl, val]) => {
		html += `<tr><td style="padding:4px 8px;border-bottom:1px solid #eee;width:45%;">${lbl}</td>
			<td style="padding:4px 8px;border-bottom:1px solid #eee;text-align:left;font-weight:600;">${frappe.utils.escape_html(String(val))}</td></tr>`;
	});
	html += `</table>`;

	html += `<div style="font-weight:700;color:#fff;background:#2e7d32;padding:5px 10px;border-radius:5px;margin:10px 0 6px;">التفاصيل المالية</div>`;
	const fin = [
		["التكلفة الأساسية", money(doc.mainly_cost)],
		["الكلفة الإضافية", money(doc.extra_cost)],
		["الأضرار", money(doc.damage)],
		["الإجمالي قبل الضريبة", money(doc.total_cost)],
		["ضريبة الإنفاق", money(doc.spending_tax)],
		["ضريبة المحلية", money(doc.local_tax)],
	];
	html += `<table style="width:100%;border-collapse:collapse;">`;
	fin.forEach(([lbl, val]) => {
		html += `<tr><td style="padding:4px 8px;border-bottom:1px solid #eee;">${lbl}</td>
			<td style="padding:4px 8px;border-bottom:1px solid #eee;text-align:left;font-weight:600;">${val}</td></tr>`;
	});
	html += `</table>`;

	html += `<div style="margin-top:10px;padding:10px 14px;background:#e8f5e9;border:2px solid #66bb6a;border-radius:8px;display:flex;justify-content:space-between;align-items:center;">
		<span style="font-weight:700;color:#1b5e20;">الإجمالي النهائي شامل الضرائب</span>
		<span style="font-weight:800;font-size:18px;color:#1b5e20;">${money(doc.grand_total)}</span></div>`;
	html += `</div>`;
	return html;
}

function show_invoice_dialog(name) {
	frappe.db.get_doc("Car Receipt", name).then((doc) => {
		const d = new frappe.ui.Dialog({
			title: __("الفاتورة النهائية — {0}", [doc.name]),
			size: "large",
			fields: [{ fieldtype: "HTML", fieldname: "body" }],
			primary_action_label: __("فتح النموذج الكامل"),
			primary_action: () => frappe.set_route("Form", "Car Receipt", name),
		});
		d.fields_dict.body.$wrapper.html(build_invoice_html(doc));
		d.show();
	});
}

function build_revenues_html(rows) {
	const money = (v) => format_currency(v || 0);
	let total = 0;
	const body = rows.map((r, i) => {
		const is_pay = r.payment_type === "دفع";
		total += (is_pay ? -1 : 1) * (r.amount || 0);
		const color = is_pay ? "#c62828" : "#2e7d32";
		const badge = is_pay
			? `<span style="background:#fbe9e7;color:#c62828;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600;">دفع</span>`
			: `<span style="background:#e8f5e9;color:#2e7d32;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600;">قبض</span>`;
		return `<tr style="${is_pay ? 'background:#fff8f8;' : ''}">
			<td style="padding:6px 8px;border-bottom:1px solid #eee;">${i + 1}</td>
			<td style="padding:6px 8px;border-bottom:1px solid #eee;"><a href="/app/revenue/${r.name}">${r.name}</a> ${badge}</td>
			<td style="padding:6px 8px;border-bottom:1px solid #eee;">${r.date ? frappe.datetime.str_to_user(r.date) : "—"}</td>
			<td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:left;font-weight:700;color:${color};">${is_pay ? "- " : ""}${money(r.amount)}</td>
			<td style="padding:6px 8px;border-bottom:1px solid #eee;">${r.payment_method || "—"}</td>
			<td style="padding:6px 8px;border-bottom:1px solid #eee;">${r.notes || "—"}</td>
		</tr>`;
	}).join("");

	return `<div style="font-family:inherit;font-size:13px;">
		<table style="width:100%;border-collapse:collapse;">
			<thead><tr style="background:#2e7d32;color:#fff;">
				<th style="padding:7px 8px;">#</th>
				<th style="padding:7px 8px;">رقم القيد</th>
				<th style="padding:7px 8px;">التاريخ</th>
				<th style="padding:7px 8px;">المبلغ</th>
				<th style="padding:7px 8px;">طريقة الدفع</th>
				<th style="padding:7px 8px;">ملاحظات</th>
			</tr></thead>
			<tbody>${body}</tbody>
		</table>
		<div style="margin-top:12px;padding:10px 14px;background:#e8f5e9;border:2px solid #66bb6a;border-radius:8px;display:flex;justify-content:space-between;align-items:center;">
			<span style="font-weight:700;color:#1b5e20;">إجمالي المقبوض (قبض − دفع)</span>
			<span style="font-weight:800;font-size:18px;color:#1b5e20;">${money(total)}</span>
		</div>
	</div>`;
}

function show_revenues_dialog(booking_name) {
	frappe.db.get_list("Revenue", {
		filters: { booking_reference: booking_name },
		fields: ["name", "date", "amount", "payment_type", "payment_method", "notes"],
		order_by: "date asc, creation asc",
		limit: 0,
	}).then((rows) => {
		if (!rows || !rows.length) {
			frappe.msgprint(__("لا توجد قيود مالية مرتبطة بهذا العقد"));
			return;
		}
		const d = new frappe.ui.Dialog({
			title: __("القيود المالية — {0}", [booking_name]),
			size: "large",
			fields: [{ fieldtype: "HTML", fieldname: "body" }],
			primary_action_label: __("فتح قائمة القيود"),
			primary_action: () =>
				frappe.set_route("List", "Revenue", { booking_reference: booking_name }),
		});
		d.fields_dict.body.$wrapper.html(build_revenues_html(rows));
		d.show();
	});
}

function render_rental_info_buttons(frm) {
	const GROUP = __("معلومات التأجير");

	// Financial entries (Revenue: قبض/دفع) linked to this booking
	frm.add_custom_button(
		__("عرض القيود المالية"),
		() => show_revenues_dialog(frm.doc.name),
		GROUP
	);

	// Inspections (تسليم / استلام) — view each checklist in a dialog
	frappe.db.get_list("Car Inspection", {
		filters: { booking: frm.doc.name },
		fields: ["name", "inspection_type"],
		order_by: "creation asc",
		limit: 0,
	}).then((rows) => {
		rows.forEach((r) => {
			const label = r.inspection_type === "عند الاستلام"
				? __("عرض فحص الاستلام")
				: __("عرض فحص التسليم");
			frm.add_custom_button(label, () => show_inspection_dialog(r.name), GROUP);
		});
	});

	// Final invoice (Car Receipt) — view summary in a dialog
	frappe.db.get_list("Car Receipt", {
		filters: { booking: frm.doc.name },
		fields: ["name"],
		order_by: "creation desc",
		limit: 1,
	}).then((rows) => {
		if (rows && rows.length) {
			frm.add_custom_button(
				__("عرض الفاتورة النهائية"),
				() => show_invoice_dialog(rows[0].name),
				GROUP
			);
		}
	});
}

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

	customer(frm) {
		fetch_customer_details(frm);
	},

	car(frm) {
		fetch_car_details(frm);
	},

	refresh(frm) {
		// On load: populate fetched fields if missing
		if (frm.doc.customer && !frm.doc.mother_name_fetched) {
			fetch_customer_details(frm);
		}
		if (frm.doc.car && !frm.doc.year_fetched) {
			fetch_car_details(frm);
		}
		// Contract terms: editable only by System Manager
		const is_admin = frappe.user_roles.includes("System Manager");
		frm.set_df_property("text_viwt", "read_only", is_admin ? 0 : 1);

		// "معلومات التأجير": view linked inspections (تسليم/استلام) + final invoice
		if (!frm.is_new()) {
			render_rental_info_buttons(frm);
		}

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("فحص السيارة — تسليم"), () => {
				frappe.new_doc("Car Inspection", {
					booking:         frm.doc.name,
					inspection_type: "عند التسليم",
				});
			}, __("Create"));

			frm.add_custom_button(__("فحص السيارة — استلام"), () => {
				frappe.new_doc("Car Inspection", {
					booking:         frm.doc.name,
					inspection_type: "عند الاستلام",
				});
			}, __("Create"));

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

			frm.add_custom_button(__("إيصال قبض"), () => {
				const today = frappe.datetime.get_today();
				const defaults = {
					payment_type: "قبض",
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

			frm.add_custom_button(__("إيصال دفع"), () => {
				const today = frappe.datetime.get_today();
				const defaults = {
					payment_type: "دفع",
					booking_reference: frm.doc.name,
					car: frm.doc.car,
					customer_name: frm.doc.customer_name_fetched,
					date: today,
				};
				frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name")
					.then(r => {
						const employee = r.message && r.message.name;
						if (employee) defaults.receiver = employee;
						frappe.new_doc("Revenue", defaults);
					});
			}, __("Create"));

			frm.page.set_inner_btn_group_as_primary(__("Create"));
		}
	},
});
