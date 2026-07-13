frappe.ui.form.on("Car Receipt", {
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
		load_previous_payments(frm);
		// On a fresh receipt, pull return odometer + date if not entered yet.
		if (frm.doc.booking && (!frm.doc.current_odometer || !frm.doc.receiving_date)) {
			fetch_return_inspection(frm);
		}
	},

	booking(frm) {
		load_previous_payments(frm);
		fetch_return_inspection(frm);
	},

	current_odometer(frm) {
		// اجمالي المسافة المقطوعة = القراءة الحالية - القراءة السابقة
		if (frm.doc.current_odometer && frm.doc.previous_odometer != null) {
			frm.set_value(
				"total_distance",
				Math.max(0, frm.doc.current_odometer - frm.doc.previous_odometer)
			);
		}
	},

	// جدول "الإيصالات السابقة" يعرض "المتبقي" = grand_total الحالي ناقص المدفوع،
	// فيجب إعادة رسمه في كل مرة يتغيّر فيها grand_total (وليس فقط عند فتح
	// النموذج) — وإلا يبقى المتبقي محسوباً على قيمة فاتورة قديمة.
	grand_total(frm) {
		load_previous_payments(frm);
	},
});

// Auto-fetch the odometer + date/time recorded in the "عند الاستلام" (return)
// Car Inspection for the same booking → current reading + actual receiving date.
function fetch_return_inspection(frm) {
	if (!frm.doc.booking) return;
	frappe.db
		.get_list("Car Inspection", {
			filters: { booking: frm.doc.booking, inspection_type: "عند الاستلام" },
			fields: ["name", "odometer", "inspection_date"],
			order_by: "creation desc",
			limit: 1,
		})
		.then((rows) => {
			if (!rows || !rows.length) return;
			const insp = rows[0];
			if (insp.odometer) {
				frm.set_value("current_odometer", insp.odometer);
			}
			if (insp.inspection_date) {
				// inspection_date is Datetime; receiving_date is a Date → take the date part.
				frm.set_value("receiving_date", insp.inspection_date.split(" ")[0]);
			}
		});
}

function load_previous_payments(frm) {
	const wrapper = frm.fields_dict.previous_payments_html.$wrapper;
	if (!frm.doc.booking) {
		wrapper.html(`<p class="text-muted" style="padding: 8px 0;">${__("لا يوجد عقد مرتبط")}</p>`);
		return;
	}

	frappe.db.get_list("Revenue", {
		filters: { booking_reference: frm.doc.booking },
		fields: ["name", "date", "amount", "payment_method", "receiver", "notes", "payment_type"],
		order_by: "date asc",
	}).then(rows => {
		if (!rows || rows.length === 0) {
			wrapper.html(`<p class="text-muted" style="padding: 8px 0;">${__("لا توجد دفعات مسجلة لهذا العقد")}</p>`);
			return;
		}

		const receiver_ids = [...new Set(rows.map(r => r.receiver).filter(Boolean))];
		const emp_promise = receiver_ids.length
			? frappe.db.get_list("Employee", {
				filters: { name: ["in", receiver_ids] },
				fields: ["name", "employee_name"],
			})
			: Promise.resolve([]);

		emp_promise.then(emps => {
			const emp_map = {};
			(emps || []).forEach(e => { emp_map[e.name] = e.employee_name; });

		const total = rows.reduce((s, r) => {
			return s + ((r.payment_type === "دفع" ? -1 : 1) * (r.amount || 0));
		}, 0);
			const grand = frm.doc.grand_total || 0;
			const remaining = grand - total;
		const rows_html = rows.map((r, i) => {
			const is_payment = r.payment_type === "دفع";
			const color = is_payment ? "#c62828" : "#2e7d32";
			const sign = is_payment ? "- " : "";
			const type_badge = is_payment
				? `<span style="background:#fbe9e7;color:#c62828;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:600;">دفع</span>`
				: `<span style="background:#e8f5e9;color:#2e7d32;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:600;">قبض</span>`;
			return `
			<tr style="${is_payment ? 'background:#fff8f8;' : ''}">
				<td>${i + 1}</td>
				<td><a href="/app/revenue/${r.name}">${r.name}</a> ${type_badge}</td>
				<td>${frappe.datetime.str_to_user(r.date)}</td>
				<td style="font-weight:700; color:${color};">${sign}${format_currency(r.amount)}</td>
				<td>${r.payment_method || "-"}</td>
				<td>${emp_map[r.receiver] || r.receiver || "-"}</td>
				<td>${r.notes || "-"}</td>
			</tr>`;
		}).join("");

		wrapper.html(`
			<div class="table-responsive" style="margin-top: 6px;">
				<table class="table table-bordered table-sm" style="margin-bottom: 0; font-size: 13px;">
					<thead style="background: var(--subtle-accent);">
						<tr>
							<th>#</th>
							<th>رقم الإيصال</th>
							<th>التاريخ</th>
							<th>المبلغ</th>
							<th>طريقة الدفع</th>
							<th>المستلم</th>
							<th>ملاحظات</th>
						</tr>
					</thead>
					<tbody>${rows_html}</tbody>
					<tfoot>
						<tr style="background: #e8f5e9; font-weight: 700;">
							<td colspan="3" style="text-align:right;">الإجمالي المدفوع</td>
							<td style="color:#2e7d32;">${format_currency(total)}</td>
							<td colspan="3"></td>
						</tr>
						<tr style="background: ${remaining > 0 ? '#fff8e1' : '#e8f5e9'}; font-weight: 700;">
							<td colspan="3" style="text-align:right;">المتبقي</td>
							<td style="color:${remaining > 0 ? '#e65100' : '#2e7d32'};">${format_currency(remaining)}</td>
							<td colspan="3"></td>
						</tr>
					</tfoot>
				</table>
			</div>`);
		}); // emp_promise.then
	}); // rows.then
}

function format_currency(val) {
	return frappe.format(val || 0, { fieldtype: "Currency" });
}
