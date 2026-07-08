frappe.query_reports["Car Activity Report"] = {
	filters: [
		{
			fieldname: "car",
			label: __("السيارة"),
			fieldtype: "Link",
			options: "Car",
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("من تاريخ"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("إلى تاريخ"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data._style) {
			value = `<span style="${data._style}">${value}</span>`;
		}
		return value;
	},

	onload(report) {
		report.page.add_inner_button(__("طباعة التقرير"), function () {
			const car = frappe.query_report.get_filter_value("car");
			const from_date = frappe.query_report.get_filter_value("from_date");
			const to_date = frappe.query_report.get_filter_value("to_date");
			if (!car) {
				frappe.msgprint(__("يرجى اختيار سيارة أولاً"));
				return;
			}
			frappe.call({
				method: "gatecar.api.get_car_activity_html",
				args: { car, from_date, to_date },
				callback(r) {
					if (!r.message) return;
					const w = window.open("", "_blank");
					w.document.write(r.message);
					w.document.close();
					setTimeout(() => w.print(), 800);
				},
			});
		});
	},
};
