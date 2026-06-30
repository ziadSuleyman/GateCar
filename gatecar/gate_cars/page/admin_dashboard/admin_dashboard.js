frappe.pages["admin-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "لوحة المراقبة",
		single_column: true,
	});

	page.profit_month = "";
	page.profit_year = String(new Date().getFullYear());
	page.date_from = moment().startOf("month").format("YYYY-MM-DD");
	page.date_to = moment().endOf("month").format("YYYY-MM-DD");

	page.main.html('<div class="admin-dashboard-container"></div>');
	page.set_secondary_action(__("تحديث"), () => load_dashboard(page), "refresh");

	load_dashboard(page);
};

function load_dashboard(page) {
	const container = page.main.find(".admin-dashboard-container");
	container.html(
		'<div class="text-center text-muted py-5"><i class="fa fa-spinner fa-spin fa-2x"></i></div>'
	);

	const month = page.profit_month;
	const year = page.profit_year;

	const profit_args = {};
	if (month) {
		profit_args.month = month;
		profit_args.year = year;
	}

	const summary_args = { date_from: page.date_from, date_to: page.date_to };

	Promise.all([
		frappe.xcall("dashboard_stats"),
		frappe.xcall("car_profitability", profit_args),
		frappe.xcall("profit_summary", summary_args),
	]).then(([stats, profitability, summary]) => {
		render_dashboard(page, container, stats, profitability, filter_month=month, filter_year=year, summary=summary);
	});
}

