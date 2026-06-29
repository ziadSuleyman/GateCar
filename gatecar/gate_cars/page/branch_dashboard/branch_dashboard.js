frappe.pages["branch-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "لوحة تحكم الفرع",
		single_column: true,
	});

	page.main.html('<div class="branch-dashboard-container"></div>');
	page.set_secondary_action(__("تحديث"), () => load_branch_dashboard(page), "refresh");

	load_branch_dashboard(page);
};

function load_branch_dashboard(page) {
	const container = page.main.find(".branch-dashboard-container");
	container.html(
		'<div class="text-center text-muted py-5"><i class="fa fa-spinner fa-spin fa-2x"></i></div>'
	);

	Promise.all([
		frappe.xcall("branch_dashboard_stats"),
		frappe.xcall("branch_car_profitability"),
	]).then(([stats, profitability]) => {
		if (stats.error) {
			container.html(`<div class="text-center text-muted py-5">${stats.error}</div>`);
			return;
		}
		render_branch_dashboard(container, stats, profitability);
	});
}

function render_branch_dashboard(container, data, profitability) {
	const available = data.status_map["متوفر"] || 0;
	const rented = data.status_map["مؤجر"] || 0;
	const reserved = data.status_map["محجوز"] || 0;
	const in_maintenance = data.status_map["داخل الصيانة"] || 0;
	const ready = data.status_map["جاهز للتسليم"] || 0;

	container.html(`
		<div style="padding: 15px;">

			<!-- البانر -->
			<div style="background: linear-gradient(135deg, #1b5e20, #4caf50); border-radius: 12px; padding: 20px 25px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
				<div>
					<h3 style="margin: 0; color: #fff; font-weight: 700; font-size: 22px;">لوحة تحكم الفرع</h3>
					<p style="margin: 5px 0 0; color: rgba(255,255,255,0.85); font-size: 13px;">مرحباً، ${frappe.session.user_fullname} — ${frappe.datetime.str_to_user(frappe.datetime.get_today())}</p>
				</div>
				<img src="/files/gatecar_logo.png" alt="Gate Cars" style="height: 55px; border-radius: 8px; background: rgba(255,255,255,0.15); padding: 5px;">
			</div>

			<!-- الإجمالي العام -->
			<div class="frappe-card" style="margin-bottom: 20px; padding: 15px;">
				<h5 style="margin: 0 0 12px; font-weight: 600;">
					<i class="fa fa-car" style="margin-left: 5px; color: #1565c0;"></i>
					إجمالي السيارات
				</h5>
				<div class="row" style="display: flex; flex-wrap: wrap;">
					${bstat("إجمالي", data.total_cars, "blue", "fa-car")}
					${bstat("متوفرة", available, "green", "fa-check-circle")}
					${bstat("محجوزة", reserved, "yellow", "fa-clock")}
					${bstat("مؤجرة", rented, "orange", "fa-key")}
					${bstat("صيانة", in_maintenance, "red", "fa-wrench")}
					${bstat("جاهز للتسليم", ready, "purple", "fa-thumbs-up")}
					${bstat("مجمدة", data.frozen_cars, "grey", "fa-snowflake")}
				</div>
			</div>

			<!-- جدول الأساطيل -->
			<div class="frappe-card" style="margin-bottom: 20px; padding: 15px;">
				<h5 style="margin-bottom: 15px; font-weight: 600;">
					<i class="fa fa-layer-group" style="margin-left: 5px;"></i>
					الأساطيل
				</h5>
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

			<!-- جدول السيارات مع الصيانة -->
			<div class="frappe-card" style="margin-bottom: 20px; padding: 15px;">
				<h5 style="margin-bottom: 15px; font-weight: 600;">
					<i class="fa fa-chart-line" style="margin-left: 5px;"></i>
					حالة السيارات والتكاليف
				</h5>
				<div class="table-responsive">
					<table class="table table-bordered table-hover" style="margin-bottom: 0;">
						<thead style="background: var(--subtle-accent);">
							<tr>
								<th>السيارة</th>
								<th>النوع</th>
								<th>الموديل</th>
								<th>الحالة</th>
								<th>تكاليف الصيانة</th>
								<th>تكاليف تبديل الزيت</th>
							</tr>
						</thead>
						<tbody>
							${profitability.map((car) => `
								<tr>
									<td><a href="/app/car/${car.name}"><strong>${car.name}</strong></a></td>
									<td>${car.brand}</td>
									<td>${car.model}</td>
									<td>${car.status}</td>
									<td style="color: #c62828;">${bcurrency(car.total_maintenance)}</td>
									<td style="color: #e65100;">${bcurrency(car.total_oil_change || 0)}</td>
								</tr>
							`).join("")}
						</tbody>
					</table>
				</div>
			</div>

			<!-- بطاقات الفروع - قابلة للطي -->
			${data.branches.map((b) => `
			<div class="frappe-card" style="margin-bottom: 20px; padding: 15px;">
				<div style="display: flex; align-items: center; justify-content: space-between; cursor: pointer;" onclick="$(this).next().toggle(); $(this).find('.toggle-icon').toggleClass('fa-chevron-down fa-chevron-up');">
					<h5 style="margin: 0; font-weight: 600;">
						<i class="fa fa-building" style="margin-left: 5px; color: #2e7d32;"></i>
						${b.branch_name}
						<span style="font-size: 12px; color: var(--text-muted); margin-right: 8px;">${b.city || ""}</span>
					</h5>
					<i class="fa fa-chevron-down toggle-icon" style="color: var(--text-muted);"></i>
				</div>
				<div style="display: none; margin-top: 12px;">
					<div class="row" style="display: flex; flex-wrap: wrap;">
						${bstat("إجمالي", b.car_count, "blue", "fa-car")}
						${bstat("متوفرة", b.available, "green", "fa-check-circle")}
						${bstat("محجوزة", b.reserved, "yellow", "fa-clock")}
						${bstat("مؤجرة", b.rented, "orange", "fa-key")}
						${bstat("صيانة", b.in_maintenance, "red", "fa-wrench")}
						${bstat("جاهز للتسليم", b.ready, "purple", "fa-thumbs-up")}
						${bstat("مجمدة", b.frozen, "grey", "fa-snowflake")}
					</div>
				</div>
			</div>
			`).join("")}

		</div>
	`);
}

function bstat(label, value, color, icon) {
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
			<div style="background: ${c.bg}; border: 1px solid ${c.border}; border-radius: 8px; padding: 10px 5px; text-align: center; height: 100%;">
				<i class="fa ${icon}" style="font-size: 16px; color: ${c.text}; margin-bottom: 4px;"></i>
				<div style="font-size: 18px; font-weight: 700; color: ${c.text};">${value}</div>
				<div style="font-size: 11px; color: ${c.text}; margin-top: 2px;">${label}</div>
			</div>
		</div>
	`;
}

function bcurrency(val) {
	return frappe.format(val, { fieldtype: "Currency" });
}
