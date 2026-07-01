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
	},

	booking(frm) {
		load_previous_payments(frm);
	},
});

function load_previous_payments(frm) {
	const wrapper = frm.fields_dict.previous_payments_html.$wrapper;
	if (!frm.doc.booking) {
		wrapper.html(`<p class="text-muted" style="padding: 8px 0;">${__("لا يوجد عقد مرتبط")}</p>`);
		return;
	}

	frappe.db.get_list("Revenue", {
		filters: { booking_reference: frm.doc.booking },
		fields: ["name", "date", "amount", "payment_method", "receiver", "notes"],
		order_by: "date asc",
	}).then(rows => {
		if (!rows || rows.length === 0) {
			wrapper.html(`<p class="text-muted" style="padding: 8px 0;">${__("لا توجد دفعات مسجلة لهذا العقد")}</p>`);
			return;
		}

		const total = rows.reduce((s, r) => s + (r.amount || 0), 0);
		const rows_html = rows.map((r, i) => `
			<tr>
				<td>${i + 1}</td>
				<td><a href="/app/revenue/${r.name}">${r.name}</a></td>
				<td>${frappe.datetime.str_to_user(r.date)}</td>
				<td style="font-weight:600; color:#2e7d32;">${format_currency(r.amount)}</td>
				<td>${r.payment_method || "-"}</td>
				<td>${r.receiver || "-"}</td>
				<td>${r.notes || "-"}</td>
			</tr>`).join("");

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
					</tfoot>
				</table>
			</div>`);
	});
}

function format_currency(val) {
	return frappe.format(val || 0, { fieldtype: "Currency" });
}