function render_dashboard(page, container, data, profitability, filter_month, filter_year, summary) {
	const available = data.status_map["متوفر"] || 0;
	const rented = data.status_map["مؤجر"] || 0;
	const reserved = data.status_map["محجوز"] || 0;
	const in_maintenance = data.status_map["داخل الصيانة"] || 0;
	const ready = data.status_map["جاهز للتسليم"] || 0;
	const is_admin = frappe.user_roles.includes("System Manager");

	container.html(`
		<div class="admin-dashboard" style="padding: 15px;">

			<!-- البانر -->
			<div style="background: linear-gradient(135deg, #1b5e20, #4caf50); border-radius: 12px; padding: 20px 25px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
				<div>
					<h3 style="margin: 0; color: #fff; font-weight: 700; font-size: 22px;">لوحة المراقبة</h3>
					<p style="margin: 5px 0 0; color: rgba(255,255,255,0.85); font-size: 13px;">مرحباً، ${frappe.session.user_fullname} — ${frappe.datetime.str_to_user(frappe.datetime.get_today())}</p>
				</div>
				<img src="/assets/gatecar/logo.png" alt="Gate Cars" style="height: 55px; border-radius: 8px; background: rgba(255,255,255,0.15); padding: 5px;">
			</div>

			${is_admin ? `
			<!-- 1. ملخص الأرباح -->
			<div class="frappe-card" style="margin-bottom: 20px; padding: 15px;">
				<h5 style="margin: 0 0 12px; font-weight: 600;">
					<i class="fa fa-coins" style="margin-left: 5px; color: #2e7d32;"></i>
					ملخص الأرباح
				</h5>
				<div>
					<div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
						<span style="font-weight: 600; font-size: 13px;">من:</span>
						<input type="date" id="profit-date-from" class="form-control input-sm" style="width: 160px;" value="${page.date_from}">
						<span style="font-weight: 600; font-size: 13px;">إلى:</span>
						<input type="date" id="profit-date-to" class="form-control input-sm" style="width: 160px;" value="${page.date_to}">
						<button id="calc-period-profit" class="btn btn-sm btn-primary">احسب</button>
					</div>
					<div class="row" style="margin-top: 12px; display: flex; flex-wrap: wrap;">
						${(() => {
							const rev   = summary.period_revenue || 0;
							const maint = summary.period_maintenance || 0;
							const oil   = summary.period_oil_change || 0;
							const net   = summary.period_profit || 0;
							const company_share   = rev * 0.20;
							const investor_share  = (rev * 0.80) - maint - oil;
							return `
							${stat_card("إجمالي الإيرادات", format_currency(rev), "green", "fa-arrow-up")}
							${stat_card("إجمالي الصيانة", format_currency(maint), "red", "fa-arrow-down")}
							${stat_card("إجمالي تبديل الزيت", format_currency(oil), "orange", "fa-oil-can")}
							${stat_card("صافي الربح", format_currency(net), net >= 0 ? "green" : "red", "fa-calculator")}
							${stat_card("صافي أرباح الشركة", format_currency(company_share), "blue", "fa-building")}
							${stat_card("صافي أرباح المستثمرين", format_currency(investor_share), investor_share >= 0 ? "purple" : "red", "fa-users")}
							`;
						})()}
					</div>
				</div>
			</div>` : ""}

			<!-- 2. جدول أرباح السيارات -->
			<div class="frappe-card" style="margin-bottom: 20px; padding: 15px;">
				<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; cursor: pointer;" class="collapsible-toggle">
					<h5 style="margin: 0; font-weight: 600;">
						<i class="fa fa-chart-line" style="margin-left: 5px;"></i>
						أرباح السيارات ${filter_month ? `(${filter_month}/${filter_year})` : "(الكل)"}
					</h5>
					<div style="display: flex; gap: 8px; align-items: center;">
						<select id="profit-month" class="form-control input-sm" style="width: auto;">
							<option value="">كل الشهور</option>
							<option value="1" ${filter_month == "1" ? "selected" : ""}>1 - يناير</option>
							<option value="2" ${filter_month == "2" ? "selected" : ""}>2 - فبراير</option>
							<option value="3" ${filter_month == "3" ? "selected" : ""}>3 - مارس</option>
							<option value="4" ${filter_month == "4" ? "selected" : ""}>4 - أبريل</option>
							<option value="5" ${filter_month == "5" ? "selected" : ""}>5 - مايو</option>
							<option value="6" ${filter_month == "6" ? "selected" : ""}>6 - يونيو</option>
							<option value="7" ${filter_month == "7" ? "selected" : ""}>7 - يوليو</option>
							<option value="8" ${filter_month == "8" ? "selected" : ""}>8 - أغسطس</option>
							<option value="9" ${filter_month == "9" ? "selected" : ""}>9 - سبتمبر</option>
							<option value="10" ${filter_month == "10" ? "selected" : ""}>10 - أكتوبر</option>
							<option value="11" ${filter_month == "11" ? "selected" : ""}>11 - نوفمبر</option>
							<option value="12" ${filter_month == "12" ? "selected" : ""}>12 - ديسمبر</option>
						</select>
						<select id="profit-year" class="form-control input-sm" style="width: auto;">
							<option value="2025" ${filter_year == "2025" ? "selected" : ""}>2025</option>
							<option value="2026" ${filter_year == "2026" ? "selected" : ""}>2026</option>
							<option value="2027" ${filter_year == "2027" ? "selected" : ""}>2027</option>
						</select>
						<i class="fa fa-chevron-down toggle-icon" style="color: var(--text-muted);"></i>
					</div>
				</div>
				<div class="collapsible-body" style="display: none; margin-top: 12px;">
					<div class="table-responsive">
						<table class="table table-bordered table-hover" style="margin-bottom: 0;">
							<thead style="background: var(--subtle-accent);">
								<tr>
									<th>السيارة</th>
									<th>النوع</th>
									<th>الموديل</th>
									<th>الحالة</th>
									${is_admin ? `<th>الإيرادات</th>` : ""}
									<th>تكاليف الصيانة</th>
									<th>تكاليف تبديل الزيت</th>
									${is_admin ? `<th>صافي الربح</th>` : ""}
									${is_admin ? `<th>التقرير</th>` : ""}
								</tr>
							</thead>
							<tbody>
								${profitability.map((car) => {
									const profit_color = car.net_profit > 0 ? "green" : car.net_profit < 0 ? "red" : "grey";
									return `
									<tr>
										<td><a href="/app/car/${car.name}"><strong>${car.name}</strong></a></td>
										<td>${car.brand}</td>
										<td>${car.model}</td>
										<td>${car.status}</td>
										${is_admin ? `<td style="color: #2e7d32;">${format_currency(car.total_revenue)}</td>` : ""}
										<td style="color: #c62828;">${format_currency(car.total_maintenance)}</td>
										<td style="color: #e65100;">${format_currency(car.total_oil_change || 0)}</td>
										${is_admin ? `<td><strong style="color: ${profit_color === "green" ? "#2e7d32" : profit_color === "red" ? "#c62828" : "#616161"};">${format_currency(car.net_profit)}</strong></td>` : ""}
										${is_admin ? `<td><a href="/app/query-report/Owner Car Report?car=${car.name}" class="btn btn-xs btn-primary-light" style="white-space: nowrap;"><i class="fa fa-file-alt" style="margin-left: 4px;"></i>عرض التقرير</a></td>` : ""}
									</tr>`;
								}).join("")}
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- 3. جدول الفروع -->
			<div class="frappe-card" style="margin-bottom: 20px; padding: 15px;">
				${collapsible_header("fa-building", "var(--text-color)", "ملخص الفروع")}
				<div class="collapsible-body" style="display: none; margin-top: 12px;">
					<div class="table-responsive">
						<table class="table table-bordered table-hover" style="margin-bottom: 0;">
							<thead style="background: var(--subtle-accent);">
								<tr>
									<th>الفرع</th>
									<th>المدينة</th>
									<th>إجمالي</th>
									<th>متوفرة</th>
									<th>محجوزة</th>
									<th>مؤجرة</th>
									<th>صيانة</th>
									<th>جاهز</th>
									<th>مجمدة</th>
								</tr>
							</thead>
							<tbody>
								${data.branches.map((b) => `
									<tr>
										<td><strong>${b.branch_name}</strong></td>
										<td>${b.city || "-"}</td>
										<td>${b.car_count}</td>
										<td><span class="indicator-pill green">${b.available}</span></td>
										<td><span class="indicator-pill yellow">${b.reserved}</span></td>
										<td><span class="indicator-pill orange">${b.rented}</span></td>
										<td><span class="indicator-pill red">${b.in_maintenance}</span></td>
										<td><span class="indicator-pill purple">${b.ready}</span></td>
										<td><span class="indicator-pill grey">${b.frozen}</span></td>
									</tr>
								`).join("")}
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- 4. جدول الأساطيل -->
			<div class="frappe-card" style="margin-bottom: 20px; padding: 15px;">
				${collapsible_header("fa-layer-group", "var(--text-color)", "الأساطيل")}
				<div class="collapsible-body" style="display: none; margin-top: 12px;">
					<div class="table-responsive">
						<table class="table table-bordered table-hover" style="margin-bottom: 0;">
							<thead style="background: var(--subtle-accent);">
								<tr>
									<th>الأسطول</th>
									<th>الفرع</th>
									<th>إجمالي السيارات</th>
									<th>متوفرة</th>
									<th>مؤجرة</th>
								</tr>
							</thead>
							<tbody>
								${data.fleets.map((f) => `
									<tr>
										<td><strong>${f.fleet_name}</strong></td>
										<td>${f.branch}</td>
										<td>${f.car_count}</td>
										<td><span class="indicator-pill green">${f.available}</span></td>
										<td><span class="indicator-pill orange">${f.rented}</span></td>
									</tr>
								`).join("")}
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- 5. البطاقات - قابلة للطي -->
			<div class="frappe-card" style="margin-bottom: 20px; padding: 15px;">
				${collapsible_header("fa-car", "#1565c0", "الإجمالي العام")}
				<div class="collapsible-body" style="display: none; margin-top: 12px;">
					<div class="row" style="display: flex; flex-wrap: wrap;">
						${stat_card("إجمالي السيارات", data.total_cars, "blue", "fa-car")}
						${stat_card("متوفرة", available, "green", "fa-check-circle")}
						${stat_card("محجوزة", reserved, "yellow", "fa-clock")}
						${stat_card("مؤجرة", rented, "orange", "fa-key")}
						${stat_card("داخل الصيانة", in_maintenance, "red", "fa-wrench")}
						${stat_card("جاهز للتسليم", ready, "purple", "fa-thumbs-up")}
						${stat_card("مجمدة", data.frozen_cars, "grey", "fa-snowflake")}
					</div>
				</div>
			</div>

			<!-- 6. بطاقات الفروع - قابلة للطي -->
			${data.branches.map((b) => `
			<div class="frappe-card" style="margin-bottom: 20px; padding: 15px;">
				${collapsible_header("fa-building", "#2e7d32", `${b.branch_name} <span style="font-size: 12px; color: var(--text-muted); font-weight: 400; margin-right: 8px;">${b.city || ""}</span>`)}
				<div class="collapsible-body" style="display: none; margin-top: 12px;">
					<div class="row" style="display: flex; flex-wrap: wrap;">
						${stat_card("إجمالي", b.car_count, "blue", "fa-car")}
						${stat_card("متوفرة", b.available, "green", "fa-check-circle")}
						${stat_card("محجوزة", b.reserved, "yellow", "fa-clock")}
						${stat_card("مؤجرة", b.rented, "orange", "fa-key")}
						${stat_card("صيانة", b.in_maintenance, "red", "fa-wrench")}
						${stat_card("جاهز للتسليم", b.ready, "purple", "fa-thumbs-up")}
						${stat_card("مجمدة", b.frozen, "grey", "fa-snowflake")}
					</div>
				</div>
			</div>
			`).join("")}

		</div>
	`);

	container.find(".collapsible-toggle").on("click", function () {
		$(this).find(".toggle-icon").toggleClass("fa-chevron-down fa-chevron-up");
		$(this).closest(".frappe-card").find(".collapsible-body").toggle();
	});

	container.find("#profit-month, #profit-year").on("click", function (e) {
		e.stopPropagation();
	});

	container.find("#profit-month, #profit-year").on("change", function () {
		page.profit_month = container.find("#profit-month").val();
		page.profit_year = container.find("#profit-year").val();
		load_dashboard(page);
	});

	container.find("#calc-period-profit").on("click", function () {
		page.date_from = container.find("#profit-date-from").val();
		page.date_to = container.find("#profit-date-to").val();
		if (!page.date_from || !page.date_to) {
			frappe.msgprint("اختر تاريخ البداية والنهاية", indicator="orange", alert=true);
			return;
		}
		load_dashboard(page);
	});
}

