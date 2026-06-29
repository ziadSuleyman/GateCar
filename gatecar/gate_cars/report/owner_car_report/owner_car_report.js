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
};
