frappe.query_reports["Owner Car Report"] = {
	filters: [
		{
			fieldname: "owner",
			label: __("المالك"),
			fieldtype: "Link",
			options: "Owners",
		},
		{
			fieldname: "car",
			label: __("السيارة"),
			fieldtype: "Link",
			options: "Car",
			get_query: function () {
				let owner = frappe.query_report.get_filter_value("owner");
				if (owner) {
					return { filters: { owner_car: owner } };
				}
			},
		},
		{
			fieldname: "from_date",
			label: __("من تاريخ"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("إلى تاريخ"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "gate_car_percent",
			label: __("نسبة Gate Car %"),
			fieldtype: "Percent",
			default: 20,
			reqd: 1,
		},
	],

	onload(report) {
		report.page.add_inner_button(__("سجل حركة السيارة"), function () {
			const car = frappe.query_report.get_filter_value("car");
			if (!car) {
				frappe.msgprint(__("يرجى اختيار سيارة أولاً"));
				return;
			}
			const from_date = frappe.query_report.get_filter_value("from_date");
			const to_date = frappe.query_report.get_filter_value("to_date");
			frappe.set_route("query-report", "Car Activity Report", {
				car: car,
				from_date: from_date,
				to_date: to_date,
			});
		});

		report.page.add_inner_button(__("تصدير للمحاسبة (CSV)"), function () {
			const from_date = frappe.query_report.get_filter_value("from_date");
			if (!from_date) {
				frappe.msgprint(__("يرجى تحديد الشهر أولاً (من تاريخ)"));
				return;
			}
			const url =
				"/api/method/gatecar.api.export_monthly_accrual_csv?period=" +
				encodeURIComponent(from_date);
			window.open(url, "_blank");
		});
	},
};