function collapsible_header(icon, color, title) {
	return `
		<div style="display: flex; align-items: center; justify-content: space-between; cursor: pointer;" class="collapsible-toggle">
			<h5 style="margin: 0; font-weight: 600;">
				<i class="fa ${icon}" style="margin-left: 5px; color: ${color};"></i>
				${title}
			</h5>
			<i class="fa fa-chevron-down toggle-icon" style="color: var(--text-muted);"></i>
		</div>
	`;
}

function stat_card(label, value, color, icon) {
	const colors = {
		blue: { bg: "#e8f4fd", text: "#1565c0", border: "#90caf9" },
		green: { bg: "#e8f5e9", text: "#2e7d32", border: "#a5d6a7" },
		orange: { bg: "#fff3e0", text: "#e65100", border: "#ffcc80" },
		yellow: { bg: "#fffde7", text: "#f57f17", border: "#fff59d" },
		red: { bg: "#fbe9e7", text: "#c62828", border: "#ef9a9a" },
		grey: { bg: "#f5f5f5", text: "#616161", border: "#e0e0e0" },
		purple: { bg: "#f3e5f5", text: "#6a1b9a", border: "#ce93d8" },
	};
	const c = colors[color] || colors.blue;

	return `
		<div class="col-sm-4 col-md-3" style="margin-bottom: 8px; flex: 1 1 0; max-width: 14.28%; min-width: 100px;">
			<div style="
				background: ${c.bg};
				border: 1px solid ${c.border};
				border-radius: 8px;
				padding: 10px 5px;
				text-align: center;
				height: 100%;
			">
				<i class="fa ${icon}" style="font-size: 16px; color: ${c.text}; margin-bottom: 4px;"></i>
				<div style="font-size: 18px; font-weight: 700; color: ${c.text};">${value}</div>
				<div style="font-size: 11px; color: ${c.text}; margin-top: 2px;">${label}</div>
			</div>
		</div>
	`;
}

function format_currency(val) {
	return frappe.format(val, { fieldtype: "Currency" });
}
